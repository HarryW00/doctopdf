"""
Exception hierarchy for all conversion failure modes.

Each exception carries the input_path it originated from, enabling
the orchestrator to log which file failed and why.
"""

from pathlib import Path
from typing import Optional


class DocToPDFError(Exception):
    """Base exception for all conversion errors."""

    def __init__(self, message: str, input_path: Optional[Path] = None):
        self.input_path = input_path
        super().__init__(message)


class WordNotInstalledError(DocToPDFError):
    """Microsoft Word is not installed or not scriptable via AppleScript/JXA."""

    def __init__(self, message: Optional[str] = None):
        super().__init__(
            message or (
                'Microsoft Word is not installed or not scriptable.\n'
                'Install Microsoft Word for macOS and try again.\n'
                'Run with --check to probe for Word.'
            )
        )


class WordPermissionError(DocToPDFError):
    """macOS Automation permission denied for the calling app → Microsoft Word."""

    def __init__(self):
        super().__init__(
            'macOS Automation permission denied.\n'
            '  → Open System Settings → Privacy & Security → Automation\n'
            '  → Ensure Terminal (or your app) is allowed to control "Microsoft Word".\n'
            '  → Then run again.'
        )


class DocumentOpenError(DocToPDFError):
    """Word failed to open the document (locked, missing, or unsupported)."""

    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Could not open document: {input_path.name}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg, input_path)


class CorruptDocumentError(DocumentOpenError):
    """Document file is corrupt or in an unsupported legacy format."""

    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Corrupt or unsupported document: {input_path.name}'
        if detail:
            msg += f' — {detail}'
        DocToPDFError.__init__(self, msg, input_path)


class ExportError(DocToPDFError):
    """Word opened the document but failed to export as PDF."""

    def __init__(self, input_path: Path, detail: str = ''):
        msg = f'Export to PDF failed: {input_path.name}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg, input_path)


class ConversionTimeoutError(DocToPDFError):
    """Word took longer than the configured timeout to convert."""

    def __init__(self, input_path: Path, timeout: int):
        msg = f'Timeout ({timeout}s) converting: {input_path.name}'
        super().__init__(msg, input_path)


class FileAccessError(DocToPDFError):
    """The output directory or file cannot be written."""

    def __init__(self, path: Path, detail: str = ''):
        msg = f'Cannot write to: {path}'
        if detail:
            msg += f' — {detail}'
        super().__init__(msg, path)


class WordCrashError(DocToPDFError):
    """Microsoft Word crashed or terminated unexpectedly during conversion."""

    def __init__(self, input_path: Path):
        msg = f'Microsoft Word crashed during conversion of: {input_path.name}'
        super().__init__(msg, input_path)
