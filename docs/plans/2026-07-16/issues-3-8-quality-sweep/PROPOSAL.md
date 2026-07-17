# Proposal: Quality Sweep — GitHub Issues #3–#8

- **Date**: 2026-07-16
- **Source**: Produced by the `discuss` skill through structured conversation
- **Project**: doctopdf — offline batch `.doc`/`.docx` → PDF converter using Microsoft Word on macOS

---

## 1. Scope

### In Scope

Five open GitHub issues, delivered as **five sequential batches, each its own PR merged to `main` in order**:

1. **#6 (bug)** — Stop silently swallowing exceptions in Word cleanup/quit/restart paths in `converter.py`; surface them via debug/warning logs so intermittent cleanup failures become diagnosable.
2. **#3 (refactor)** — Remove ~50 lines of near-duplicate `LogRecord` construction in `orchestrator.py` by extracting a single error-record helper.
3. **#4 (testing)** — Add the project's first test suite covering the scanner, custom errors, and the retry/converter logic (converter driven by mocks, so no real Word required).
4. **#7 (chore)** — Add GitHub Actions CI that lints and type-checks the codebase on every push/PR, plus the matching ruff/mypy configuration.
5. **#8 (docs)** — Move the long Automator Quick Action guide out of the README into its own doc, leaving a short summary + link behind.

**Cross-cutting decisions agreed in discussion:**

- **Python baseline = 3.11, standardized everywhere** — ruff/mypy target, CI runtime, and dev dependencies. This also **bumps `requires-python` to `>=3.11` and removes the 3.9/3.10 classifiers**, resolving the py39-vs-3.11 contradiction (note: drops the prior 3.9/3.10 support claim).
- **CI must be green from day one.** Any pre-existing lint/type violations in the current codebase are cleaned up as part of this effort (folded into the code-change batches), so the CI badge is trustworthy, not noise.
- **Sequence is fixed: #6 → #3 → #4 → #7 → #8.** The bugfix and refactor land *before* tests, so the test suite locks in already-correct, already-clean code; CI lands *after* tests so it has something real to run; docs are independent and come last.
- **Spec-phase resolutions:** (1) #6 includes a `--verbose`/`--debug` CLI flag + `logging.basicConfig` so the new diagnostics are observable; (2) CI (#7) runs the pytest suite in addition to ruff/mypy.

### Out of Scope (Explicitly Excluded)

- **#5 (demo GIF + file-access screenshot) is deferred.** Producing these assets requires a real macOS + Microsoft Word session and cannot be generated autonomously in the working environment. It will be revisited separately when the assets can be captured by hand.
- **No coverage gate.** `pytest-cov` is added to report coverage only; no fail-under threshold. A threshold can be introduced later, once coverage is broad enough to be meaningful.
- **No behavior changes** beyond the explicit bug fix in #6. The refactor (#3) must be behavior-preserving; tests (#4) assert existing behavior, they do not specify new behavior.
- **No changes to the actual PDF conversion logic, CLI surface, or supported document formats.**

---

## 2. User Scenarios

### Target Users

- **The maintainer (solo developer)** — benefits directly from cleaner code, a safety net of tests, and trustworthy CI.
- **Future contributors / first-time visitors** — benefit from a focused README, a green CI badge signalling the project is actively maintained, and tests that document expected behavior.

### Typical Flow

1. Maintainer opens a PR for batch #6; CI (once it exists in batch #7) and local checks pass; it merges to `main` and auto-closes issue #6.
2. Repeat in sequence for #3, #4, #7, #8 — each batch independently reviewable and mergeable, each closing its own issue.
3. By the end, pushing any change triggers CI; regressions in file discovery, error classification, or retry behavior are caught automatically instead of manually.

### Success Criteria

- Every except block in `_convert_single` builds its error record through one shared helper (no duplicated `LogRecord` construction remains).
- Suppressed cleanup exceptions are visible when running verbosely; a stalled Word relaunch emits a warning rather than failing silently.
- `pytest tests/` passes with the converter fully mocked (no Microsoft Word needed to run tests).
- CI runs ruff + mypy on every push to `main` and on every PR, and is **green** on its first run.
- README's Automator section is a short summary linking to `docs/automator.md`, which contains the full guide verbatim.
- Issues #3, #4, #6, #7, #8 are each closed by their respective batch's commit.

### Error Handling

- This is a maintainer-facing quality effort, so "errors" here are **build/CI/test failures**. Any failure blocks that batch's merge until resolved; later batches do not start until the prior one merges (sequential dependency).
- The one user-facing error-handling change is #6 itself: silent failures become logged failures (still non-fatal — cleanup remains best-effort).

---

## 3. Constraints

- **Environment**: Tests must run without Microsoft Word installed — satisfied by mocking the converter subprocess (#4). The deferred #5 is the only item requiring a real macOS + Word session.
- **Platform**: macOS-only project; the Python 3.11 baseline assumes current macOS users run 3.11+ (e.g., via Homebrew/pyenv). No stated need to support Python 3.9 or other platforms.
- **Timeline / budget**: None specified — self-paced maintainer effort.
- **Region / language**: None specified (English documentation).
- **Security / privacy**: No sensitive-data handling introduced. The tool already processes users' local documents; this effort changes no data flows.
- **Tooling**: ruff + mypy for lint/type-check, pytest + pytest-cov for tests; all pinned under a `dev` optional-dependency group.

---

## 4. Business Value

### Problem Statement

The codebase has accumulated duplication that is fragile to maintain (#3), silently swallows failures that make intermittent bugs un-diagnosable (#6), has no automated safety net to catch regressions (#4, #7), and buries the main use case under an advanced power-user guide (#8) — so this sweep makes the project cheaper to maintain, safer to change, and more inviting to new users and contributors.

---

## 5. Requirement Summary

- **Reliable failure visibility (#6):** Cleanup, quit, and restart of Microsoft Word must log (not silently swallow) failures, while remaining best-effort and non-fatal.
- **De-duplicated error reporting (#3):** Error log records must be built in one place so the codebase has a single point of truth for that structure.
- **Automated regression safety net (#4):** The project must ship a runnable, Word-free test suite covering file discovery, error classification/hierarchy, and retry behavior.
- **Trustworthy continuous integration (#7):** Every change must be automatically lint- and type-checked on a consistent Python 3.11 baseline, starting green.
- **Focused first impression (#8):** The README must lead with the common terminal workflow and defer the advanced Automator setup to a linked dedicated document.
- **Sequential, independently-shippable delivery:** The five changes must land in the fixed order #6 → #3 → #4 → #7 → #8, one PR each, so each safely builds on the last.

---

## 6. Open Questions

- None. All ambiguities (packaging, #5 scope, CI-cleanup scope, Python baseline, coverage gating) were resolved during discussion.
