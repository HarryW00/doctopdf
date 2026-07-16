# Reference: pytest `caplog` fixture

Authoritative source: https://docs.pytest.org/en/stable/how-to/logging.html

## Purpose

`caplog` captures log records emitted during a test so we can assert that #6's
new `_log.debug`/`_log.warning` calls actually fire.

## Key facts (cite, do not guess)

| API | Behaviour |
|---|---|
| `caplog.records` | List of `logging.LogRecord` objects (each has `.levelno`, `.levelname`, `.message`, `.name`). |
| `caplog.messages` | List of format-interpolated message strings. |
| `caplog.set_level(level)` | Sets the capture level for the test (and the root logger). **Required to capture DEBUG** — pytest only captures WARNING+ by default. |
| Default capture | pytest auto-captures WARNING+ and shows it under "Captured log call" for failed tests; DEBUG records are dropped unless `set_level(DEBUG)`. |

## Pattern for #6 tests

```python
import logging
from doctopdf import converter

def test_cleanup_stale_word_logs_debug_no_raise(caplog, monkeypatch):
    def boom(*a, **kw):
        raise FileNotFoundError("osascript missing")
    monkeypatch.setattr(converter.subprocess, "run", boom)

    with caplog.at_level(logging.DEBUG, logger="doctopdf.converter"):
        converter.WordConverter._cleanup_stale_word()   # must not raise

    assert any(
        r.levelno == logging.DEBUG and "cleanup" in r.message.lower()
        for r in caplog.records
    )
```

## Constraints for #6

- For DEBUG assertions always use `caplog.at_level(logging.DEBUG, ...)` / `caplog.set_level(DEBUG)`.
- Monkeypatch `subprocess.run`, `time.sleep`, and `WordConverter.check_word_installed` so tests never invoke real osascript/Word and never actually sleep through `restart_word`'s 30s polling.
- Assert on **captured records** (side-effect), not merely that the call returned.
