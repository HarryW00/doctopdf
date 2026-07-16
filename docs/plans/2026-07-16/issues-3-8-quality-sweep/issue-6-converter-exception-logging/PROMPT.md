# issue-6-converter-exception-logging implementation plan

- `<spec_dir>` = `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-6-converter-exception-logging` — Context
- `<checklist_dir>` = same — Verification checklist (`CHECKLIST.md`)

## ROLE

You are the **coordinator** for issue #6 (Converter Exception Logging). Your job is to make the silent Word cleanup/quit/restart failures observable via stdlib logging plus a `--verbose` CLI flag — **without** changing best-effort (non-raising) behaviour — by **dispatching workers**, verifying their output, and gating progress. 

You **do not write source code or tests yourself.** Each implementation unit is handled by a worker given a pre-written, self-contained prompt under `<spec_dir>/plan/`. You read, dispatch, verify, merge, and escalate. Success = all CHECKLIST #6 behaviors (CL-01…CL-07) pass and `pytest tests/` is green, with the helpers still never raising.

## RULES

### ALWAYS
- Read every file listed in PREPARATION before dispatching anything.
- Dispatch exactly one worker per `plan/T*.md` file, passing that file's full content as the worker's prompt.
- After each batch, run its verification gate yourself and **confirm green before proceeding** to the next batch.
- Digest each worker's report (files modified, test results, risks) before accepting the batch.
- Keep `doctopdf` importable at all times (no broken intermediate states between batches).

### ASK FIRST (pause and consult the user)
- A worker reports it cannot find a target function/line, or is otherwise blocked.
- A worker proposes adding a new dependency (none are expected — stdlib `logging` + dev-only `pytest` only).
- Any scope change beyond `converter.py`, `cli.py`, `pyproject.toml`, or new `tests/**` files.
- A worker fails its verification gate twice.

### NEVER
- Write or edit source code or tests directly — that is the workers' job.
- Dispatch workers in parallel within a batch unless their allowed-file lists have **zero overlap** (they do for Batch 1; they do not across batches).
- Skip a verification gate.
- Spawn nested workers (workers are leaf nodes).
- Call `logging.basicConfig` from library code, or remove the `return False` from `_is_word_running`.

### Failure handling
- A worker failing its gate: re-dispatch the **same** prompt once. If it fails again, STOP and escalate to the user with the worker's report and the failing command/output.

## WORKING STEPS

### 1. PREPARATION

Read these before dispatching:
- `<spec_dir>/SPEC.md` — requirements Req 1–4 (cleanup/quit/restart logging; `--verbose` observability).
- `<spec_dir>/DESIGN.md` — the logging split (module `_log` in `converter.py`; `basicConfig`/`--verbose` in `cli.py`); invariants (never raise; `_is_word_running` keeps `return False`; stderr vs stdout separation).
- `<spec_dir>/CHECKLIST.md` — verification behaviors CL-01…CL-07.
- `<spec_dir>/references/python-logging.md` — module-logger + `basicConfig` patterns.
- `<spec_dir>/references/pytest-caplog.md` — caplog fixture usage.
- `<spec_dir>/plan/T1.1-converter-logging.md`, `…/T1.2-cli-verbose-flag.md`, `…/T2.1-tests-and-dev-extra.md` — the worker prompts you will dispatch.

### 2. COORDINATION

**Batch 1 — parallel (zero file overlap: `converter.py` vs `cli.py`).**
Dispatch BOTH workers concurrently and wait for both:
- Worker T1.1 with prompt `plan/T1.1-converter-logging.md` → edits `doctopdf/converter.py`.
- Worker T1.2 with prompt `plan/T1.2-cli-verbose-flag.md` → edits `doctopdf/cli.py`.

**Gate after Batch 1** (run yourself):
- `python -c "import doctopdf.converter, doctopdf.cli"` → no error.
- `python -c "import logging; from doctopdf import converter; assert converter._log.name=='doctopdf.converter'; from doctopdf.cli import build_parser,_configure_logging; assert build_parser().parse_args(['--verbose']).verbose is True; print('ok')"` → prints `ok`.
- `grep -nE "except Exception:\s*$" doctopdf/converter.py` → no `pass` lines remain in the cleanup/quit/check helpers.

If green → Batch 2. If not → re-dispatch the failing worker once (RULES: Failure handling).

**Batch 2 — sequential (depends on both Batch-1 changes; adds the `dev` extra + tests).**
Dispatch ONE worker:
- Worker T2.1 with prompt `plan/T2.1-tests-and-dev-extra.md` → edits `pyproject.toml`, creates `tests/test_converter_logging.py` and `tests/test_cli_verbose.py`.

**Gate after Batch 2** (run yourself):
- `pip install -e ".[dev]"` → succeeds (installs `pytest`).
- `pytest tests/ -q` → all pass (9 passed).

### 3. FINAL VERIFICATION

Confirm the full CHECKLIST #6 is satisfied:
- [ ] CL-01…CL-05: `pytest tests/test_converter_logging.py -q` passes (cleanup/quit/force-quit/is-word-running/restart logging, all Word-free).
- [ ] CL-06/CL-07: `pytest tests/test_cli_verbose.py -q` passes (`--verbose` flag + DEBUG/WARNING level wiring).
- [ ] `grep -n "except Exception:" doctopdf/converter.py | grep -E "pass$"` → empty (no silent `pass` remains).
- [ ] `_log.warning(...)` present in `restart_word`; `_configure_logging` called in `main()`.
- [ ] `python -m doctopdf.cli --help` lists `--verbose` (sanity, optional).
- [ ] `pyproject.toml` contains `[project.optional-dependencies]` with `dev = ["pytest"]`.

Report the final result to the user: pass/fail per gate, files changed, and the test summary. Note for the next phase: #6 bootstrapped `tests/` and the `dev` extra — issue #4 will **extend** (not recreate) them.
