"""
Logger module — structured recording and reporting of conversion results.

Provides the ConversionLogger class which:
- Records per-file conversion results in memory.
- Prints real-time status lines during a batch run.
- Outputs aggregate summaries on completion.
- Exports logs in CSV and JSON formats for post-hoc analysis.
"""

import csv
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, TextIO


@dataclass
class LogRecord:
    """A single conversion result record."""

    timestamp: str = ''
    input_path: str = ''
    output_path: str = ''
    status: str = 'pending'       # pending | success | error | skipped
    duration: float = 0.0
    error: Optional[str] = None
    attempts: int = 1


class ConversionLogger:
    """Records and displays conversion results."""

    def __init__(self, out_stream: TextIO = sys.stdout):
        self.records: List[LogRecord] = []
        self._out = out_stream
        self._errors: List[LogRecord] = []

    def log_result(self, record: LogRecord) -> None:
        """Record a result and print a status line."""
        self.records.append(record)
        if record.status == 'error':
            self._errors.append(record)
        self._print_status(record)

    def log_message(self, message: str, level: str = 'INFO') -> None:
        """Print an informational message (not tied to a file)."""
        label = f'[{level}]'
        print(f'  {label} {message}', file=self._out)

    # ── Status line rendering ───────────────────────────────────

    STATUS_ICONS = {
        'success': '✓',   # ✓
        'error':   '✗',   # ✗
        'skipped': '→',   # →
        'pending': '…',   # …
    }

    def _print_status(self, record: LogRecord) -> None:
        """Print a single status line for the terminal."""
        icon = self.STATUS_ICONS.get(record.status, '?')

        parts = [f'  {icon}']

        # Short display: show just the filename, not the full path
        input_name = Path(record.input_path).name if record.input_path else '?'
        output_name = Path(record.output_path).name if record.output_path else '?'

        parts.append(input_name)
        parts.append(f'→ {output_name}')  # →

        if record.duration > 0:
            parts.append(f'[{record.duration:.1f}s]')

        if record.attempts > 1:
            parts.append(f'(attempt {record.attempts})')

        if record.error:
            # Truncate long errors for terminal display
            err = record.error[:120]
            if len(record.error) > 120:
                err += '…'
            parts.append(f'— {err}')  # —

        print(' '.join(parts), file=self._out)

    # ── Summary ─────────────────────────────────────────────────

    def print_summary(self, time_suffix: str = '') -> None:
        """Print an aggregate summary of the batch run."""
        total = len(self.records)
        success = sum(1 for r in self.records if r.status == 'success')
        errors = sum(1 for r in self.records if r.status == 'error')
        skipped = sum(1 for r in self.records if r.status == 'skipped')
        total_dur = sum(r.duration for r in self.records if r.status == 'success')
        total_all = sum(r.duration for r in self.records)

        print('\n── Summary ───────────'
              '──────────────'
              '────────────', file=self._out)
        print(f'  Total processed: {total}', file=self._out)
        print(f'  Successful:      {success}  '
              f'({total_dur:.1f}s spent on successful conversions)', file=self._out)
        if errors:
            print(f'  Errors:          {errors}', file=self._out)
        if skipped:
            print(f'  Skipped:         {skipped}', file=self._out)
        if success:
            avg = total_dur / success
            print(f'  Average:         {avg:.1f}s per file', file=self._out)
        if total_all > 0:
            print(f'  Total wall time: {total_all:.1f}s', file=self._out)

        if self._errors:
            print(f'\n  Failed files ({len(self._errors)}):', file=self._out)
            for rec in self._errors[:10]:  # Show first 10 errors
                print(f'    ✗ {Path(rec.input_path).name}: {rec.error[:80]}', file=self._out)
            if len(self._errors) > 10:
                print(f'    ... and {len(self._errors) - 10} more (see --log-file for full list)', file=self._out)

    # ── Export ───────────────────────────────────────────────────

    def export_csv(self, path: Path) -> None:
        """Write all records to a CSV file."""
        fieldnames = [
            'timestamp', 'input_path', 'output_path',
            'status', 'duration', 'error', 'attempts',
        ]
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self.records:
                row = asdict(rec)
                row['error'] = row['error'] or ''
                writer.writerow(row)

    def export_json(self, path: Path) -> None:
        """Write all records to a JSON file."""
        data = []
        for rec in self.records:
            row = asdict(rec)
            data.append(row)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Factory methods ─────────────────────────────────────────

    @classmethod
    def from_result(
        cls,
        status: str,
        input_path: str,
        output_path: str = '',
        duration: float = 0.0,
        error: Optional[str] = None,
        attempts: int = 1,
    ) -> LogRecord:
        """Create a LogRecord with an auto-generated timestamp."""
        return LogRecord(
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
            input_path=input_path,
            output_path=output_path,
            status=status,
            duration=round(duration, 2),
            error=error,
            attempts=attempts,
        )
