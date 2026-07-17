# Spec: Error Record Helper Refactor (#3)

- **Date**: 2026-07-16
- **Feature**: error-record-helper
- **Batch**: issues-3-8-quality-sweep — **sequence position 2 of 5** (order: #6 → #3 → #4 → #7 → #8)
- **Source issue**: GitHub #3 (refactor)

## Goal

Eliminate ~50 lines of near-duplicate `LogRecord` construction across the `except` blocks of `orchestrator._convert_single` by consolidating error-record creation into one private helper — a pure, behavior-preserving refactor.

## Scope

### In Scope

- Add a single private helper to `Orchestrator` that builds an error `LogRecord` (`status='error'`, current timestamp, input/output paths, duration measured from a `start` marker, error string, optional attempts).
- Replace **all five** error `except` blocks (`WordPermissionError`, `CorruptDocumentError`, `ConversionTimeoutError`, `ExportError`, `DocToPDFError`) **and** the catch-all `Exception` block in `_convert_single` with one-liner calls to the helper.
- Preserve the exact per-branch field values that exist today (see Requirement 2).

### Out of Scope

- Changing the **success**-path `LogRecord` construction.
- Changing the `LogRecord` dataclass fields or the `ConversionLogger` API.
- Reusing `ConversionLogger.from_result` (a design decision for the `design` phase; not required by this spec).
- Changing which exceptions are caught, their order, or how they are handled.
- Any change to retry counts, status strings, or user-visible output.

## Functional Behaviors (BDD)

### Requirement 1: All error outcomes flow through one shared helper
**GIVEN** `_convert_single` catches any handled error type (`WordPermissionError`, `CorruptDocumentError`, `ConversionTimeoutError`, `ExportError`, `DocToPDFError`) or an unexpected `Exception`
**WHEN** it builds the result record
**THEN** the record is produced by a single private helper method
**AND** no inline `LogRecord(...)` construction remains inside any `except` block of `_convert_single`

**Uncertainty Level**: Known

### Requirement 2: The refactor is behavior-preserving (per-branch fields identical)
**GIVEN** the pre-refactor and post-refactor code
**WHEN** the same exception is raised for the same file with the same `converter.retry_count`
**THEN** every field of the resulting `LogRecord` is identical to before — timestamp format (`%Y-%m-%dT%H:%M:%S`), `status='error'`, input/output paths, duration rounding (2 decimals from the same `start`), error text, and `attempts`
**AND** specifically: `attempts == retry_count + 1` for `ConversionTimeoutError` and `ExportError`; `attempts` defaults (1) for `WordPermissionError`, `CorruptDocumentError`, `DocToPDFError`, and the catch-all
**AND** the catch-all error text retains its `Unexpected error: {e}` prefix (not a bare `str(e)`)

**Uncertainty Level**: Known

## Error and Edge Cases

- A new exception type not in the current list → still reaches the catch-all and is formatted via the helper with the `Unexpected error:` prefix.
- Helper invoked with an explicit `attempts` override (timeout/export) versus the default (permission/corrupt/base) → both paths must yield the correct value.
- The `start` monotonic reference and 2-decimal duration rounding must be unchanged.
- The helper must not alter exception control flow — it builds a record only; it must not itself raise.

## Clarification Questions

- None. All requirements are Known and internally verifiable by comparing `LogRecord` output before and after.

## References

- **Key code file paths** affected by this spec:
  - `doctopdf/orchestrator.py` — `_convert_single:228` and the six `except` blocks at lines 255–317
  - `doctopdf/logger.py` — `LogRecord` dataclass (`:21`), `ConversionLogger.from_result` (`:152`, candidate for reuse during design)
- Related project context files:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
