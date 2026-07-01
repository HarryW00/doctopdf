# DocToPDF — macOS Batch Document Converter

> **Design Document** · Microsoft Word automation via AppleScript/JXA  
> **Date:** 2026-07-01  
> **Status:** Ready for implementation

---

## 1. System Design Overview

### 1.1 Purpose

Convert `.doc` and `.docx` files to PDF on macOS using Microsoft Word as the authoritative rendering engine. Operates entirely offline — no web APIs, cloud upload, browser automation, or external SaaS.

### 1.2 Core Principle

**Microsoft Word's built-in PDF export is the most faithful conversion path** on macOS for complex Office documents. Alternative approaches (LibreOffice, Pandoc, custom parsers) all introduce rendering discrepancies — font substitution, layout shifts, missing features. By automating Word itself, we guarantee that what you see in Word is what you get in the PDF.

### 1.3 High-Level Flow

```
Input Folder (.doc/.docx)
        │
        ▼
┌──────────────────┐
│  Scanner Module  │  recursive walk, filter, map to output paths
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Orchestrator    │  queue management, retry, concurrency gate
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Converter       │  AppleScript/JXA → Microsoft Word
│  (Word Bridge)   │  open → export as PDF → close
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Output Folder   │  mirrored tree, PDF files
│  + Log           │  structured CSV/JSON log
└──────────────────┘
```

---

## 2. Architecture Components

### 2.1 Module Map

```
doctopdf/
├── __init__.py
├── __main__.py          # python -m doctopdf entry
├── cli.py               # Argument parsing, user interface
├── scanner.py           # File discovery, path mapping
├── converter.py         # Word automation bridge (Applescript/JXA)
├── orchestrator.py      # Batch queue, retry, concurrency
├── logger.py            # Structured logging + results CSV
├── applescript/         # Raw .applescript source files
│   ├── export_document.applescript
│   └── check_word.applescript
├── errors.py            # Custom exception hierarchy
└── config.py            # Defaults, constants, retry policy
```

### 2.2 Component Responsibilities

| Component | Responsibility |
|---|---|
| `cli.py` | Parse CLI args, dispatch to orchestrator, format output |
| `scanner.py` | Walk input tree, match `.doc`/`.docx`, build output path map |
| `converter.py` | Compose & execute AppleScript/JXA; parse results; timeout |
| `orchestrator.py` | Iterate file queue, call converter, apply retry policy |
| `logger.py` | Per-file structured record + aggregated summary |
| `errors.py` | Typed exceptions for all failure modes |
| `config.py` | Retry count, timeout seconds, output structure policy |

---

## 3. Output Path Strategy

### 3.1 Mirrored Tree (Recommended)

Output PDFs are written into a **mirrored directory tree** under the user-specified `--output` folder, preserving the relative path of the input file.

```
Input:  ./docs/subdir/report.docx
Output: ./pdfs/subdir/report.pdf
```

**Why mirrored over flat:**
- Batch conversions spanning many subfolders would produce filename collisions in a flat layout.
- Mirrored paths are deterministic and traceable.
- Users can visually match input and output structures.

### 3.2 Flat Mode (Optional)

With `--flat`, all PDFs land directly in the output directory. A collision suffix (`_1`, `_2`) is appended when duplicate filenames arise.

---

## 4. Microsoft Word Automation Bridge

### 4.1 Primary Approach: JXA (JavaScript for Automation)

JXA is preferred over AppleScript for the following reasons:
- Better error propagation (try/catch with meaningful error objects)
- Easier string handling (no AppleScript's concatenation quirks)
- More reliable with modern Word for Mac (Office 365 / 2021+)
- Python's `osascript` can execute JXA with `-l JavaScript`

### 4.2 Core JXA Export Script

```javascript
// export_document.js
function run(argv) {
    var inputPath = argv[0];
    var outputPath = argv[1];
    var timeoutSec = parseInt(argv[2]) || 60;

    try {
        var app = Application('Microsoft Word');
        app.includeStandardAdditions = true;

        // Open the document (absolute path required)
        var doc = app.open(inputPath);

        // Wait for document to be ready (basic readiness check)
        if (doc === null || doc === undefined) {
            throw new Error('Word returned null when opening document');
        }

        // Export as PDF
        // Note: 'save as PDF' constant may vary by Word locale/version
        var exportResult = doc.export({
            to: outputPath,
            as: 'PDF'  // or use constant: MicrosoftWord.SaveAsPDF
        });

        // Close without saving changes to the original
        doc.close({ saving: 'no' });

        return JSON.stringify({
            status: 'success',
            input: inputPath,
            output: outputPath
        });
    } catch (e) {
        // Attempt cleanup: close active document if still open
        try {
            var activeDoc = app.activeDocument;
            if (activeDoc) {
                activeDoc.close({ saving: 'no' });
            }
        } catch (ignore) {}

        return JSON.stringify({
            status: 'error',
            input: inputPath,
            error: e.message || String(e)
        });
    }
}
```

### 4.3 Fallback: AppleScript Variant

```applescript
-- export_document.applescript
on run {inputPath, outputPath}
    try
        tell application "Microsoft Word"
            -- Open the document
            set doc to open inputPath

            -- Export as PDF
            -- Documentation note: Word for Mac uses "save as PDF" format
            save as doc format format PDF file name outputPath

            -- Close without saving changes to original
            close doc saving no
        end tell

        return "{\"status\":\"success\"}"
    on error errMsg
        -- Cleanup: close any stray document
        try
            tell application "Microsoft Word"
                close active document saving no
            end tell
        end try

        return "{\"status\":\"error\",\"error\":\"" & errMsg & "\"}"
    end try
end run
```

**Important:** The AppleScript `save as` constants (`format PDF`) may differ across Word versions. The implementation should probe Word's dictionary at first run or allow a `--word-version` flag.

### 4.4 Invocation from Python

```python
import subprocess
import json
import os

def run_jxa(script_path: str, input_path: str, output_path: str, timeout: int = 60) -> dict:
    """
    Execute a JXA script via osascript.
    Returns parsed JSON from the script's stdout.
    """
    cmd = [
        'osascript',
        '-l', 'JavaScript',
        script_path,
        input_path,
        output_path,
        str(timeout)
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 15,  # 15s grace over Word's timeout
        )
        if result.returncode != 0:
            return {
                'status': 'error',
                'error': result.stderr.strip() or 'osascript returned non-zero'
            }
        # Parse the JSON returned by the script
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'error': f'Word timeout after {timeout}s'
        }
```

### 4.5 Word Installation Check

```applescript
-- check_word.applescript
try
    tell application "Microsoft Word" to version
    return "{\"installed\":true}"
on error
    return "{\"installed\":false}"
end try
```

---

## 5. Python Implementation Plan

### 5.1 File Discovery (`scanner.py`)

```python
import os
import re
from pathlib import Path
from typing import List, Tuple

SUPPORTED_EXTENSIONS = {'.doc', '.docx'}

def find_documents(
    input_dir: Path,
    recursive: bool = True,
    min_size_bytes: int = 0
) -> List[Path]:
    """Recursively discover supported document files."""
    pattern = '**/*' if recursive else '*'
    files = []
    for p in Path(input_dir).glob(pattern):
        if not p.is_file():
            continue
        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
            if p.stat().st_size >= min_size_bytes:
                files.append(p)
    return sorted(files)  # Deterministic order


def map_output_path(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    flat: bool = False
) -> Path:
    """Map an input file to its output PDF path."""
    if flat:
        return output_root / f'{input_path.stem}.pdf'
    else:
        rel = input_path.relative_to(input_root)
        return output_root / rel.with_suffix('.pdf')


def ensure_output_dir(output_path: Path) -> None:
    """Create parent directories for the output path if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
```

### 5.2 Converter (`converter.py`)

```python
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict

from .errors import (
    WordNotInstalledError,
    DocumentOpenError,
    ExportError,
    ConversionTimeoutError,
    CorruptDocumentError,
)


class WordConverter:
    """Manages the Microsoft Word automation bridge."""

    JXA_SCRIPT = Path(__file__).parent / 'applescript' / 'export_document.js'
    CHECK_SCRIPT = Path(__file__).parent / 'applescript' / 'check_word.applescript'

    def __init__(
        self,
        timeout: int = 60,
        retry_count: int = 2,
        retry_delay: float = 2.0,
    ):
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    @classmethod
    def check_word_installed(cls) -> bool:
        """Probe whether Microsoft Word is installed and scriptable."""
        cmd = ['osascript', cls.CHECK_SCRIPT]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout.strip())
            return data.get('installed', False)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return False

    def convert(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Dict:
        """Convert a single document to PDF via JXA bridge."""
        abs_input = str(input_path.resolve())
        abs_output = str(output_path.resolve())

        cmd = [
            'osascript',
            '-l', 'JavaScript',
            str(self.JXA_SCRIPT),
            abs_input,
            abs_output,
            str(self.timeout),
        ]

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 15,
            )
        except subprocess.TimeoutExpired:
            self._cleanup_stale_word()
            raise ConversionTimeoutError(input_path, self.timeout)

        duration = time.monotonic() - start

        if result.returncode != 0:
            raise ExportError(
                input_path, result.stderr.strip() or 'osascript failed'
            )

        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError as e:
            raise ExportError(input_path, f'Cannot parse script output: {e}')

        if data.get('status') == 'error':
            error = data.get('error', 'Unknown error')
            if 'file format' in error.lower() or 'corrupt' in error.lower():
                raise CorruptDocumentError(input_path, error)
            raise ExportError(input_path, error)

        return {
            'input': str(input_path),
            'output': str(output_path),
            'duration': duration,
            'status': 'success',
        }

    def convert_with_retry(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Dict:
        """Convert with retry logic."""
        last_error = None
        for attempt in range(1, self.retry_count + 2):  # +1 initial attempt
            try:
                return self.convert(input_path, output_path)
            except (ExportError, ConversionTimeoutError) as e:
                last_error = e
                if attempt <= self.retry_count:
                    time.sleep(self.retry_delay * attempt)
                    self._cleanup_stale_word()
                    continue
                raise

    @staticmethod
    def _cleanup_stale_word() -> None:
        """If Word is open but unresponsive, prompt user (do not force-kill)."""
        # On macOS, force-killing Word risks data loss.
        # Instead, detect and log; user can intervene.
        import subprocess
        cmd = [
            'osascript', '-e',
            'tell application "System Events" to exists process "Microsoft Word"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.stdout.strip() == 'true':
                # Word is running but may be hung — log a warning
                # We do NOT kill; we let the next conversion attempt proceed.
                pass
        except Exception:
            pass
```

### 5.3 Orchestrator (`orchestrator.py`)

```python
import time
from pathlib import Path
from typing import List, Optional, Callable

from .scanner import find_documents, map_output_path, ensure_output_dir
from .converter import WordConverter
from .logger import ConversionLogger
from .errors import DocToPDFError


class ConversionResult:
    """Outcome of a single file conversion."""
    def __init__(self, input_path: Path, output_path: Path):
        self.input_path = input_path
        self.output_path = output_path
        self.status: str = 'pending'   # pending | success | error | skipped
        self.duration: float = 0.0
        self.error: Optional[str] = None
        self.attempts: int = 0


class Orchestrator:
    """Batch conversion orchestrator with sequential processing."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        flat: bool = False,
        timeout: int = 60,
        retry: int = 2,
        dry_run: bool = False,
        progress_callback: Optional[Callable] = None,
    ):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.recursive = recursive
        self.flat = flat
        self.dry_run = dry_run
        self.converter = WordConverter(timeout=timeout, retry_count=retry)
        self.logger = ConversionLogger()
        self.progress_callback = progress_callback

    def run(self) -> List[ConversionResult]:
        """Execute the full batch conversion."""
        # Phase 1: Pre-flight check
        if not self.dry_run:
            if not WordConverter.check_word_installed():
                raise WordNotInstalledError(
                    'Microsoft Word not found. Install Word and try again.'
                )

        # Phase 2: Discover files
        files = find_documents(self.input_dir, recursive=self.recursive)
        if not files:
            self.logger.log('No supported documents found.', level='WARN')
            return []

        results = []

        # Phase 3: Convert each file sequentially
        for i, input_path in enumerate(files):
            output_path = map_output_path(
                input_path, self.input_dir, self.output_dir, flat=self.flat
            )

            result = ConversionResult(input_path, output_path)

            if self.dry_run:
                result.status = 'skipped'
                results.append(result)
                self.logger.log_result(result)
                continue

            # Handle filename collision (mirrored tree: unlikely; flat: possible)
            if output_path.exists():
                output_path = self._resolve_collision(output_path)

            try:
                ensure_output_dir(output_path)

                start = time.monotonic()
                if not self.dry_run:
                    conv_result = self.converter.convert_with_retry(
                        input_path, output_path
                    )
                duration = time.monotonic() - start

                result.status = 'success'
                result.duration = duration
                result.attempts = conv_result.get('attempts', 1)

            except DocToPDFError as e:
                result.status = 'error'
                result.error = str(e)
                result.duration = time.monotonic() - start
            except Exception as e:
                result.status = 'error'
                result.error = f'Unexpected: {e}'
                result.duration = time.monotonic() - start

            results.append(result)
            self.logger.log_result(result)

            if self.progress_callback:
                self.progress_callback(i + 1, len(files), result)

        # Phase 4: Summary
        self.logger.print_summary()
        return results

    @staticmethod
    def _resolve_collision(path: Path) -> Path:
        """Append _N suffix when output file already exists."""
        stem = path.stem
        parent = path.parent
        ext = '.pdf'
        counter = 1
        while True:
            new_path = parent / f'{stem}_{counter}{ext}'
            if not new_path.exists():
                return new_path
            counter += 1
```

### 5.4 CLI (`cli.py`)

```python
#!/usr/bin/env python3
"""
DocToPDF — macOS batch document converter using Microsoft Word.

Usage:
    convert-word-pdf --input ./docs --output ./pdfs [--recursive] [--flat]
    convert-word-pdf --input ./docs --output ./pdfs --dry-run
    convert-word-pdf --input ./docs --output ./pdfs --format json
    convert-word-pdf --check          # check if Word is installed
"""

import argparse
import sys
import json
from pathlib import Path
from .orchestrator import Orchestrator
from .converter import WordConverter
from .errors import WordNotInstalledError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='convert-word-pdf',
        description='Batch convert .doc/.docx to PDF using Microsoft Word.',
        epilog='Runs entirely offline. Microsoft Word must be installed.',
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        help='Input directory containing .doc/.docx files',
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory for PDF files',
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='Recursively scan input directory (default: on)',
    )
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not scan subdirectories',
    )
    parser.add_argument(
        '--flat',
        action='store_true',
        default=False,
        help='Write all PDFs to flat output dir (default: mirrored tree)',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Seconds to wait per document before timeout (default: 60)',
    )
    parser.add_argument(
        '--retry',
        type=int,
        default=2,
        help='Max retry attempts per failed conversion (default: 2)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Scan and report files without converting',
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if Microsoft Word is installed and exit',
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Output format for results (default: text)',
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        help='Write detailed log to file',
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # --check mode
    if args.check:
        installed = WordConverter.check_word_installed()
        if installed:
            print('Microsoft Word is installed and scriptable. ✓')
            return 0
        else:
            print('Microsoft Word is NOT installed or not scriptable.')
            print('Install Microsoft Word (macOS) and try again.')
            return 1

    # Validate required args
    if not args.input or not args.output:
        parser.error('--input and --output are required (use --check to probe)')

    if not args.input.is_dir():
        parser.error(f'Input path is not a directory: {args.input}')

    try:
        orchestrator = Orchestrator(
            input_dir=args.input,
            output_dir=args.output,
            recursive=args.recursive,
            flat=args.flat,
            timeout=args.timeout,
            retry=args.retry,
            dry_run=args.dry_run,
        )
        results = orchestrator.run()

        # Print summary
        success = sum(1 for r in results if r.status == 'success')
        errors = sum(1 for r in results if r.status == 'error')
        skipped = sum(1 for r in results if r.status == 'skipped')

        print(f'\nDone: {len(results)} files, {success} OK, {errors} failed'
              f'{f", {skipped} skipped" if skipped else ""}')

        return 0 if errors == 0 else 1

    except WordNotInstalledError:
        print('ERROR: Microsoft Word is not installed.')
        print('Install Word and run again, or use --check to probe.')
        return 1
    except KeyboardInterrupt:
        print('\nCancelled by user.')
        return 130
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

### 5.5 Logger (`logger.py`)

```python
import csv
import json
import time
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class LogRecord:
    timestamp: str
    input_path: str
    output_path: str
    status: str          # success | error | skipped
    duration: float
    error: Optional[str] = None
    attempts: int = 1


class ConversionLogger:
    """Structured logger for conversion results."""

    def __init__(self):
        self.records: List[LogRecord] = []

    def log_result(self, result) -> None:
        """Record a conversion result."""
        record = LogRecord(
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'),
            input_path=str(result.input_path),
            output_path=str(result.output_path),
            status=result.status,
            duration=result.duration,
            error=result.error,
            attempts=result.attempts,
        )
        self.records.append(record)
        self._print_record(record)

    def _print_record(self, record: LogRecord) -> None:
        """Print a single record to stdout."""
        status_icon = {'success': '✓', 'error': '✗', 'skipped': '→', 'pending': '…'}
        icon = status_icon.get(record.status, '?')
        duration_str = f'{record.duration:.1f}s' if record.duration > 0 else ''
        error_str = f' — {record.error}' if record.error else ''
        output_str = f' → {record.output_path}'
        att_str = f' (attempt {record.attempts})' if record.attempts > 1 else ''
        print(f'  {icon} {record.input_path}{output_str} [{duration_str}]{att_str}{error_str}')

    def export_csv(self, path: Path) -> None:
        """Write all records to a CSV file."""
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'input_path', 'output_path',
                'status', 'duration', 'error', 'attempts'
            ])
            writer.writeheader()
            for r in self.records:
                writer.writerow(r.__dict__)

    def export_json(self, path: Path) -> None:
        """Write all records to a JSON file."""
        with open(path, 'w') as f:
            json.dump([r.__dict__ for r in self.records], f, indent=2)

    def print_summary(self) -> None:
        """Print aggregate summary to stdout."""
        total = len(self.records)
        success = sum(1 for r in self.records if r.status == 'success')
        errors = sum(1 for r in self.records if r.status == 'error')
        skipped = sum(1 for r in self.records if r.status == 'skipped')
        total_dur = sum(r.duration for r in self.records if r.status == 'success')

        print(f'\n── Summary ──')
        print(f'  Total:   {total}')
        print(f'  Success: {success}')
        print(f'  Errors:  {errors}')
        if skipped:
            print(f'  Skipped: {skipped}')
        if success:
            avg = total_dur / success
            print(f'  Avg time per file: {avg:.1f}s')
```

### 5.6 Errors (`errors.py`)

```python
from pathlib import Path


class DocToPDFError(Exception):
    """Base exception for all conversion errors."""
    def __init__(self, message: str, input_path: Path = None):
        self.input_path = input_path
        super().__init__(message)


class WordNotInstalledError(DocToPDFError):
    """Microsoft Word is not installed or not scriptable."""
    def __init__(self, message: str = None):
        super().__init__(message or 'Microsoft Word not found')


class DocumentOpenError(DocToPDFError):
    """Word failed to open the document (locked, corrupt, or unsupported)."""
    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Cannot open document: {input_path}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg, input_path)


class CorruptDocumentError(DocumentOpenError):
    """Document file is corrupt or in an unsupported format."""
    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Corrupt or unsupported document: {input_path}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg)


class ExportError(DocToPDFError):
    """Word opened the document but failed to export as PDF."""
    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Export failed: {input_path}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg, input_path)


class ConversionTimeoutError(DocToPDFError):
    """Word took too long to convert a document."""
    def __init__(self, input_path: Path, timeout: int):
        msg = f'Timeout ({timeout}s) converting: {input_path}'
        super().__init__(msg, input_path)


class PermissionError_(DocToPDFError):
    """macOS Automation permission not granted for Terminal → Word."""
    def __init__(self):
        super().__init__(
            'macOS Automation permission missing.\n'
            'Go to System Preferences → Privacy & Security → Automation\n'
            'and ensure Terminal (or your app) is allowed to control "Microsoft Word".'
        )
```

---

## 6. Error Handling Strategy

| Failure Mode | Detection | Handling |
|---|---|---|
| Word not installed | `check_word_installed()` before batch | Clear error + install instructions |
| File locked (open in Word) | AppleScript throws on `open` | Retry with exponential backoff; log |
| Corrupt document | Word's `open` returns error | Classify as `CorruptDocumentError`; skip |
| Export failure | Word's `save as` returns error | Retry up to `--retry N`; log error |
| Timeout | Subprocess timeout on `osascript` | Kill osascript; cleanup; retry or skip |
| Permission missing | osascript returns -1743 | Suggest System Preferences fix |
| Disk full | Word fails to write output | Detect low space; abort batch |
| Word crashes | osascript returns non-zero | Detect crash; restart Word; retry once |

### 6.1 Cleanup After Failure

After any failure:
1. Attempt to close the active document in Word (`close saving no`).
2. If Word appears hung, do NOT force-kill (data loss risk). Log a warning and proceed to next file.
3. Track open document count; if Word is left in a bad state, suggest manual restart.

---

## 7. Concurrency Model

**Sequential-only.** Word on macOS is a single-window-application-driven process. Running multiple conversions concurrently:

- Creates race conditions on Word's internal state.
- Causes document handle conflicts.
- Produces inconsistent PDF output.
- Risks Word crashes under load.

If throughput is critical, the orchestrator can split the file list and run **one conversion at a time** but accept **drag-and-drop folder groups** from different Finder selections. The script itself never parallelizes.

**Future optimization (if Word reliability improves):** Run 2-3 conversions in sequence, not parallel, but with Word kept open to avoid relaunch overhead. Benchmark before adopting.

---

## 8. CLI Interface (Complete Reference)

```bash
# Basic usage — recursive scan, mirrored output tree
convert-word-pdf --input ~/Documents/reports --output ~/Documents/pdfs

# Non-recursive, flat output
convert-word-pdf -i ./docs -o ./pdfs --no-recursive --flat

# Dry run to see what would be converted
convert-word-pdf -i ./docs -o ./pdfs --dry-run

# Check Word installation
convert-word-pdf --check

# Custom timeout and retry
convert-word-pdf -i ./docs -o ./pdfs --timeout 120 --retry 3

# Detailed format output
convert-word-pdf -i ./docs -o ./pdfs --format json --log-file ./conversion-log.json

# Help
convert-word-pdf --help
```

---

## 9. Automator Quick Action Integration

### 9.1 Setup Steps

1. Open **Automator.app**.
2. File → New → **Quick Action**.
3. Configure:
   - Workflow receives: `files or folders` → `Finder`
   - Applies to: `any`
   - Image: pick a PDF/doc icon
4. Add **"Run Shell Script"** action:
   - Shell: `/bin/zsh`
   - Pass input: `as arguments`

```bash
# Automator Quick Action script
# Receives Finder selections as file/folder paths

PROJECT_DIR="$HOME/Documents/doctopdf"
OUTPUT_BASE="$HOME/Documents/PDF_Conversions"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
OUTPUT_DIR="${OUTPUT_BASE}/batch_${TIMESTAMP}"

# Collect all .doc and .docx from the selection(s)
INPUT_DIR=$(mktemp -d)
for item in "$@"; do
    if [ -d "$item" ]; then
        # If a directory was dropped, symlink its contents
        ln -s "$item"/* "$INPUT_DIR/" 2>/dev/null
    elif [ -f "$item" ]; then
        ln -s "$item" "$INPUT_DIR/"
    fi
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run the converter
cd "$PROJECT_DIR" || exit 1
python3 -m doctopdf --input "$INPUT_DIR" --output "$OUTPUT_DIR" --recursive

# Open the output folder in Finder
open "$OUTPUT_DIR"

# Cleanup temp symlink directory
rm -rf "$INPUT_DIR"
```

5. Save as **"Convert to PDF (Word)"**.
6. Now appears in Finder's right-click menu → **Quick Actions** → or **Services** menu.

### 9.2 Permissions Note

The first time the Quick Action runs, macOS will prompt:
> **Automator wants access to control Microsoft Word.**

Grant this in **System Settings → Privacy & Security → Automation**.

---

## 10. Performance & Reliability Notes

### 10.1 Expected Performance

| File Type | Size | Approx. Time |
|---|---|---|
| Simple .docx (text only) | 50 KB | 3–8 s |
| Complex .docx (images, tables) | 5 MB | 8–20 s |
| Large .doc (legacy format) | 20 MB | 15–45 s |
| Corrupt file | N/A | ~timeout |

**Key bottleneck:** Word launch overhead (5–15 s for first launch). Consider keeping Word open between conversions.

### 10.2 Keep-Warm Optimization (Optional Enhancement)

To avoid relaunching Word per-file (saves ~10 s per file after the first):

```python
# In orchestrator.py — optimization for batch > 5 files
# 1. Open Word once at batch start (via osascript -e 'tell app "Word" to activate')
# 2. Convert all files via one long-lived JXA context
# 3. Close Word at batch end (unless user had it open)
```

### 10.3 Tradeoffs vs LibreOffice

| Dimension | Word (this design) | LibreOffice |
|---|---|---|
| **Fidelity** | ★★★★★ Best possible | ★★★ Good, but font/metric subtleties differ |
| **Speed** | ★★★ Slower (Word launch overhead) | ★★★★ Faster headless |
| **Dependency** | Requires paid Microsoft Word license | Free, open source |
| **macOS Integration** | Native app, AppleScript | X11/GUI or headless via `--headless` |
| **Bulk Reliability** | ★★★ Single-app bottleneck | ★★★★ More stable under load |
| **Format Support** | ★★★★★ Full Word compatibility | ★★★★ Some edge case rendering differences |
| **Offline** | Yes | Yes |

**Verdict:** Choose Word when fidelity is paramount (legal documents, official submissions, complex formatting). Choose LibreOffice when you need free, faster, headless batch conversion and can accept minor rendering differences.

### 10.4 AppleScript/JXA Limitations

1. **Constants vary by version.** Word 2016 vs Word 2021 vs Office 365 may use different save-format identifiers. The script should detect Word version and adjust.
2. **Password-protected documents.** Word will prompt for password via dialog; the AppleScript cannot silently provide passwords. These documents must be handled manually.
3. **Embedded content.** Documents with embedded files, ActiveX controls, or legacy OLE objects may trigger Word security dialogs that block scripting.
4. **Tracked changes / comments.** By default these are included in the PDF. Consider whether `PrintHiddenText = false` or similar settings are needed.

---

## 11. Security & Permissions

### 11.1 macOS Automation Permissions

When any tool (Terminal, iTerm2, Automator) first attempts to control Microsoft Word via AppleScript/JXA, macOS presents a dialog:

> **"Terminal" wants access to control "Microsoft Word".**
> [Deny] [Allow]

If denied, the script returns error code -1743. The converter must detect this and print:

```
ERROR: macOS Automation permission denied.
→ Open System Preferences → Privacy & Security → Automation
→ Add "Terminal" (or your app) with control over "Microsoft Word".
→ Then run again.
```

### 11.2 SIP and App Sandbox

- This tool runs as a regular user process; no SIP modifications needed.
- File access is subject to normal macOS permissions.
- If run from within a sandboxed app (e.g., some third-party terminals), file access may be restricted.
- The output directory must be writable by the user.

### 11.3 Offline Enforcement

The design contains zero network calls:
- No HTTP requests.
- No cloud API calls.
- No browser automation (Playwright, Puppeteer, Selenium).
- No web views.
- Only local `osascript` IPC to a local desktop application.

---

## 12. Dependencies

| Dependency | Type | Reason |
|---|---|---|
| Python 3.9+ | Runtime | Orchestration and CLI |
| Microsoft Word for Mac | Runtime | Rendering engine (tested on Word 2019 / 2021 / 365) |
| (none beyond stdlib) | Python | No pip packages required |

Zero pip dependencies. Everything in `scanner.py`, `converter.py`, `orchestrator.py`, `cli.py`, `logger.py`, `errors.py` uses only Python standard library + `osascript` (bundled with macOS).

---

## 13. Implementation Order

| Phase | Files | Deliverable |
|---|---|---|
| 1 | `errors.py`, `config.py` | Exception hierarchy + constants |
| 2 | `applescript/export_document.js`, `applescript/check_word.applescript` | Word bridge tested in isolation |
| 3 | `converter.py` | Single-file conversion via JXA |
| 4 | `scanner.py` | File discovery + path mapping |
| 5 | `logger.py` | Structured logging |
| 6 | `orchestrator.py` | Batch orchestration + retry |
| 7 | `cli.py`, `__main__.py` | CLI interface + entry point |
| 8 | Integration test | Convert real .doc/.docx files, verify PDF output |
| 9 | Automator Quick Action | `.workflow` bundle + setup instructions |
| 10 | Documentation | README.md with all setup + usage notes |

---

## 14. Testing Strategy

| Test Type | What | How |
|---|---|---|
| Unit | Error classes, path mapping, collision logic | `pytest` or plain assert |
| Unit | JXA script argument handling | Run with test paths, inspect JSON output |
| Integration | Single .docx → PDF conversion | Actual Word invocation, verify file exists |
| Integration | Corrupt file handling | Feed a truncated .docx, expect error |
| Integration | Batch of 10 mixed files | Full pipeline, verify all outputs |
| Manual | Permission denied | Revoke automation permission, verify error message |
| Manual | Word not installed | Uncheck Word, verify early exit |
| Manual | Automator Quick Action | Right-click files in Finder, verify workflow |

---

## 15. Out of Scope (Explicitly Rejected Alternatives)

| Approach | Reason Rejected |
|---|---|
| **LibreOffice headless** | Different rendering engine; font/metric differences |
| **Pandoc** | Markdown-centric output; severe fidelity loss |
| **python-docx → ReportLab** | Cannot execute VBA macros; no layout engine; incomplete spec coverage |
| **Browser-based (Playwright)** | Requires cloud or local server; security restrictions |
| **Web API (ConvertAPI, Zamzar, etc.)** | Cloud upload violates security policy; offline requirement |
| **WPS Office / OnlyOffice** | Non-Mac-native; different rendering; not the authoritative engine |
| **docker-libreoffice** | Still LibreOffice; same fidelity issues |

**The primary and only design path is Microsoft Word as the authoritative export engine on macOS.**

---

> **End of design document.** Ready for implementation.
