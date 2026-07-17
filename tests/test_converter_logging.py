"""Tests for #6: converter cleanup/quit/restart logging (Word-free)."""
import logging

from doctopdf import converter


def _raise(*_a, **_k):
    raise FileNotFoundError("osascript missing")


def test_cleanup_stale_word_logs_debug_no_raise(caplog, monkeypatch):
    monkeypatch.setattr(converter.subprocess, "run", _raise)
    with caplog.at_level(logging.DEBUG, logger="doctopdf.converter"):
        converter.WordConverter._cleanup_stale_word()
    assert any(
        r.levelno == logging.DEBUG and "cleanup" in r.message.lower()
        for r in caplog.records
    )


def test_force_quit_word_logs_debug_no_raise(caplog, monkeypatch):
    monkeypatch.setattr(converter.subprocess, "run", _raise)
    with caplog.at_level(logging.DEBUG, logger="doctopdf.converter"):
        converter.WordConverter._force_quit_word()
    assert any(
        r.levelno == logging.DEBUG and "force-quit" in r.message.lower()
        for r in caplog.records
    )


def test_quit_word_logs_debug_then_force_quits(caplog, monkeypatch):
    monkeypatch.setattr(converter.subprocess, "run", _raise)
    called = {"force": False}

    def fake_force():
        called["force"] = True

    monkeypatch.setattr(converter.WordConverter, "_force_quit_word", fake_force)
    with caplog.at_level(logging.DEBUG, logger="doctopdf.converter"):
        converter.WordConverter.quit_word()
    assert called["force"] is True
    assert any(
        r.levelno == logging.DEBUG
        and ("graceful" in r.message.lower() or "force-quit" in r.message.lower())
        for r in caplog.records
    )


def test_is_word_running_returns_false_on_error(caplog, monkeypatch):
    monkeypatch.setattr(converter.subprocess, "run", _raise)
    with caplog.at_level(logging.DEBUG, logger="doctopdf.converter"):
        result = converter.WordConverter._is_word_running()
    assert result is False
    assert any("process check" in r.message.lower() for r in caplog.records)


def test_restart_word_warns_when_no_relaunch(caplog, monkeypatch):
    monkeypatch.setattr(converter.WordConverter, "_force_quit_word", lambda: None)
    monkeypatch.setattr(converter.WordConverter, "_is_word_running", lambda: False)
    monkeypatch.setattr(
        converter.WordConverter, "check_word_installed", lambda: (False, "no word")
    )
    monkeypatch.setattr(converter.time, "sleep", lambda *_a, **_k: None)
    with caplog.at_level(logging.WARNING, logger="doctopdf.converter"):
        converter.WordConverter.restart_word()
    assert any(
        r.levelno == logging.WARNING and "did not relaunch" in r.message.lower()
        for r in caplog.records
    )
