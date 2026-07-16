# Checklist: Converter Exception Logging (#6)

- **Date**: 2026-07-16
- **Feature**: converter-exception-logging
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-6-converter-exception-logging/SPEC.md`

> **Purpose:** Verification strategy for #6 — confirms the silent-failure paths now emit observable diagnostics while remaining best-effort/non-fatal. All tests are unit-level (caplog + monkeypatch); **no Microsoft Word required**.

---

## Behavior-to-Test Checklist

| ID | Observable Behavior | SPEC Requirement | Corresponding Test | Result |
|---|---|---|---|---|
| CL-01 | `_cleanup_stale_word` logs a DEBUG record when its osascript call raises, and does not propagate | Req 1 | `test_cleanup_stale_word_logs_debug_no_raise` | `[pending]` |
| CL-02 | `quit_word` logs a DEBUG record on graceful-quit failure and still calls `_force_quit_word` | Req 2 | `test_quit_word_logs_debug_then_force_quits` | `[pending]` |
| CL-03 | `_force_quit_word` logs DEBUG (non-critical) on failure, does not raise | Req 1 (applies to all cleanup helpers) | `test_force_quit_word_logs_debug_no_raise` | `[pending]` |
| CL-04 | `restart_word` logs a WARNING when Word fails to relaunch within the polling window, and returns without raising | Req 3 | `test_restart_word_warns_when_no_relaunch` | `[pending]` |
| CL-05 | `_is_word_running` still returns `False` on exception (debug log added, return value preserved) | Edge / Invariant | `test_is_word_running_returns_false_on_error` | `[pending]` |
| CL-06 | `build_parser` exposes a `--verbose` flag; default is off | Req 4 | `test_parser_has_verbose_flag_default_false` | `[pending]` |
| CL-07 | With `--verbose`, the effective root log level is DEBUG; without it, a WARNING record is still emitted/visible | Req 4 | `test_verbose_sets_debug_level` / `test_warning_visible_by_default` | `[pending]` |

---

## Hardening Checklist

- [x] Regression tests for the bug-prone behavior (the silent `pass`) — the caplog tests above are exactly this.
- [ ] Unit drift checks for non-trivial logic — `N/A` (no new branching logic; log-and-continue).
- [ ] Property-based coverage — `N/A` (no business logic to property-test).
- [x] External services mocked / faked — `subprocess.run`, `time.sleep`, and `WordConverter.check_word_installed` are monkeypatched; no real osascript/Word.
- [ ] Adversarial cases for abuse paths — `N/A` (local CLI, no abuse surface).
- [ ] Authorization / idempotency / concurrency — `N/A` (single-threaded batch; no auth).
- [x] Assertions verify outcomes and side-effects (log records captured via `caplog.records` / `caplog.messages`), not just "no exception".
- [ ] Fixtures reproducible (fixed seed / clock) — `N/A` (no randomness; `time.sleep` patched to no-op so restart polling is deterministic and fast).

---

## E2E / Integration Decisions

| Flow / Risk | Test Level | Rationale |
|---|---|---|
| Logging emitted by cleanup/quit/restart helpers | Unit (caplog + monkeypatch) | The behavior is fully observable via captured log records; no real Word needed. |
| `--verbose` → `basicConfig` level wiring | Unit (parser + call assertion) | Asserting `build_parser` has the flag and that `main` configures DEBUG is sufficient; full CLI invocation would require mocking osascript in `--check`. |
| Real Word conversion with logging | Existing coverage / deferred | True end-to-end conversion is out of scope for #6 and inherently requires macOS + Word; covered manually if ever needed. |

---

## References

- **Designed code file paths**: `doctopdf/converter.py`, `doctopdf/cli.py`, `tests/test_converter_logging.py` (to create), `pyproject.toml`
- **Project context files**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-6-converter-exception-logging/DESIGN.md`, `PROPOSAL.md`
- **Related documents**:
  - SPEC: `issue-6-converter-exception-logging/SPEC.md`
  - `references/python-logging.md`, `references/pytest-caplog.md`
  - [pytest logging docs](https://docs.pytest.org/en/stable/how-to/logging.html)
