# issue-4-unit-test-suite implementation plan

- `<spec_dir>` = `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-4-unit-test-suite` — Context
- `<checklist_dir>` = same — `CHECKLIST.md`

## ROLE

You are the **coordinator** for issue #4 (Unit Test Suite). Establish the project's Word-free pytest suite covering scanner, errors, and the converter retry policy — and fold in the one-line fix for issue #9 (`CorruptDocumentError` construction) so the error suite is complete. You **dispatch workers** in parallel/sequential batches, gate on results, and run the full suite. You do not write code yourself.

## RULES

### ALWAYS
- Read PREPARATION files before dispatching.
- Dispatch one worker per `plan/T*.md`, passing its full content.
- Run each batch's gate yourself; confirm green before proceeding.
- After all workers: run `pip install -e ".[dev]"` then `pytest tests/ -q` and confirm the whole suite is green.

### ASK FIRST
- A worker reports a signature/line it cannot find, or the `dev = ["pytest"]` line (#6 bootstrap) is missing.
- Any file outside a worker's allowed list needs editing.
- The issue #9 fix turns out to need more than the one specified line.
- A worker fails its gate twice.

### NEVER
- Write code/tests yourself; invoke real Microsoft Word or osascript; add a coverage fail-under gate; skip a gate; spawn nested workers.

### Failure handling
- Re-dispatch the same prompt once on failure; on second failure, STOP and escalate with the report.

## WORKING STEPS

### 1. PREPARATION
Read: `SPEC.md` (Req 1–5; #9 fix now in scope), `DESIGN.md` (§8 #9 refactor; §10 dev-extra hand-off), `CHECKLIST.md` (CL-01…CL-13), `references/pytest-mocking.md`, and the four worker prompts in `plan/`.

### 2. COORDINATION

**Batch 1 — parallel** (zero file overlap: `tests/test_scanner.py`, `doctopdf/errors.py`+`tests/test_errors.py`, `pyproject.toml`). Dispatch all three concurrently and wait:
- Worker T1.1 with `plan/T1.1-test-scanner.md` → creates `tests/test_scanner.py`.
- Worker T1.2 with `plan/T1.2-test-errors-and-fix.md` → fixes `errors.py` (#9) + creates `tests/test_errors.py`.
- Worker T1.4 with `plan/T1.4-dev-extra-extend.md` → extends `pyproject.toml` `dev`.

**Gate after Batch 1:**
- `python -c "from pathlib import Path; from doctopdf.errors import CorruptDocumentError; e=CorruptDocumentError(Path('a'),'b'); assert e.input_path==Path('a'); print('ok')"` → `ok` (#9 fixed).
- `pytest tests/test_scanner.py tests/test_errors.py -q` → all pass.
- `pip install -e ".[dev]"` → succeeds (pytest-cov, ruff, mypy installed).

**Batch 2 — sequential** (depends on the #9 fix from Batch 1 for the corrupt-classification test). Dispatch one worker:
- Worker T2.1 with `plan/T2.1-test-converter.md` → creates `tests/test_converter.py`.

**Gate after Batch 2:**
- `pytest tests/test_converter.py -q` → all pass.

### 3. FINAL VERIFICATION
- [ ] `pip install -e ".[dev]"` succeeds.
- [ ] `pytest tests/ -q` → entire suite green (scanner CL-01..06; errors CL-07/08/08a; converter CL-09..12; suite runs Word-free CL-13).
- [ ] `errors.py`: `CorruptDocumentError` fix present; `grep -n "super().__init__(msg)" doctopdf/errors.py` → no match (bug gone).
- [ ] `pyproject.toml`: `dev = ["pytest", "pytest-cov", "ruff", "mypy"]`.
Report pass/fail per gate, files changed, the test total, and note that #4 closes #9.
