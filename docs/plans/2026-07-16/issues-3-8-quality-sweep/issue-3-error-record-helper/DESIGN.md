# Design: Error Record Helper Refactor (#3)

- **Date**: 2026-07-16
- **Feature**: error-record-helper
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-3-error-record-helper/SPEC.md`

> **Purpose:** Pure, behavior-preserving refactor — consolidate the six duplicated `LogRecord(...)` constructions in `orchestrator._convert_single` into one private helper.

---

## 1. Research Summary

### 1.1 Technical Feasibility

| Requirement | Feasibility | Risk |
|---|---|---|
| Req 1 — all error outcomes via one helper | Feasible (pure refactor) | None |
| Req 2 — byte-identical `LogRecord` per branch | Feasible | Low — must preserve the catch-all's `Unexpected error:` prefix and per-branch `attempts` |

**Overall assessment**: ✅ All feasible. No external dependency; internal refactor only.

### 1.2 Existing Reference Implementations

`N/A` — no external pattern needed. The project already has `ConversionLogger.from_result` (`logger.py:152`), a factory that builds a `LogRecord` with an auto-timestamp; considered as an alternative (see Trade-offs) but not reused.

### 1.3 Tech Stack Compatibility

`N/A` — stdlib only (`time`, `dataclasses`); no dependency change.

---

## 2. Architecture Overview

### 2.1 Module List

| Module Key | Responsibility | Owned Artifacts |
|---|---|---|
| `doctopdf.orchestrator` | Batch coordination; gains a private error-record factory | new private method `Orchestrator._make_error_record` |

### 2.2 Boundaries

- **Entry points**: unchanged (`Orchestrator.run` → `_convert_files` → `_convert_single`).
- **Trust boundary**: `None` — no boundary change.

### 2.3 Target vs Baseline

| | Baseline | Target |
|---|---|---|
| Error handling in `_convert_single` | 6 inline `LogRecord(...)` blocks (~50 lines) | 6 one-liner calls to `_make_error_record(...)` |

---

## 3. Interaction Design

**None.** Change is confined to a single method within one module; no new cross-module coupling.

---

## 4. External Dependencies

**None** — stdlib only.

---

## 5. Data Persistence

**None** — `LogRecord` is an in-memory dataclass; no persistence change.

---

## 6. System Invariants

| Invariant | How Architecture Could Violate It | Symptoms of Violation |
|---|---|---|
| Error `LogRecord` output must be byte-identical before/after | Helper signature that drops/renames a field, or that formats the catch-all error differently | Log/CSV/JSON output drifts; downstream parsing breaks |
| Per-branch `attempts` must be preserved | Defaulting `attempts` everywhere | Timeout/Export records lose their `retry_count + 1` value |

---

## 7. Technical Trade-offs

| Decision | Rejected Alternatives | Lock-in Effect |
|---|---|---|
| Helper takes the **final error string** (`error: str`), not an `Exception` | Issue's literal suggestion `error: Exception` → `str(error)` — rejected because it **cannot** reproduce the catch-all's `f"Unexpected error: {e}"` prefix | Callers pass `str(e)` (or the prefixed string for the catch-all) |
| Dedicated `Orchestrator._make_error_record` (instance method, uses `self.converter.retry_count`) | Reuse `ConversionLogger.from_result` — rejected: it is status-generic, doesn't compute duration from `start`, and would mix two construction styles (success still inline) | One private method on `Orchestrator` |
| Keep success path unchanged | Also route success through a helper — rejected: out of issue #3 scope | Only error blocks refactored |

---

## 8. Design-Time Refactoring

| Finding | Affected Module | Tier | Disposition | Test Evidence |
|---|---|---|---|---|
| Duplicated `LogRecord` construction across 6 except blocks | `doctopdf/orchestrator.py` | T1 | **Refactored** (this change) | `tests/test_orchestrator_error_record.py` |

---

## 9. Architecture Diff

**N/A (justified).** Intra-method refactor within one module; no feature/container/component/module boundary change; atlas empty. No architectural boundary crossed.

---

## 10. Test Infrastructure Hand-off (sequencing note)

#3 is **position 2**, immediately after #6 — so the `tests/` directory and `pytest` dev extra already exist (bootstrapped by #6). #3 adds `tests/test_orchestrator_error_record.py` to verify behavior-equivalence. Note: #4 (position 3) covers scanner/errors/converter but **not** orchestrator, so #3 must self-verify.

---

## 11. References

- **Designed code file paths**: `doctopdf/orchestrator.py` (`_convert_single:228`, except blocks 255–317), `doctopdf/logger.py` (`LogRecord:21`, `from_result:152`), `tests/test_orchestrator_error_record.py` (to create)
- **Related documents**: `issue-3-error-record-helper/SPEC.md`, `PROPOSAL.md`
