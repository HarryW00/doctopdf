# Spec: CI Lint Pipeline (#7)

- **Date**: 2026-07-16
- **Feature**: ci-lint-pipeline
- **Batch**: issues-3-8-quality-sweep — **sequence position 4 of 5** (order: #6 → #3 → #4 → #7 → #8)
- **Source issue**: GitHub #7 (chore / enhancement)

## Goal

Automatically lint, type-check, **and test** every change so style drift, simple errors, and regressions are caught at PR time, with a trustworthy **green** badge from the very first run.

## Scope

### In Scope

- `.github/workflows/lint.yml` that triggers on push to `main` and on pull requests.
- Install ruff + mypy on a **Python 3.11** runner and run `ruff check doctopdf/` and `mypy doctopdf/ --ignore-missing-imports`.
- **Run the test suite** in CI: install the package with the `[dev]` extra and run `pytest tests/` (the Word-free suite from #4) — spec-phase decision.
- Add `[tool.ruff]` (`target-version = py311`, line-length 100) and `[tool.mypy]` (`python_version = "3.11"`, `ignore_missing_imports`) configuration to `pyproject.toml`.
- **Standardize the project on Python 3.11**: bump `requires-python` to `>=3.11` and remove the 3.9/3.10 classifiers — spec-phase decision (note: drops the prior 3.9/3.10 support claim).
- Add a CI badge to the README beneath the existing badges.
- Clean up any pre-existing ruff/mypy violations so CI is green on day one (agreed decision).

### Out of Scope

- A coverage gate (coverage reported by #4 only; not enforced).
- Pre-commit hooks (separate effort).
- Multi-OS CI runners (the project is macOS-only; lint/type/test on Ubuntu runners is sufficient).
- A multi-version Python matrix (baseline is a single version: 3.11).
- Releasing/publishing automation.

## Functional Behaviors (BDD)

### Requirement 1: CI triggers on every push and pull request
**GIVEN** the workflow file exists in `.github/workflows/`
**WHEN** a commit is pushed to `main` or a pull request is opened or updated
**THEN** the workflow runs on a GitHub-hosted runner

**Uncertainty Level**: Known

### Requirement 2: CI enforces ruff and mypy, green from day one
**GIVEN** the workflow installs ruff and mypy on Python 3.11 and `pyproject.toml` configures them (`ruff` line-length 100, `target-version = py311`; `mypy` `ignore_missing_imports`, `python_version = "3.11"`)
**WHEN** `ruff check doctopdf/` and `mypy doctopdf/ --ignore-missing-imports` execute against the current codebase
**THEN** both exit 0 (pre-existing violations cleaned up as part of this batch)
**AND** the job is green on its first run

**Uncertainty Level**: Known

### Requirement 3: README displays a CI badge linked to the workflow
**GIVEN** the README already has a row of badges
**WHEN** the CI badge markdown is added
**THEN** it references the `lint.yml` workflow and renders directly beneath the existing badges

**Uncertainty Level**: Known

### Requirement 4: The Python baseline is consistent project-wide at 3.11
**GIVEN** `pyproject.toml`'s `requires-python`/classifiers, ruff `target-version`, mypy `python_version`, and the CI runner version
**WHEN** a contributor inspects the project configuration
**THEN** all agree on Python 3.11 — `requires-python` bumped to `>=3.11`, the 3.9/3.10 classifiers removed, ruff `target-version = py311`, mypy `python_version = "3.11"`, CI on a 3.11 runner

**Uncertainty Level**: Known

### Requirement 5: CI runs the test suite
**GIVEN** the workflow installs the package with the `[dev]` extra (pytest available from #4)
**WHEN** the workflow runs `pytest tests/`
**THEN** the Word-free suite executes and must pass on every push and PR

**Uncertainty Level**: Known

## Error and Edge Cases

- New code introduces a lint violation → CI fails and blocks merge (intended).
- `mypy` reports missing third-party stubs → ignored via `ignore_missing_imports`; must not fail CI.
- A PR opened from a fork → workflow still triggers on `pull_request`.
- The badge SVG is briefly stale after a run → acceptable; GitHub refreshes it on the next run.
- A pre-existing violation is discovered when CI first runs → fixed within this batch so the first run is green (per Requirement 2).
- A test fails in CI → the job fails red (intended); the badge reflects the real state.

## Clarification Questions

### Resolved: Python baseline (decided during spec)
- **Decision**: Accept option **A** — standardize on Python 3.11 everywhere: bump `requires-python` to `>=3.11`, remove the 3.9/3.10 classifiers, set ruff `target-version = py311` and mypy `python_version = "3.11"`, CI on a single 3.11 runner. This drops the project's previous 3.9/3.10 support claim. Captured in Requirement 4.

### Resolved: CI scope (decided during spec)
- **Decision**: Accept option **B** — CI runs the pytest suite (installing the `[dev]` extra) in addition to ruff and mypy. Captured in Requirement 5.

## References

- **Key code file paths / artifacts** affected by this spec:
  - `.github/workflows/lint.yml` — to create (ruff + mypy + pytest)
  - `pyproject.toml` — current `requires-python = ">=3.9"` and classifiers 3.9–3.12 (to bump to `>=3.11`, drop 3.9/3.10); `[tool.ruff]` / `[tool.mypy]` to add; `[project.optional-dependencies] dev` added by #4
  - `README.md` — existing badges row (CI badge to be added beneath)
- Related project context files:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-4-unit-test-suite/SPEC.md` (the suite CI runs)
