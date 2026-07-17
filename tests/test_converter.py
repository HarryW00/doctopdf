"""Tests for #4: converter classification + retry policy (Word-free)."""
import subprocess
from pathlib import Path

import pytest

from doctopdf.converter import WordConverter
from doctopdf.errors import (
    ConversionTimeoutError,
    CorruptDocumentError,
    DocumentOpenError,
    ExportError,
    FileAccessError,
    WordCrashError,
    WordPermissionError,
)


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_convert_success(monkeypatch, tmp_path):
    inp = tmp_path / "a.docx"
    inp.write_bytes(b"doc")
    out = tmp_path / "a.pdf"

    def fake_run(*a, **k):
        out.write_bytes(b"%PDF-1.5\nrest")
        return _completed(stdout='{"status": "ok"}', returncode=0)

    monkeypatch.setattr("doctopdf.converter.subprocess.run", fake_run)
    result = WordConverter().convert(inp, out)
    assert result["status"] == "success"
    assert result["attempts"] == 1


@pytest.mark.parametrize("stderr,exc_type", [
    ("-1743 not allowed", WordPermissionError),
    ("execution error -50", WordCrashError),
])
def test_convert_nonzero_stderr_classification(monkeypatch, tmp_path, stderr, exc_type):
    inp = tmp_path / "a.docx"
    inp.write_bytes(b"doc")
    out = tmp_path / "a.pdf"
    monkeypatch.setattr(
        "doctopdf.converter.subprocess.run",
        lambda *a, **k: _completed(stdout="", stderr=stderr, returncode=1),
    )
    with pytest.raises(exc_type):
        WordConverter().convert(inp, out)


def test_convert_timeout(monkeypatch, tmp_path):
    inp = tmp_path / "a.docx"
    inp.write_bytes(b"doc")
    out = tmp_path / "a.pdf"

    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="osascript", timeout=60)

    monkeypatch.setattr(WordConverter, "_cleanup_stale_word", lambda *a, **k: None)
    monkeypatch.setattr("doctopdf.converter.subprocess.run", boom)
    with pytest.raises(ConversionTimeoutError):
        WordConverter().convert(inp, out)


def test_convert_corrupt_classification(monkeypatch, tmp_path):
    inp = tmp_path / "a.docx"
    inp.write_bytes(b"doc")
    out = tmp_path / "a.pdf"
    monkeypatch.setattr(
        "doctopdf.converter.subprocess.run",
        lambda *a, **k: _completed(
            stdout='{"status":"error","error":"File is corrupt"}', returncode=0
        ),
    )
    with pytest.raises(CorruptDocumentError):  # relies on the #9 fix
        WordConverter().convert(inp, out)


@pytest.mark.parametrize("exc", [
    CorruptDocumentError(Path("a.docx")),
    WordPermissionError(),
    DocumentOpenError(Path("a.docx"), "locked"),
    FileAccessError(Path("a.docx")),
])
def test_no_retry_terminal_errors(monkeypatch, exc):
    calls = {"n": 0}

    def fake_convert(*a, **k):
        calls["n"] += 1
        raise exc

    monkeypatch.setattr(WordConverter, "convert", fake_convert)
    monkeypatch.setattr(WordConverter, "_cleanup_stale_word", lambda *a, **k: None)
    monkeypatch.setattr("doctopdf.converter.time.sleep", lambda *a, **k: None)
    c = WordConverter(retry_count=2)
    with pytest.raises(type(exc)):
        c.convert_with_retry(Path("a.docx"), Path("a.pdf"))
    assert calls["n"] == 1


@pytest.mark.parametrize("exc", [
    ExportError(Path("a.docx")),
    WordCrashError(Path("a.docx")),
    ConversionTimeoutError(Path("a.docx"), 60),
])
def test_retry_retriable_errors_linear_backoff(monkeypatch, exc):
    calls = {"n": 0}
    sleeps = []

    def fake_convert(*a, **k):
        calls["n"] += 1
        raise exc

    monkeypatch.setattr(WordConverter, "convert", fake_convert)
    monkeypatch.setattr(WordConverter, "_cleanup_stale_word", lambda *a, **k: None)
    monkeypatch.setattr("doctopdf.converter.time.sleep", lambda s, *a, **k: sleeps.append(s))
    c = WordConverter(retry_count=2, retry_delay=2.0)
    with pytest.raises(ExportError, match="Failed after"):
        c.convert_with_retry(Path("a.docx"), Path("a.pdf"))
    assert calls["n"] == 3          # initial + 2 retries
    assert sleeps == [2.0, 4.0]     # linear: retry_delay * attempt
