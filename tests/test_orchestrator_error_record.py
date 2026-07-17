"""Tests for #3: Orchestrator error-record helper (behavior-preserving)."""
import inspect
from pathlib import Path

import doctopdf.orchestrator as orchestrator_module
from doctopdf.errors import (
    ConversionTimeoutError,
    CorruptDocumentError,
    ExportError,
    WordPermissionError,
)
from doctopdf.orchestrator import Orchestrator


class _FakeConverter:
    def __init__(self, retry_count=2, exc=None):
        self.retry_count = retry_count
        self._exc = exc

    def convert_with_retry(self, input_path, output_path):
        if self._exc:
            raise self._exc


def _make_orch(exc, retry=2, tmp_path=None):
    orch = Orchestrator(
        input_dir=Path(tmp_path or "."), output_dir=Path(tmp_path or "."),
        dry_run=True, retry=retry,
    )
    orch.converter = _FakeConverter(retry_count=retry, exc=exc)
    return orch


def test_uses_make_error_record_helper():
    src = inspect.getsource(Orchestrator._convert_single)
    assert "self._make_error_record" in src


def test_permission_error_record(tmp_path):
    orch = _make_orch(WordPermissionError(), tmp_path=tmp_path)
    rec = orch._convert_single(Path("a.docx"), Path("a.pdf"), 1, 1)
    assert rec.status == "error"
    assert rec.attempts == 1
    assert rec.error == str(WordPermissionError())


def test_corrupt_error_record_attempts_default(tmp_path):
    orch = _make_orch(CorruptDocumentError(Path("a.docx")), tmp_path=tmp_path)
    rec = orch._convert_single(Path("a.docx"), Path("a.pdf"), 1, 1)
    assert rec.attempts == 1


def test_timeout_error_record_attempts(tmp_path):
    orch = _make_orch(ConversionTimeoutError(Path("a.docx"), 60), retry=2, tmp_path=tmp_path)
    rec = orch._convert_single(Path("a.docx"), Path("a.pdf"), 1, 1)
    assert rec.attempts == 3  # retry_count + 1


def test_export_error_record_attempts(tmp_path):
    orch = _make_orch(ExportError(Path("a.docx")), retry=2, tmp_path=tmp_path)
    rec = orch._convert_single(Path("a.docx"), Path("a.pdf"), 1, 1)
    assert rec.attempts == 3


def test_unexpected_error_prefix_preserved(tmp_path):
    orch = _make_orch(RuntimeError("boom"), tmp_path=tmp_path)
    rec = orch._convert_single(Path("a.docx"), Path("a.pdf"), 1, 1)
    assert rec.error.startswith("Unexpected error:")
    assert rec.attempts == 1
