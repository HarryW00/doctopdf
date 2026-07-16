# Checklist: Error Record Helper Refactor (#3)

- **Date**: 2026-07-16
- **Feature**: error-record-helper
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-3-error-record-helper/SPEC.md`

> **Purpose:** Verify the refactor is behavior-preserving — every error branch produces a byte-identical `LogRecord` via the new helper.

---

## Behavior-to-Test Checklist

| ID | Observable Behavior | SPEC Requirement | Corresponding Test | Result |
|---|---|---|---|---|
| CL-01 | No inline `LogRecord(...)` remains in any `_convert_single` except block | Req 1 | `test_no_inline_logrecord_in_except_blocks` (AST/grep assertion) | `[pending]` |
| CL-02 | `WordPermissionError` → `status='error'`, `error=str(e)`, `attempts=1` | Req 2 | `test_permission_error_record` | `[pending]` |
| CL-03 | `CorruptDocumentError` → `attempts=1` | Req 2 | `test_corrupt_error_record` | `[pending]` |
| CL-04 | `ConversionTimeoutError` → `attempts=retry_count+1` | Req 2 | `test_timeout_error_record_attempts` | `[pending]` |
| CL-05 | `ExportError` → `attempts=retry_count+1` | Req 2 | `test_export_error_record_attempts` | `[pending]` |
| CL-06 | `DocToPDFError` (base) → `attempts=1` | Req 2 | `test_base_error_record` | `[pending]` |
| CL-07 | Catch-all `Exception` → `error` starts with `Unexpected error:`, `attempts=1` | Req 2 | `test_unexpected_error_prefix_preserved` | `[pending]` |
| CL-08 | All records share `status='error'`, ISO timestamp, 2-decimal duration from `start` | Req 2 | (covered by CL-02…07 parametrized) | `[pending]` |

> Implementation hint: use a fake converter whose `convert_with_retry` raises a given exception, plus a fixed `start` (monkeypatch `time.monotonic`) so duration is deterministic. Drive via `Orchestrator._convert_single` or call `_make_error_record` directly for the unit-level check.

---

## Hardening Checklist

- [x] Regression tests for the refactored paths — the parametrized record-equivalence tests above.
- [ ] Unit drift checks — `N/A` (no logic change; equivalence is the check).
- [ ] Property-based coverage — `N/A`.
- [x] External services mocked — a fake converter raises the desired exception; no Word.
- [ ] Adversarial / auth / concurrency — `N/A`.

---

## E2E / Integration Decisions

| Flow / Risk | Test Level | Rationale |
|---|---|---|
| `_convert_single` error branches | Unit (fake converter + monkeypatched clock) | Equivalence is fully observable from the returned `LogRecord`; no real conversion needed. |

---

## References

- **Designed code file paths**: `doctopdf/orchestrator.py`, `tests/test_orchestrator_error_record.py`
- **Related documents**: `issue-3-error-record-helper/SPEC.md`, `issue-3-error-record-helper/DESIGN.md`
