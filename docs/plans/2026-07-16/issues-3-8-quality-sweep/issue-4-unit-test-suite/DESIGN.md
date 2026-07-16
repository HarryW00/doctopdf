# Design: Unit Test Suite (#4)

- **Date**: 2026-07-16
- **Feature**: unit-test-suite
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-4-unit-test-suite/SPEC.md`

> **Purpose:** Establish a Word-free automated test suite covering scanner, errors, and the converter retry policy, plus the dev tooling to run it.

---

## 1. Research Summary

### 1.1 Technical Feasibility

| Requirement | Feasibility | Risk |
|---|---|---|
| Req 1 — scanner discovery tests | Feasible (`tmp_path` tree) | None |
| Req 2 — mapping + collision tests | Feasible | None |
| Req 3 — exception hierarchy tests | Feasible | None |
| Req 4 — retry policy tests (mocked) | Feasible (`monkeypatch subprocess.run` + `time.sleep`) | Low — must avoid real sleeps; patch `time.sleep` |
| Req 5 — Word-free, installable via `dev` extra | Feasible | None |

**Overall assessment**: ✅ All feasible. Stdlib + pytest only.

### 1.2 Existing Reference Implementations

| Source | Reusable Design Patterns |
|---|---|
| [pytest temporary dirs](https://docs.pytest.org/en/stable/how-to/tmp_path.html) | `tmp_path` fixture for building scanner test trees. |
| [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) | Patch `subprocess.run`/`time.sleep` to drive `convert`/`convert_with_retry` without osascript/Word. |
| [pytest parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) | Parametrize the terminal-vs-retriable error matrix. |

### 1.3 Tech Stack Compatibility

| Candidate | Compatibility | License | Decision |
|---|---|---|---|
| pytest | New dev dep | MIT | ✅ Already bootstrapped by #6; #4 keeps it |
| pytest-cov | New dev dep | MIT | ✅ Add (report only — no gate) |
| ruff, mypy | New dev dep | MIT + MIT | ✅ Add (lint/type; CI enforced by #7) |

---

## 2. Architecture Overview

### 2.1 Module List

| Module Key | Responsibility | Owned Artifacts |
|---|---|---|
| `tests/test_scanner.py` | Discovery, filtering, mapping, collision | — |
| `tests/test_errors.py` | Messages + hierarchy | — |
| `tests/test_converter.py` | `convert` classification + `convert_with_retry` retry policy (mocked) | — |

### 2.2 Boundaries

- **Entry points**: tests import `doctopdf.scanner`, `doctopdf.errors`, `doctopdf.converter`.
- **Trust boundary**: `None` — test-only; no real Word.

### 2.3 Target vs Baseline

| | Baseline | Target |
|---|---|---|
| Test coverage | none | scanner, errors, converter-retry (mocked) |
| Dev tooling | `dev = ["pytest"]` (from #6) | `dev = ["pytest", "pytest-cov", "ruff", "mypy"]` |

---

## 3. Interaction Design

**None (new).** Tests call existing public functions; no new product coupling. Mocking surface: `doctopdf.converter.subprocess.run`, `doctopdf.converter.time.sleep`.

---

## 4. External Dependencies

### 4.1 Dependency Overview

| Dependency | Purpose | Official Documentation |
|---|---|---|
| pytest | Test runner | https://docs.pytest.org/ |
| pytest-cov | Coverage reporting (no gate) | https://pytest-cov.readthedocs.io/ |

Detailed mocking patterns in `references/pytest-mocking.md`.

---

## 5. Data Persistence

**None** — tests use `tmp_path` (auto-cleaned); no persisted state.

---

## 6. System Invariants

| Invariant | How Architecture Could Violate It | Symptoms of Violation |
|---|---|---|
| Tests run without Microsoft Word | Calling real `subprocess.run`/osascript | Tests hang/fail on non-macOS or without Word |
| Tests are deterministic & fast | Leaving real `time.sleep` in retry tests | Slow/flaky suite |

---

## 7. Technical Trade-offs

| Decision | Rejected Alternatives | Lock-in Effect |
|---|---|---|
| Mock at `subprocess.run` boundary (craft JSON stdout) | Mock the whole `convert` method — rejected: loses coverage of error classification inside `convert` | Tests exercise real classification logic |
| Patch `time.sleep` to a no-op | Real sleeps — rejected (slow) | Fast retry tests |
| Coverage reported, not gated | Add fail-under threshold — rejected (Q5=A; converter mocked → brittle early threshold) | No gate; revisit later |

---

## 8. Design-Time Refactoring

| Finding | Affected Module | Tier | Disposition | Test Evidence |
|---|---|---|---|---|
| `CorruptDocumentError(...)` crashes at construction with `AttributeError` (issue #9) | `doctopdf/errors.py` | T1 | **Refactored** (this change) — call `DocToPDFError.__init__(self, msg, input_path)` instead of `super().__init__(msg)` | `tests/test_errors.py` constructs it and asserts `input_path` |

All other production code is unchanged by #4; pre-existing lint/type cleanup belongs to #7.

---

## 9. Architecture Diff

**N/A (justified).** Tests don't change product architecture; atlas empty.

---

## 10. Test Infrastructure Hand-off (sequencing note)

#4 is **position 3**. It **extends** the `dev` extra and `tests/` dir bootstrapped by #6 (and joined by #3's orchestrator test). #4 adds `pytest-cov`, `ruff`, `mypy` to `dev` and the scanner/errors/converter suites. #7 (position 4) then consumes this `dev` extra in CI.

---

## 11. References

- **Designed code file paths**: `doctopdf/scanner.py`, `doctopdf/errors.py`, `doctopdf/converter.py`, `tests/test_scanner.py` / `tests/test_errors.py` / `tests/test_converter.py` (to create), `pyproject.toml` (extend `dev`)
- **Reference docs**: `references/pytest-mocking.md`
- **Related documents**: `issue-4-unit-test-suite/SPEC.md`, `PROPOSAL.md`
