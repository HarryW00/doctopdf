# issue-3-error-record-helper implementation plan

- `<spec_dir>` = `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-3-error-record-helper` — Context
- `<checklist_dir>` = same — `CHECKLIST.md`

## ROLE

You are the **coordinator** for issue #3 (Error Record Helper). Your job is to deliver a pure, behavior-preserving refactor that consolidates the six duplicated `LogRecord(...)` constructions in `_convert_single` into one `_make_error_record` helper — verified by equivalence tests — by **dispatching a worker** and gating on its results. You do not write code yourself.

## RULES

### ALWAYS
- Read the PREPARATION files before dispatching.
- Dispatch the worker with its full prompt; run the verification gate yourself; confirm green before accepting.
- Confirm byte-equivalence is asserted by the tests (status, attempts per branch, `Unexpected error:` prefix).

### ASK FIRST
- Worker cannot find a target block, or any error `LogRecord` field would change.
- Any file outside `doctopdf/orchestrator.py` / `tests/test_orchestrator_error_record.py` needs editing.
- Worker fails its gate twice.

### NEVER
- Write code yourself; change the success-path `LogRecord`; change caught exceptions or order; skip the gate; spawn nested workers.

### Failure handling
- Re-dispatch the same prompt once on failure; on second failure, STOP and escalate with the report.

## WORKING STEPS

### 1. PREPARATION
Read: `SPEC.md` (Req 1–2), `DESIGN.md` (helper takes error **string**; per-branch `attempts`; `from_result` considered/rejected), `CHECKLIST.md` (CL-01…CL-08), `plan/T1.1-error-record-helper-and-test.md`.

### 2. COORDINATION
**Batch 1 — single worker** (one coupled unit: refactor + its equivalence test; tests depend on the refactored API, so they are not split):
- Dispatch Worker T1.1 with prompt `plan/T1.1-error-record-helper-and-test.md` → edits `doctopdf/orchestrator.py`, creates `tests/test_orchestrator_error_record.py`.

**Gate after Batch 1:**
- `python -c "import doctopdf.orchestrator"` → no error.
- `pytest tests/test_orchestrator_error_record.py -q` → all pass.

### 3. FINAL VERIFICATION
- [ ] `pytest tests/test_orchestrator_error_record.py -q` green (CL-01…CL-08 equivalence).
- [ ] `_convert_single` except blocks call `self._make_error_record`; success path unchanged.
- [ ] `python -c "import doctopdf.orchestrator, doctopdf.cli"` still imports (no regression).
Report pass/fail per gate, files changed, test summary.
