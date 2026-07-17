"""Tests for #4: exception messages, hierarchy, and the #9 fix."""
from pathlib import Path

from doctopdf.errors import (
    ConversionTimeoutError,
    CorruptDocumentError,
    DocToPDFError,
    DocumentOpenError,
    ExportError,
    FileAccessError,
    WordCrashError,
    WordNotInstalledError,
    WordPermissionError,
)


def test_docpdf_error_is_exception():
    assert issubclass(DocToPDFError, Exception)


def test_exception_hierarchy():
    assert issubclass(DocumentOpenError, DocToPDFError)
    assert issubclass(CorruptDocumentError, DocumentOpenError)
    assert issubclass(CorruptDocumentError, DocToPDFError)
    assert issubclass(ExportError, DocToPDFError)
    assert issubclass(ConversionTimeoutError, DocToPDFError)
    assert issubclass(FileAccessError, DocToPDFError)
    assert issubclass(WordCrashError, DocToPDFError)
    assert issubclass(WordPermissionError, DocToPDFError)
    assert issubclass(WordNotInstalledError, DocToPDFError)


def test_corrupt_document_error_constructs():  # CL-08a, issue #9
    e = CorruptDocumentError(Path("a.docx"), "bad file")
    assert e.input_path == Path("a.docx")
    assert "a.docx" in str(e)
    assert "Corrupt" in str(e)


def test_corrupt_document_error_no_detail():
    e = CorruptDocumentError(Path("a.docx"))
    assert e.input_path == Path("a.docx")
    assert "Corrupt" in str(e)


def test_export_carries_input_path():
    e = ExportError(Path("a.docx"), "fail")
    assert e.input_path == Path("a.docx")
    assert "a.docx" in str(e)


def test_timeout_message_contains_value():
    e = ConversionTimeoutError(Path("a.docx"), 60)
    assert e.input_path == Path("a.docx")
    assert "60" in str(e)


def test_word_permission_message():
    e = WordPermissionError()
    assert "permission" in str(e).lower()
