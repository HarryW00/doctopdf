"""
Configuration defaults and constants for the DocToPDF converter.

Centralises all tunable parameters so they can be adjusted without
digging through implementation modules.
"""

from pathlib import Path

# ── File discovery ──────────────────────────────────────────────
SUPPORTED_EXTENSIONS: set = {'.doc', '.docx'}
"""File extensions treated as convertible documents (case-insensitive)."""

MIN_FILE_SIZE_BYTES: int = 1
"""Files smaller than this (in bytes) are skipped as likely empty."""

# ── Conversion defaults ─────────────────────────────────────────
DEFAULT_TIMEOUT: int = 60
"""Seconds to wait for Word to convert a single document before timing out."""

DEFAULT_RETRY_COUNT: int = 2
"""Number of additional attempts per file after the first failure."""

DEFAULT_RETRY_DELAY: float = 2.0
"""Base seconds to wait between retries (actual = delay × attempt_number)."""

# ── Output structure ────────────────────────────────────────────
DEFAULT_OUTPUT_DIR: Path = Path.home() / 'Documents' / 'PDF_Conversions'
"""Fallback output directory when --output is not specified."""

DEFAULT_FLAT: bool = False
"""If True, write all PDFs to a single flat output directory instead of mirrored tree."""

# ── Logging ─────────────────────────────────────────────────────
DEFAULT_LOG_FORMAT: str = 'text'
"""One of 'text', 'json', 'csv'."""

# ── Path to bundled AppleScript/JXA assets ──────────────────────
SCRIPT_DIR: Path = Path(__file__).parent / 'applescript'

APPLESCRIPT_EXPORT_SCRIPT: Path = SCRIPT_DIR / 'export_document.applescript'
"""Primary: AppleScript that opens a document in Word and exports it as PDF."""

JXA_EXPORT_SCRIPT: Path = SCRIPT_DIR / 'export_document.js'
"""Fallback: JXA script that opens a document in Word and exports it as PDF."""

APPLESCRIPT_CHECK_WORD: Path = SCRIPT_DIR / 'check_word.applescript'
"""AppleScript that returns JSON indicating whether Word is installed."""

# ── Word version support ────────────────────────────────────────
# Some Word versions use different constant names for PDF format.
# This is probed at runtime but can be overridden.
WORD_FORMAT_PDF: str = 'PDF'
"""The format identifier used in Word's export command."""
