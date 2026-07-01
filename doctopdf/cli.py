#!/usr/bin/env python3
"""
CLI module — command-line interface for DocToPDF.

Provides argument parsing and dispatches to the orchestrator.
Supports both standard CLI usage and Automator Quick Action invocation.

Usage:
    convert-word-pdf --input ./docs --output ./pdfs
    convert-word-pdf --input ./docs --output ./pdfs --recursive --flat
    convert-word-pdf --check
    convert-word-pdf --input ./docs --output ./pdfs --dry-run
    convert-word-pdf --version
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .orchestrator import Orchestrator
from .converter import WordConverter
from .errors import WordNotInstalledError, WordPermissionError, FileAccessError


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser with all CLI options."""
    parser = argparse.ArgumentParser(
        prog='convert-word-pdf',
        description=(
            'Batch convert .doc and .docx files to PDF using Microsoft Word. '
            'Runs entirely offline with no cloud dependencies.'
        ),
        epilog=(
            'Examples:\n'
            '  %(prog)s --input ./docs --output ./pdfs\n'
            '  %(prog)s --input ./docs --output ./pdfs --recursive --flat\n'
            '  %(prog)s --check\n'
            '  %(prog)s --input ./docs --output ./pdfs --dry-run\n'
            '\n'
            'Requires Microsoft Word for macOS. Automator Quick Action:\n'
            '  See README.md for Finder right-click integration.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Required (or alternative) ───────────────────────────────
    parser.add_argument(
        '--input', '-i',
        type=Path,
        metavar='DIR',
        help='Input directory containing .doc/.docx files',
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        metavar='DIR',
        help='Output directory for generated PDF files',
    )

    # ── Scanning options ────────────────────────────────────────
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='Recursively scan input subdirectories (default: on)',
    )
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not scan subdirectories (top-level only)',
    )
    parser.add_argument(
        '--flat',
        action='store_true',
        default=False,
        help=(
            'Write all PDFs flat into output directory instead of '
            'mirroring the input folder structure'
        ),
    )

    # ── Conversion options ──────────────────────────────────────
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        metavar='SEC',
        help='Seconds to wait per document before timing out (default: 60)',
    )
    parser.add_argument(
        '--retry',
        type=int,
        default=2,
        metavar='N',
        help='Number of retries per failed conversion (default: 2)',
    )
    parser.add_argument(
        '--restart-every',
        type=int,
        default=10,
        metavar='N',
        help='Restart Word after N successful conversions (0 = never restart, '
             'the default). Useful to prevent state degradation in very large '
             'batches (100+ files).',
    )

    # ── Output options ──────────────────────────────────────────
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Scan and report files without performing conversion',
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        metavar='FILE',
        help='Write structured log to FILE (.json or .csv)',
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress per-file status output (summary only)',
    )

    # ── Utility ─────────────────────────────────────────────────
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if Microsoft Word is installed and scriptable, then exit',
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}',
        help='Show version number and exit',
    )

    return parser


def cmd_check() -> int:
    """Probe for Microsoft Word and report status."""
    installed, info = WordConverter.check_word_installed()

    if installed:
        print(f'✓ Microsoft Word is installed (version: {info})')
        print('  The automation bridge is operational.')
        return 0
    else:
        print('✗ Microsoft Word is NOT installed or not scriptable.')
        print()
        print('  To use this tool, install Microsoft Word for macOS:')
        print('    - Microsoft 365 (subscription)')
        print('    - Microsoft Office 2019 or later (one-time purchase)')
        print()
        print('  After installing Word, grant Automation permissions:')
        print('    System Settings → Privacy & Security → Automation')
        print('    → Allow Terminal (or your app) to control "Microsoft Word"')
        print()
        print(f'  Probe details: {info}')
        return 1


def cmd_validate_args(args: argparse.Namespace) -> Optional[str]:
    """Validate mutually-dependent arguments. Returns error string or None."""
    if not args.input and not args.check:
        return '--input is required (use --check to probe for Word)'

    if args.input and not args.input.is_dir():
        return f'Input path is not a directory or does not exist: {args.input}'

    if not args.output and not args.check and not args.dry_run:
        # In dry-run mode, output is not strictly needed
        if args.input:
            return '--output is required for conversion (omit with --dry-run)'

    if args.log_file:
        parent = Path(args.log_file).parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return f'Cannot create directory for log file: {args.log_file}'

    return None


def cmd_convert(args: argparse.Namespace) -> int:
    """Run the batch conversion."""
    # If no --output was given but we have --input, use a default
    output_dir = args.output
    if not output_dir and args.input:
        output_dir = Path.home() / 'Documents' / 'PDF_Conversions'
        print(f'  Output directory not specified, using: {output_dir}')

    orchestrator = Orchestrator(
        input_dir=args.input,
        output_dir=output_dir,
        recursive=args.recursive,
        flat=args.flat,
        timeout=args.timeout,
        retry=args.retry,
        restart_every=args.restart_every,
        dry_run=args.dry_run,
        log_file=args.log_file,
    )

    try:
        results = orchestrator.run()
    except KeyboardInterrupt:
        print('\n\nCancelled by user.')
        return 130

    success = orchestrator.success_count
    errors = orchestrator.error_count

    if orchestrator.dry_run:
        return 0

    # Print opening line if output was created
    if success > 0:
        print(f'\n  PDFs written to: {output_dir}')

    # Return non-zero if any errors occurred
    return 0 if errors == 0 else 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI entry point.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 = success, 1 = error, 130 = cancelled).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # ── Mode dispatch ──────────────────────────────────────────
    if args.check:
        return cmd_check()

    # ── Validate ────────────────────────────────────────────────
    error_msg = cmd_validate_args(args)
    if error_msg:
        parser.error(error_msg)
        return 2  # pragma: no cover

    # ── Convert ─────────────────────────────────────────────────
    try:
        return cmd_convert(args)
    except WordNotInstalledError:
        print('ERROR: Microsoft Word is not installed or not scriptable.')
        print('  Run with --check for diagnostic information.')
        print('  Alternatively, install Microsoft Word for macOS.')
        return 1
    except WordPermissionError as e:
        print(f'ERROR: {e}')
        return 1
    except FileAccessError as e:
        print(f'ERROR: {e}')
        return 1
    except Exception as e:
        print(f'ERROR: Unexpected error: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
