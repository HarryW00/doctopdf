# Checklist: CI Lint Pipeline (#7)

- **Date**: 2026-07-16
- **Feature**: ci-lint-pipeline
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-7-ci-lint-pipeline/SPEC.md`

> **Purpose:** Verify CI triggers, is green from day one, runs lint+type+test on a consistent 3.11 baseline, and shows a badge.

---

## Behavior-to-Test Checklist

| ID | Observable Behavior | SPEC Requirement | Corresponding Check | Result |
|---|---|---|---|---|
| CL-01 | Workflow triggers on push to `main` and on PRs | Req 1 | YAML inspection: `on: {push: {branches: [main]}, pull_request:}` | `[pending]` |
| CL-02 | `ruff check doctopdf/` exits 0 on current code | Req 2 | Local `ruff check doctopdf/` → 0 | `[pending]` |
| CL-03 | `mypy doctopdf/ --ignore-missing-imports` exits 0 | Req 2 | Local `mypy doctopdf/ --ignore-missing-imports` → 0 | `[pending]` |
| CL-04 | README has a CI badge beneath existing badges | Req 3 | `grep` badge markdown referencing `lint.yml` | `[pending]` |
| CL-05 | `requires-python = ">=3.11"`; no 3.9/3.10 classifiers; ruff `py311`; mypy `3.11` | Req 4 | `grep`/read `pyproject.toml` | `[pending]` |
| CL-06 | "Python 3.9+" README badge updated to "3.11+" | Req 4 | `grep` README badge line | `[pending]` |
| CL-07 | Workflow runs `pytest tests/` (install via `.[dev]`) | Req 5 | YAML inspection + local `pytest tests/` → 0 | `[pending]` |
| CL-08 | First real CI run on a PR is green | Req 2 | Open PR → Actions tab → green | `[pending]` |

---

## Hardening Checklist

- [x] Regression guard — CI fails on any new lint/type/test regression (intended).
- [ ] Property-based / adversarial — `N/A` (CI config).
- [x] Pre-existing violations cleaned so first run is green (CL-02/03 local pre-flight).
- All other hardening items — `N/A`.

---

## E2E / Integration Decisions

| Flow / Risk | Test Level | Rationale |
|---|---|---|
| Workflow correctness | Config inspection + local pre-flight (`ruff`/`mypy`/`pytest` all green) | Full CI verification = first real PR run |
| Python-3.11 consistency | Static `grep` of pyproject | Mechanical check |

---

## References

- **Designed file paths**: `.github/workflows/lint.yml`, `pyproject.toml`, `README.md`
- **Reference docs**: `references/ci-tooling.md`
- **Related documents**: `issue-7-ci-lint-pipeline/SPEC.md`, `issue-7-ci-lint-pipeline/DESIGN.md`
