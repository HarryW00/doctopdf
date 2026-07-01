"""
Scanner module — file discovery and output path mapping.

Responsible for walking the input directory tree, filtering for
supported document formats, and deterministically mapping each
input file to its intended output PDF path.
"""

from pathlib import Path
from typing import List

from .config import SUPPORTED_EXTENSIONS, MIN_FILE_SIZE_BYTES


def find_documents(
    input_dir: Path,
    recursive: bool = True,
    min_size_bytes: int = MIN_FILE_SIZE_BYTES,
) -> List[Path]:
    """
    Recursively discover supported document files under input_dir.

    Files are returned in sorted (ASCII-betical) order to ensure
    deterministic processing order across runs.

    Args:
        input_dir: Directory to scan.
        recursive: If True, descend into subdirectories.
        min_size_bytes: Skip files smaller than this threshold.

    Returns:
        Sorted list of Path objects for matching files.
    """
    input_dir = Path(input_dir).resolve()

    if not input_dir.is_dir():
        return []

    pattern = '**/*' if recursive else '*'
    matches: List[Path] = []

    for path in input_dir.glob(pattern):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.stat().st_size < min_size_bytes:
            continue
        # Skip hidden files and files in hidden directories
        if any(part.startswith('.') for part in path.relative_to(input_dir).parts):
            continue
        # Skip Word temporary/lock files (start with ~$)
        if path.name.startswith('~$'):
            continue

        matches.append(path)

    return sorted(matches)


def map_output_path(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    flat: bool = False,
) -> Path:
    """
    Map an input document path to its intended output PDF path.

    In mirrored-tree mode (default), preserves the relative directory
    structure under the output root:

        input:  /docs/subdir/report.docx
        output: /pdfs/subdir/report.pdf

    In flat mode, all PDFs land directly in the output directory,
    with only the filename (suffix changed to .pdf).

    Args:
        input_path: Path to the source document.
        input_root: Root of the input directory tree.
        output_root: Root of the output directory tree.
        flat: If True, flatten the directory structure.

    Returns:
        Output Path with .pdf extension.
    """
    input_root = Path(input_root).resolve()
    output_root = Path(output_root).resolve()
    input_path = Path(input_path)

    if flat:
        return output_root / f'{input_path.stem}.pdf'
    else:
        try:
            rel = input_path.resolve().relative_to(input_root)
        except ValueError:
            # Path is outside input_root — use just the filename
            rel = Path(input_path.name)
        return output_root / rel.with_suffix('.pdf')


def resolve_collision(output_path: Path, max_attempts: int = 1000) -> Path:
    """
    Append a numeric suffix (_1, _2, …) when the output path already exists.

    Args:
        output_path: The originally desired output path.
        max_attempts: Safety limit to prevent infinite loops.

    Returns:
        A non-existent path with a collision-avoiding suffix.
    """
    if not output_path.exists():
        return output_path

    stem = output_path.stem
    parent = output_path.parent

    for counter in range(1, max_attempts + 1):
        candidate = parent / f'{stem}_{counter}.pdf'
        if not candidate.exists():
            return candidate

    # Fallback (extremely unlikely): timestamp
    import time
    return parent / f'{stem}_{int(time.time())}.pdf'


def resolve_input_paths(input_paths: List[Path], recursive: bool = True) -> List[Path]:
    """
    Normalise a mix of file and directory arguments into a flat list
    of document files.

    Directories are expanded via find_documents; individual files are
    kept if they have a supported extension.

    Args:
        input_paths: List of file and/or directory paths.
        recursive: Whether to recurse into subdirectories.

    Returns:
        Sorted list of document paths, deduplicated.
    """
    documents: List[Path] = []

    for path in input_paths:
        path = Path(path).resolve()
        if path.is_dir():
            documents.extend(find_documents(path, recursive=recursive))
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(path)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for doc in documents:
        if doc not in seen:
            seen.add(doc)
            unique.append(doc)

    return sorted(unique)
