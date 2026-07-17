"""
Converter module — Microsoft Word automation bridge.

Provides the WordConverter class which uses AppleScript (via osascript)
to open a document in Microsoft Word and export it as PDF.

All interaction with Word is through AppleScript via osascript(1);
no Python-to-Word native bridge is used. A JXA fallback is available
but AppleScript is the primary, battle-tested path for Word automation.

Typical usage:
    converter = WordConverter(timeout=60, retry_count=2)
    result = converter.convert_with_retry(
        Path('/input/report.docx'),
        Path('/output/report.pdf')
    )
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Tuple

_logger = logging.getLogger(__name__)

from .config import APPLESCRIPT_EXPORT_SCRIPT, APPLESCRIPT_CHECK_WORD
from .errors import (
    WordPermissionError,
    DocumentOpenError,
    CorruptDocumentError,
    ExportError,
    ConversionTimeoutError,
    WordCrashError,
    FileAccessError,
)


_log = logging.getLogger(__name__)


class WordConverter:
    """Manages the Microsoft Word automation bridge for a single conversion."""

    # ═══════════════════════════════════════════════════════════════
    # BRIDGE SELECTION
    # ═══════════════════════════════════════════════════════════════
    #
    # Microsoft Word on macOS is automated via AppleScript (the
    # osascript CLI). Two script engines are available:
    #
    #   1. AppleScript (.applescript) — PRIMARY.
    #      Battle-tested, works reliably across Word 2016 → 365.
    #      Uses `save as ... file format format PDF`.
    #
    #   2. JXA/JavaScript (.js) — FALLBACK.
    #      Available but has known issues with Word's `open` method
    #      returning null on some versions.
    #
    # The AppleScript bridge is the default. JXA can be enabled by
    # setting bridge='jxa' for testing or fallback scenarios.
    # ═══════════════════════════════════════════════════════════════

    def __init__(
        self,
        timeout: int = 60,
        retry_count: int = 2,
        retry_delay: float = 2.0,
        bridge: str = 'applescript',
    ):
        """
        Args:
            timeout: Max seconds to wait for a single Word conversion.
            retry_count: Number of retry attempts after initial failure.
            retry_delay: Base delay in seconds between retries (scaled by attempt).
            bridge: 'applescript' (default) or 'jxa'.
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.bridge = bridge.lower()

    @property
    def _script_path(self) -> Path:
        """Return the bridge script path based on selected engine."""
        if self.bridge == 'jxa':
            from .config import JXA_EXPORT_SCRIPT
            return JXA_EXPORT_SCRIPT
        return APPLESCRIPT_EXPORT_SCRIPT

    @property
    def _script_args(self) -> list:
        """Return osascript arguments. AppleScript uses -e; JXA uses -l JavaScript."""
        if self.bridge == 'jxa':
            return ['osascript', '-l', 'JavaScript', str(self._script_path)]
        return ['osascript', str(self._script_path)]

    # ── Installation check ─────────────────────────────────────

    @staticmethod
    def check_word_installed() -> Tuple[bool, str]:
        """
        Probe whether Microsoft Word is installed and scriptable.

        Returns:
            (True, version_str) if Word is available.
            (False, error_msg) otherwise.
        """
        try:
            result = subprocess.run(
                ['osascript', str(APPLESCRIPT_CHECK_WORD)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return False, result.stderr.strip() or 'osascript failed'

            data = json.loads(result.stdout.strip())
            if data.get('installed') is True:
                return True, data.get('version', 'unknown')
            else:
                return False, data.get('error', 'Word not scriptable')

        except subprocess.TimeoutExpired:
            return False, 'osascript probe timed out'
        except json.JSONDecodeError:
            return False, 'Cannot parse Word probe result'
        except FileNotFoundError:
            return False, 'osascript not found (not macOS?)'
        except Exception as e:
            return False, str(e)

    # ── Single conversion ───────────────────────────────────────

    def convert(self, input_path: Path, output_path: Path) -> Dict:
        """
        Convert a single document to PDF via the AppleScript bridge.

        The bridge:
          1. Opens the document in Word (via `open ... as POSIX file as alias`).
          2. Exports as PDF (`save as ... file format format PDF`).
          3. Closes the document without saving changes.
          4. Returns JSON status to stdout.

        Args:
            input_path: Absolute path to the source .doc/.docx file.
            output_path: Desired path for the output .pdf file.

        Returns:
            Dictionary with keys: status, input, output, duration.

        Raises:
            WordNotInstalledError
            WordPermissionError
            DocumentOpenError / CorruptDocumentError
            ExportError
            ConversionTimeoutError
            WordCrashError
            FileAccessError
        """
        abs_input = str(input_path.resolve())
        abs_output = str(output_path.resolve())

        # ── Quick sanity checks before invoking Word ────────────
        if not input_path.exists():
            raise FileAccessError(input_path, 'File does not exist')

        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise FileAccessError(output_dir, str(e))
        elif not os.access(str(output_dir), os.W_OK):
            raise FileAccessError(output_dir, 'Output directory not writable')

        # ── Build osascript command ─────────────────────────────
        cmd = self._script_args + [abs_input, abs_output, str(self.timeout)]

        start_time = time.monotonic()

        try:
            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 15,  # 15s grace for osascript overhead
            )
        except subprocess.TimeoutExpired:
            self._cleanup_stale_word()
            raise ConversionTimeoutError(input_path, self.timeout)

        duration = round(time.monotonic() - start_time, 2)

        # ── Handle osascript failures ───────────────────────────
        if proc_result.returncode != 0:
            stderr = (proc_result.stderr or '').strip()

            # Detect permission error (-1743 = AppleScript permission denied)
            if '-1743' in stderr or 'not allowed' in stderr.lower() \
               or 'permission' in stderr.lower():
                raise WordPermissionError()

            # Detect Word crash
            if 'execution error' in stderr.lower() or 'killed' in stderr.lower():
                raise WordCrashError(input_path)

            # Generic osascript failure
            raise ExportError(
                input_path,
                stderr or f'osascript exit code {proc_result.returncode}'
            )

        # ── Parse the JSON result from the AppleScript ──────────
        stdout = (proc_result.stdout or '').strip()
        if not stdout:
            raise ExportError(input_path, 'Bridge script produced no output')

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise ExportError(
                input_path,
                f'Cannot parse bridge JSON output: {e}\nOutput: {stdout[:200]}'
            )

        # ── Interpret the result ────────────────────────────────
        status = data.get('status', 'error')

        if status == 'error':
            error_msg = data.get('error', 'Unknown error from Word')

            # Classify the error type
            if 'corrupt' in error_msg.lower() or 'bad file' in error_msg.lower():
                raise CorruptDocumentError(input_path, error_msg)
            elif 'read' in error_msg.lower() or 'open' in error_msg.lower() \
                 or 'not found' in error_msg.lower() or 'null' in error_msg.lower():
                raise DocumentOpenError(input_path, error_msg)
            elif '-1743' in error_msg:
                raise WordPermissionError()
            else:
                raise ExportError(input_path, error_msg)

        # ── Verify output exists ────────────────────────────────
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ExportError(input_path, 'No PDF file produced (empty or missing)')

        # Quick verification: check PDF header
        try:
            with open(output_path, 'rb') as f:
                header = f.read(5)
            if header != b'%PDF-':
                raise ExportError(
                    input_path,
                    f'Output file is not a valid PDF (header: {header!r})'
                )
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(input_path, f'Cannot verify output PDF: {e}')

        return {
            'status': 'success',
            'input': str(input_path),
            'output': str(output_path),
            'duration': duration,
            'attempts': 1,
        }

    # ── Retry wrapper ───────────────────────────────────────────

    def convert_with_retry(self, input_path: Path, output_path: Path) -> Dict:
        """
        Convert a document with automatic retry on recoverable failures.

        Retries on:
        - ExportError (Word may have transient state issues)
        - ConversionTimeoutError (Word may be busy from prior conversion)
        - WordCrashError (restart Word between attempts)

        Does NOT retry on:
        - CorruptDocumentError (retrying won't help)
        - WordPermissionError (user must fix permissions)
        - DocumentOpenError (locked files stay locked)
        - FileAccessError (disk/environment issue)

        Args:
            input_path: Absolute path to the source document.
            output_path: Desired path for the output PDF.

        Returns:
            Same format as convert().
        """
        terminal_errors = (
            CorruptDocumentError,
            WordPermissionError,
            DocumentOpenError,
            FileAccessError,
        )

        last_error = None

        for attempt in range(1, self.retry_count + 2):  # +1 for the initial try
            try:
                result = self.convert(input_path, output_path)
                if attempt > 1:
                    result['attempts'] = attempt
                return result

            except terminal_errors:
                raise  # Don't retry these

            except (ExportError, ConversionTimeoutError, WordCrashError) as e:
                last_error = e
                if attempt <= self.retry_count:
                    wait = self.retry_delay * attempt
                    time.sleep(wait)
                    self._cleanup_stale_word()
                    continue
                raise ExportError(
                    input_path,
                    f'Failed after {self.retry_count + 1} attempts. '
                    f'Last error: {e}'
                )

        raise ExportError(
            input_path,
            f'Failed after all retries. Last error: {last_error}'
        )

    # ── Cleanup helpers ─────────────────────────────────────────

    @staticmethod
    def _cleanup_stale_word() -> None:
        """
        Attempt to close stray Word documents without saving.

        We deliberately do NOT force-kill Word to avoid data loss —
        the user may have other documents open.
        """
        try:
            cleanup_script = '''
try
    tell application "Microsoft Word"
        if not (exists document 1) then return
        set docCount to count documents
        if docCount > 0 then
            close every document saving no
        end if
    end tell
end try
'''
            subprocess.run(
                ['osascript', '-e', cleanup_script],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            _logger.warning(
                "Word cleanup failed (non-fatal)", exc_info=True
            )

    @staticmethod
    def quit_word() -> None:
        """
        Ask Microsoft Word to quit gracefully (saving no documents).

        In a batch automation context, Word may have invisible dialogs
        that block AppleScript. If graceful quit fails, falls back to
        force-quit via pkill.
        """
        try:
            quit_script = '''
try
    tell application "Microsoft Word"
        close every document saving no
        quit saving no
    end tell
end try
'''
            subprocess.run(
                ['osascript', '-e', quit_script],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            _logger.warning(
                "Word graceful quit failed (non-fatal)", exc_info=True
            )

        # Verify Word actually exited; force if necessary
        WordConverter._force_quit_word()

    @staticmethod
    def _force_quit_word() -> None:
        """Force-kill Microsoft Word process if still running."""
        try:
            subprocess.run(
                ['pkill', '-x', 'Microsoft Word'],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            _logger.warning(
                "Force-quit Word failed (non-fatal)", exc_info=True
            )

    @staticmethod
    def restart_word() -> None:
        """
        Restart Microsoft Word to clear accumulated state.

        Uses force-quit (pkill) because in a batch context there are
        no user documents to protect — the converter only opens,
        exports, and closes its own documents.

        After killing, waits for Word to fully relaunch and become
        responsive before returning.
        """
        WordConverter._force_quit_word()
        # Wait for process to fully disappear
        for _ in range(30):
            if not WordConverter._is_word_running():
                break
            time.sleep(0.5)

        time.sleep(1)  # Extra settle time after kill

        # Trigger Word launch and wait until it's responsive
        # by repeatedly probing with the check-word script.
        installed = False
        for _ in range(30):  # Up to 30s for Word to launch
            installed, _ = WordConverter.check_word_installed()
            if installed:
                time.sleep(1)  # Extra settle after Word reports ready
                return
            time.sleep(1)

        # If Word didn't launch, next conversion will fail with a clear error
        _log.warning(
            "Microsoft Word did not relaunch within 30s after restart. "
            "Next conversion may fail."
        )

    @staticmethod
    def _is_word_running() -> bool:
        """Check if Microsoft Word process is currently running."""
        try:
            check = [
                'osascript', '-e',
                'tell application "System Events" to '
                'exists process "Microsoft Word"'
            ]
            result = subprocess.run(check, capture_output=True, text=True, timeout=5)
            return result.stdout.strip() == 'true'
        except Exception:
            _logger.warning(
                "Word process check failed (non-fatal)", exc_info=True
            )
            return False
