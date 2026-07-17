# Design: CI Lint Pipeline (#7)

- **Date**: 2026-07-16
- **Feature**: ci-lint-pipeline
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-7-ci-lint-pipeline/SPEC.md`

> **Purpose:** Automated ruff + mypy + pytest on every push/PR, standardized on Python 3.11, green from day one.

---

## 1. Research Summary

### 1.1 Technical Feasibility

| Requirement | Feasibility | Risk |
|---|---|---|
| Req 1 — workflow triggers | Feasible (GHA `on:`) | None |
| Req 2 — ruff + mypy green | Feasible | Low — pre-existing violations must be cleaned first |
| Req 3 — CI badge | Feasible | None |
| Req 4 — 3.11 baseline consistent | Feasible | Low — `requires-python` bump + classifier removal |
| Req 5 — pytest in CI | Feasible | None (suite from #4 is Word-free) |

**Overall assessment**: ✅ All feasible. Standard tooling.

### 1.2 Existing Reference Implementations

| Source | Reusable config |
|---|---|
| [Configuring Ruff — Astral](https://docs.astral.sh/ruff/configuration/) | `[tool.ruff]` `line-length`, `target-version` |
| [Ruff settings](https://docs.astral.sh/ruff/settings/) | `target-version = "py311"` for Python ≥3.11 |
| [mypy config file](https://mypy.readthedocs.io/en/stable/config_file.html) | `[tool.mypy]` `python_version`, `ignore_missing_imports` |
| [actions/setup-python](https://github.com/marketplace/actions/setup-python) | `python-version: "3.11"` |

### 1.3 Tech Stack Compatibility

| Candidate | Compatibility | License | Decision |
|---|---|---|---|
| ruff | New (dev/CI) | MIT | ✅ |
| mypy | New (dev/CI) | MIT | ✅ |
| actions/setup-python@v5 | GHA | Apache-2.0 | ✅ |

---

## 2. Architecture Overview

### 2.1 Module List

| Module Key | Responsibility | Owned Artifacts |
|---|---|---|
| `.github/workflows/lint.yml` | Lint + type-check + test on push/PR | workflow YAML |
| `pyproject.toml` (tool config) | ruff/mypy settings; Python metadata | `[tool.ruff]`, `[tool.mypy]`, `requires-python`, classifiers |
| `README.md` (badges) | CI badge + updated Python badge | badge lines |

### 2.2 Boundaries

- **Entry points**: GitHub push/PR event → workflow.
- **Trust boundary**: `None` (CI runs untrusted code in a sandboxed runner; standard GHA trust model).

### 2.3 Target vs Baseline

| | Baseline | Target |
|---|---|---|
| CI | none | ruff + mypy + pytest on push(main)+PR, Python 3.11 |
| Python metadata | `requires-python >= 3.9`, classifiers 3.9–3.12 | `requires-python >= 3.11`, classifiers 3.11–3.12 |
| README badges | "Python 3.9+" badge | "Python 3.11+" badge + CI badge |

---

## 3. Interaction Design

**None (product).** CI is infrastructure; no new product-module coupling. CI consumes the `[dev]` extra (from #4) via `pip install -e ".[dev]"`.

---

## 4. External Dependencies

### 4.1 Dependency Overview

| Dependency | Purpose | Documentation |
|---|---|---|
| ruff | Linter/formatter | https://docs.astral.sh/ruff/ |
| mypy | Static type checker | https://mypy.readthedocs.io/ |
| actions/setup-python@v5 | Install Python on runner | https://github.com/marketplace/actions/setup-python |

Config snippets in `references/ci-tooling.md`.

### 4.2 ruff / mypy

#### Limits and Failure Modes

| Category | Fact | Coding Obligation |
|---|---|---|
| mypy missing stubs | Third-party libs may lack stubs | `ignore_missing_imports = true` (CI must not fail on this) |
| Pre-existing violations | Current code may not be clean | Fix all before merge so first CI run is green |

---

## 5. Data Persistence

**None.**

---

## 6. System Invariants

| Invariant | How Architecture Could Violate It | Symptoms of Violation |
|---|---|---|
| CI is green from day one | Landing CI before cleaning violations | Red badge on first run → trust erodes |
| Single Python baseline | ruff target ≠ mypy version ≠ CI runner ≠ `requires-python` | Contradictory support claims |
| CI covers lint + types + tests | Omitting pytest step | Regressions slip through |

---

## 7. Technical Trade-offs

| Decision | Rejected Alternatives | Lock-in Effect |
|---|---|---|
| `ruff check` + `mypy` + `pytest` only | Add `ruff format --check` — **deferred** (keeps #7 to agreed scope; one-line future add) | Matches issue #7 + the agreed test-in-CI decision |
| Single Python 3.11 runner (no matrix) | Matrix 3.9+3.11 — rejected (decision dropped 3.9 support) | One version |
| Install via `pip install -e ".[dev]"` | `pip install ruff mypy` separately — rejected (duplicated; dev extra already has them from #4) | One install step |
| Bump `requires-python` to `>=3.11` | Keep `>=3.9` — rejected (decision CQ2=A) | Drops 3.9/3.10 support claim |

---

## 8. Design-Time Refactoring

| Finding | Affected Module | Tier | Disposition | Test Evidence |
|---|---|---|---|---|
| Pre-existing ruff/mypy violations in `doctopdf/` (TBD on first run) | `doctopdf/*` | T1 | **Refactored** (this change) — fix until `ruff check` + `mypy` exit 0 | CI green + local `ruff`/`mypy` clean |

---

## 9. Architecture Diff

**N/A (justified).** CI infrastructure + metadata; no product feature/container/component/module change; atlas empty.

---

## 10. Test Infrastructure Hand-off (sequencing note)

#7 is **position 4**, after #4 — so the `[dev]` extra (with pytest/pytest-cov/ruff/mypy) and the `tests/` suite already exist. #7 adds the workflow, the ruff/mypy pyproject config, the Python-3.11 metadata change, and the README badges. The lint job installs via `pip install -e ".[dev]"` and runs `ruff check doctopdf/`, `mypy doctopdf/ --ignore-missing-imports`, and `pytest tests/`.

---

## 11. References

- **Designed file paths**: `.github/workflows/lint.yml` (to create), `pyproject.toml`, `README.md`
- **Reference docs**: `references/ci-tooling.md`
- **Related documents**: `issue-7-ci-lint-pipeline/SPEC.md`, `issue-4-unit-test-suite/SPEC.md` (suite CI runs), `PROPOSAL.md`
