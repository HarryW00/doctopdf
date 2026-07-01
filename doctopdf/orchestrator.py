"""
Orchestrator — batch conversion coordination.

Manages the end-to-end conversion pipeline:
1. Pre-flight checks (Word installed, input/output paths valid)
2. File discovery (scanner)
3. Sequential conversion loop (converter with retry)
4. Logging and results collection
"""

import time
from pathlib import Path
from typing import Callable, List, Optional

from .scanner import find_documents, map_output_path, resolve_collision
from .converter import WordConverter
from .logger import ConversionLogger, LogRecord
from .errors import (
    DocToPDFError,
    WordNotInstalledError,
    WordPermissionError,
    CorruptDocumentError,
    ExportError,
    ConversionTimeoutError,
    FileAccessError,
)


class Orchestrator:
    """
    Batch conversion orchestrator.

    Processes documents sequentially (one at a time) to maintain
    reliability with Microsoft Word's single-instance architecture.

    Usage:
        orch = Orchestrator(
            input_dir=Path('./docs'),
            output_dir=Path('./pdfs'),
            recursive=True,
        )
        results = orch.run()
    """

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        flat: bool = False,
        timeout: int = 60,
        retry: int = 2,
        restart_every: int = 0,
        dry_run: bool = False,
        log_file: Optional[Path] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """
        Args:
            input_dir: Root directory to scan for documents.
            output_dir: Directory where PDFs will be written.
            recursive: Scan subdirectories recursively.
            flat: If True, write all PDFs flat (no mirrored tree).
            timeout: Seconds to wait per document before timeout.
            retry: Number of retry attempts after first failure.
            restart_every: Restart Word after this many successful conversions
                           to prevent state degradation. 0 = never restart.
            dry_run: Scan and report without converting.
            log_file: Optional path for CSV/JSON log export.
            progress_callback: Optional fn(file_num, total, result).
        """
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.recursive = recursive
        self.flat = flat
        self.restart_every = restart_every
        self.dry_run = dry_run
        self.log_file = log_file

        # Track Word state for periodic restart
        self._conversions_since_restart = 0

        self.converter = WordConverter(
            timeout=timeout,
            retry_count=retry,
            retry_delay=2.0,
        )
        self.logger = ConversionLogger()
        self.progress_callback = progress_callback

        # State
        self._results: List[LogRecord] = []
        self._start_time: float = 0.0

    # ── Main entry point ────────────────────────────────────────

    def run(self) -> List[LogRecord]:
        """
        Execute the full batch conversion workflow.

        Returns:
            List of LogRecord instances, one per file.

        Raises:
            WordNotInstalledError: Pre-flight check failed.
            FileAccessError: Output directory is not writable.
        """
        self._start_time = time.monotonic()

        # Phase 1: Pre-flight checks
        self._pre_flight()

        # Phase 2: Discover files
        files = find_documents(self.input_dir, recursive=self.recursive)
        if not files:
            self.logger.log_message('No supported documents found.', level='WARN')
            return []

        self.logger.log_message(
            f'Found {len(files)} document(s) in {self.input_dir}'
            f'{" (recursive)" if self.recursive else ""}'
        )

        if self.dry_run:
            self._dry_run_files(files)
            return self._results

        # Phase 3: Sequential conversion
        self._convert_files(files)

        # Phase 4: Summary and export
        self._finalise()

        return self._results

    # ── Phase 1: Pre-flight ─────────────────────────────────────

    def _pre_flight(self) -> None:
        """Verify environment before starting conversions."""
        self.logger.log_message('Checking environment…')

        if not self.input_dir.is_dir():
            raise FileAccessError(
                self.input_dir,
                'Input directory does not exist or is not accessible'
            )

        if not self.dry_run:
            installed, version = WordConverter.check_word_installed()
            if not installed:
                raise WordNotInstalledError()
            self.logger.log_message(
                f'Microsoft Word detected (version: {version})'
            )

        # Create output directory if needed
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise FileAccessError(self.output_dir, str(e))

        if self.dry_run:
            self.logger.log_message('DRY RUN — no files will be converted')

    # ── Phase 2: Files (dry run) ────────────────────────────────

    def _dry_run_files(self, files: List[Path]) -> None:
        """Report what would be converted without actually doing it."""
        self.logger.log_message('Files to convert:')

        for f in files:
            output = map_output_path(f, self.input_dir, self.output_dir, flat=self.flat)
            size_kb = f.stat().st_size / 1024
            self.logger.log_message(
                f'  {f.relative_to(self.input_dir)} '
                f'({size_kb:.0f} KB) → {output.name}'
            )

        total = len(files)
        self.logger.log_message(
            f'{total} file(s) would be converted.'
        )

    # ── Phase 3: Conversion loop ────────────────────────────────

    def _convert_files(self, files: List[Path]) -> None:
        """Convert each file sequentially with logging."""
        total = len(files)

        for idx, input_path in enumerate(files, start=1):
            output_path = map_output_path(
                input_path, self.input_dir, self.output_dir, flat=self.flat
            )

            # Handle filename collisions
            if output_path.exists():
                original = output_path
                output_path = resolve_collision(output_path)
                self.logger.log_message(
                    f'Output exists: {original.name}, using: {output_path.name}',
                    level='WARN'
                )

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert
            result = self._convert_single(input_path, output_path, idx, total)
            self._results.append(result)
            self.logger.log_result(result)

            # Callback (optional — can be None)
            if self.progress_callback:
                self.progress_callback(idx, total, result)

            # Periodically restart Word to prevent state degradation
            if result.status == 'success':
                self._conversions_since_restart += 1
                if (self.restart_every > 0
                        and self._conversions_since_restart >= self.restart_every):
                    self.logger.log_message(
                        f'Restarting Word after {self._conversions_since_restart} '
                        f'conversions…'
                    )
                    WordConverter.restart_word()
                    self._conversions_since_restart = 0

    def _convert_single(
        self,
        input_path: Path,
        output_path: Path,
        index: int,
        total: int,
    ) -> LogRecord:
        """Convert a single file and return a LogRecord."""
        # Brief pause between files to let Word settle
        if index > 1:
            time.sleep(0.5)

        start = time.monotonic()

        try:
            conv_result = self.converter.convert_with_retry(input_path, output_path)
            duration = time.monotonic() - start

            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='success',
                duration=round(duration, 2),
                attempts=conv_result.get('attempts', 1),
            )

        except WordPermissionError as e:
            # Permission issues are critical — surface immediately
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=str(e),
            )

        except CorruptDocumentError as e:
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=str(e),
            )

        except ConversionTimeoutError as e:
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=str(e),
                attempts=self.converter.retry_count + 1,
            )

        except ExportError as e:
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=str(e),
                attempts=self.converter.retry_count + 1,
            )

        except DocToPDFError as e:
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=str(e),
            )

        except Exception as e:
            # Catch-all for unexpected errors
            return LogRecord(
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
                input_path=str(input_path),
                output_path=str(output_path),
                status='error',
                duration=round(time.monotonic() - start, 2),
                error=f'Unexpected error: {e}',
            )

    # ── Phase 4: Finalise ───────────────────────────────────────

    def _finalise(self) -> None:
        """Print summary and optionally export log file."""
        self.logger.print_summary()

        if self.log_file:
            suffix = Path(self.log_file).suffix.lower()
            try:
                if suffix == '.csv':
                    self.logger.export_csv(self.log_file)
                else:
                    self.logger.export_json(self.log_file)
                self.logger.log_message(f'Log written to: {self.log_file}')
            except PermissionError as e:
                self.logger.log_message(
                    f'Cannot write log file: {e}', level='ERROR'
                )

    # ── Properties ──────────────────────────────────────────────

    @property
    def results(self) -> List[LogRecord]:
        """All conversion results from the last run."""
        return list(self._results)

    @property
    def success_count(self) -> int:
        """Number of successful conversions."""
        return sum(1 for r in self._results if r.status == 'success')

    @property
    def error_count(self) -> int:
        """Number of failed conversions."""
        return sum(1 for r in self._results if r.status == 'error')

    @property
    def elapsed(self) -> float:
        """Wall-clock seconds since run() was called."""
        if self._start_time:
            return time.monotonic() - self._start_time
        return 0.0
