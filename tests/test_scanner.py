"""Tests for #4: scanner discovery, mapping, collision (Word-free)."""
from pathlib import Path

from doctopdf.scanner import find_documents, map_output_path, resolve_collision


def _make_tree(tmp_path: Path) -> Path:
    (tmp_path / "a.docx").write_bytes(b"x" * 10)
    (tmp_path / "b.doc").write_bytes(b"x" * 10)
    (tmp_path / "ignore.pdf").write_bytes(b"x" * 10)
    (tmp_path / "ignore.txt").write_bytes(b"hello")
    (tmp_path / ".hidden.docx").write_bytes(b"x" * 10)
    (tmp_path / "~$lock.docx").write_bytes(b"x" * 10)
    (tmp_path / "empty.docx").write_bytes(b"")  # 0 bytes < MIN_FILE_SIZE_BYTES(1)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.docx").write_bytes(b"x" * 10)
    return tmp_path


def test_find_documents_filters_and_sorts(tmp_path):
    found = find_documents(_make_tree(tmp_path), recursive=True)
    names = [p.name for p in found]
    assert names == sorted(names)
    assert {"a.docx", "b.doc", "c.docx"} <= set(names)
    assert "ignore.pdf" not in names and "ignore.txt" not in names
    assert ".hidden.docx" not in names and "~$lock.docx" not in names
    assert "empty.docx" not in names


def test_find_documents_non_recursive(tmp_path):
    names = [p.name for p in find_documents(_make_tree(tmp_path), recursive=False)]
    assert "c.docx" not in names
    assert "a.docx" in names


def test_find_documents_missing_dir(tmp_path):
    assert find_documents(tmp_path / "nope", recursive=True) == []


def test_map_output_path_flat_and_mirrored(tmp_path):
    in_root = tmp_path / "in"
    out_root = tmp_path / "out"
    nested = in_root / "sub" / "report.docx"
    assert map_output_path(nested, in_root, out_root, flat=True) == out_root / "report.pdf"
    assert map_output_path(nested, in_root, out_root, flat=False) == out_root / "sub" / "report.pdf"


def test_map_output_path_outside_root(tmp_path):
    out_root = tmp_path / "out"
    outside = tmp_path / "elsewhere" / "x.docx"
    assert map_output_path(outside, tmp_path / "in", out_root, flat=False) == out_root / "x.pdf"


def test_resolve_collision_suffixes(tmp_path):
    base = tmp_path / "report.pdf"
    base.write_bytes(b"exists")
    first = resolve_collision(base)
    assert first == tmp_path / "report_1.pdf"
    (tmp_path / "report_1.pdf").write_bytes(b"exists")
    second = resolve_collision(base)
    assert second == tmp_path / "report_2.pdf"
    assert not second.exists()
