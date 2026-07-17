# Reference: Python `logging` (stdlib)

Authoritative source: https://docs.python.org/3/library/logging.html and
https://docs.python.org/3/howto/logging.html

## Pattern used in #6

- **Library code** (`doctopdf/converter.py`): create one module logger, never configure it.
  ```python
  import logging
  _log = logging.getLogger(__name__)   # name == "doctopdf.converter"
  ```
  Emit with lazy `%`-style args (never f-strings in log calls):
  ```python
  except Exception as e:
      _log.debug("Stale Word cleanup failed (non-critical): %s", e)
  ```
- **Application entry** (`doctopdf/cli.py::main`): configure the root logger once.
  ```python
  logging.basicConfig(
      level=logging.DEBUG if args.verbose else logging.WARNING,
      format="%(levelname)s %(name)s: %(message)s",
      stream=sys.stderr,
  )
  ```

## Key facts (cite, do not guess)

| API | Behaviour |
|---|---|
| `logging.getLogger(name)` | Returns the same logger object for repeated calls with the same name; child loggers propagate records to ancestors up to the root. |
| `logging.basicConfig(...)` | Installs a `StreamHandler` on the **root** logger **only if** it has no handlers yet (no-op once configured). First caller wins. |
| Default library behaviour | With no `basicConfig`, a library logger has **no handler** → its records are dropped (nothing prints). This is why #6 must configure logging in the CLI. |
| Levels | `DEBUG=10`, `INFO=20`, `WARNING=30`, `ERROR=40`. A record is emitted only if `record.levelno >= logger.effectiveLevel`. |

## Constraints for #6

- Never call `basicConfig` from `converter.py` (library anti-pattern).
- Logging calls must not raise into the caller — keep the `try/except` structure; just replace `pass` with `_log.debug(...)`.
- Use `stream=sys.stderr` so stdlib logging stays separate from `ConversionLogger`'s stdout status lines.
