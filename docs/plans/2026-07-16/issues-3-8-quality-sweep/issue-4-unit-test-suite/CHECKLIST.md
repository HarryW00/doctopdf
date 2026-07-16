# Checklist: Unit Test Suite (#4)

- **Date**: 2026-07-16
- **Feature**: unit-test-suite
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-4-unit-test-suite/SPEC.md`

> **Purpose:** This IS the test artifact. Maps each SPEC #4 BDD requirement to concrete test cases. All Word-free.

---

## Behavior-to-Test Checklist

| ID | Observable Behavior | SPEC Requirement | Corresponding Test | Result |
|---|---|---|---|---|
| CL-01 | `find_documents` returns only `.doc/.docx`, sorted, excluding hidden/`~$`/<min-size | Req 1 | `test_find_documents_filters_and_sorts` (tmp tree) | `[pending]` |
| CL-02 | `recursive=False` omits nested files | Req 1 | `test_find_documents_non_recursive` | `[pending]` |
| CL-03 | `find_documents` on missing dir → `[]` | Edge | `test_find_documents_missing_dir` | `[pending]` |
| CL-04 | `map_output_path` flat → `output_root/<stem>.pdf`; mirrored → preserves subdir | Req 2 | `test_map_output_path_flat_and_mirrored` | `[pending]` |
| CL-05 | `map_output_path` on path outside root → filename only | Edge | `test_map_output_path_outside_root` | `[pending]` |
| CL-06 | `resolve_collision` → `_1`, `_2`, …; never returns existing | Req 2 | `test_resolve_collision_suffixes` | `[pending]` |
| CL-07 | Each exception carries correct message + `input_path` | Req 3 | `test_exception_messages_and_paths` (parametrized) | `[pending]` |
| CL-08 | Hierarchy: `CorruptDocumentError`→`DocumentOpenError`→`DocToPDFError`→`Exception` | Req 3 | `test_exception_hierarchy` | `[pending]` |
| CL-09 | `convert` success returns expected dict; missing `attempts` defaults to 1 | Req 4/Edge | `test_convert_success` | `[pending]` |
| CL-10 | `convert` classifies: `-1743`→`WordPermissionError`; crash→`WordCrashError`; timeout→`ConversionTimeoutError`; `corrupt`→`CorruptDocumentError` | Req 4 | `test_convert_error_classification` (parametrized via mocked stdout/stderr) | `[pending]` |
| CL-11 | `convert_with_retry` does NOT retry terminal errors (`Corrupt`, `WordPermission`, `DocumentOpen`, `FileAccess`) | Req 4 | `test_no_retry_terminal_errors` (assert run-count == 1) | `[pending]` |
| CL-12 | `convert_with_retry` retries `ExportError`/`ConversionTimeoutError`/`WordCrashError` with linear backoff, then raises `ExportError("Failed after N attempts…")` | Req 4 | `test_retry_retriable_errors_linear_backoff` | `[pending]` |
| CL-13 | `pip install -e ".[dev]"` + `pytest tests/` runs Word-free, exits 0, emits coverage | Req 5 | `test_suite_runs_word_free` (CI/local smoke) | `[pending]` |

---

## Hardening Checklist

- [x] Regression tests for retry classification — CL-10/11/12.
- [ ] Property-based coverage — `N/A` (deterministic logic; parametrized suffices).
- [x] External services mocked — `subprocess.run` + `time.sleep` patched.
- [ ] Adversarial / auth / concurrency — `N/A`.
- [x] Assertions verify outcomes (exception type, run-count, returned dict), not just "no error".
- [x] Fixtures reproducible — `tmp_path` trees; `time.sleep` no-op.

---

## E2E / Integration Decisions

| Flow / Risk | Test Level | Rationale |
|---|---|---|
| Scanner over a real (temp) filesystem | Integration (tmp_path) | Exercises actual `glob`/`stat` |
| Converter retry policy | Unit (mocked subprocess) | Policy is fully observable via run-count + raised type |
| Real Word conversion | Out of scope | Requires macOS + Word; not part of #4 |

---

## References

- **Designed code file paths**: `doctopdf/scanner.py`, `doctopdf/errors.py`, `doctopdf/converter.py`, `pyproject.toml`, `tests/test_*.py`
- **Reference docs**: `references/pytest-mocking.md`
- **Related documents**: `issue-4-unit-test-suite/SPEC.md`, `issue-4-unit-test-suite/DESIGN.md`
