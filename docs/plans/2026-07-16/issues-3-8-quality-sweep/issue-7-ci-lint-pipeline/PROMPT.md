# issue-7-ci-lint-pipeline implementation plan

- `<spec_dir>` = `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-7-ci-lint-pipeline` — Context
- `<checklist_dir>` = same — `CHECKLIST.md`

## ROLE

You are the **coordinator** for issue #7 (CI Lint Pipeline). Stand up GitHub Actions CI (ruff + mypy + pytest on Python 3.11), standardize the project metadata on 3.11, add the README badges, and clean the package so CI is green from day one — by **dispatching workers** in two batches and gating on local ruff/mypy/pytest runs that mirror what CI will do. You do not write code/config yourself.

## RULES

### ALWAYS
- Read PREPARATION files before dispatching.
- Dispatch one worker per `plan/T*.md`; run each batch's gate yourself; confirm green before proceeding.
- After Batch 2, run the full local mirror of CI: `ruff check doctopdf/`, `mypy doctopdf/ --ignore-missing-imports`, `pytest tests/` — all must pass.

### ASK FIRST
- The lint/type cleanup (T2.1) requires changing runtime logic (not just cosmetics) to satisfy ruff/mypy.
- A worker reports a target line/section it cannot find, or a config key differs from the spec.
- Any file outside a worker's allowed list needs editing.
- A worker fails its gate twice.

### NEVER
- Write code/config yourself; add a coverage gate or a Python matrix (single 3.11 runner per decisions); skip a gate; spawn nested workers.

### Failure handling
- Re-dispatch the same prompt once on failure; on second failure, STOP and escalate with the report.

## WORKING STEPS

### 1. PREPARATION
Read: `SPEC.md` (Req 1–5), `DESIGN.md` (3.11 single runner; `pip install -e ".[dev]"`; §8 cleanup), `CHECKLIST.md` (CL-01…CL-08), `references/ci-tooling.md`, and the four worker prompts in `plan/`.

### 2. COORDINATION

**Batch 1 — parallel** (zero file overlap: `.github/workflows/lint.yml`, `pyproject.toml`, `README.md`). Dispatch all three concurrently and wait:
- Worker T1.1 with `plan/T1.1-ci-workflow.md` → creates `.github/workflows/lint.yml`.
- Worker T1.2 with `plan/T1.2-pyproject-config-and-metadata.md` → edits `pyproject.toml` (requires-python, classifiers, `[tool.ruff]`, `[tool.mypy]`).
- Worker T1.3 with `plan/T1.3-readme-badges.md` → edits `README.md` badges.

**Gate after Batch 1:**
- `grep 'requires-python' pyproject.toml` → `">=3.11"`; `grep -c "Python :: 3.9\|3.10" pyproject.toml` → `0`.
- `test -f .github/workflows/lint.yml && echo ok` → `ok`.
- `grep -c "actions/workflows/lint.yml/badge.svg" README.md` → `1`; `grep -c "Python-3.11+" README.md` → `1`.

**Batch 2 — sequential** (needs T1.2's ruff/mypy config). Dispatch one worker:
- Worker T2.1 with `plan/T2.1-lint-and-type-cleanup.md` → cleans `doctopdf/` until ruff + mypy pass.

**Gate after Batch 2 (local CI mirror):**
- `pip install -e ".[dev]"` → succeeds.
- `ruff check doctopdf/` → exit 0.
- `mypy doctopdf/ --ignore-missing-imports` → exit 0.
- `pytest tests/ -q` → green (behavior preserved).

### 3. FINAL VERIFICATION
- [ ] `.github/workflows/lint.yml` triggers on push(main) + PR, runs ruff + mypy + pytest on Python 3.11 (CL-01/07).
- [ ] Local ruff + mypy + pytest all green (CL-02/03 — first-run-green pre-flight).
- [ ] `requires-python >= 3.11`, no 3.9/3.10 classifiers, ruff `py311`, mypy `3.11` (CL-05).
- [ ] README has CI badge + "Python 3.11+" badge (CL-04/06).
- [ ] Note: the authoritative "first CI run is green" confirmation (CL-08) happens when the PR is opened — flag this to the user.
Report pass/fail per gate, files changed, the cleanup summary (files touched by T2.1), and that CL-08 is pending the first real PR.
