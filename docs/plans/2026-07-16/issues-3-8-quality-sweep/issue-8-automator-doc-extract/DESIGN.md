# Design: Extract Automator Guide to Its Own Doc (#8)

- **Date**: 2026-07-16
- **Feature**: automator-doc-extract
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-8-automator-doc-extract/SPEC.md`

> **Purpose:** Pure documentation restructure — relocate the long Automator Quick Action guide from README into `docs/automator.md`, leaving a short summary + link.

---

## 1. Research Summary

### 1.1 Technical Feasibility

| Requirement | Feasibility | Risk |
|---|---|---|
| Req 1 — verbatim move to `docs/automator.md` | Feasible | Low — must preserve any image links after the path change |
| Req 2 — README summary + link | Feasible | None |

**Overall assessment**: ✅ All feasible. Documentation-only; no code/dependency impact.

### 1.2 Existing Reference Implementations

`N/A` — no external pattern. Standard "extract long section to a sub-doc + link" doc pattern.

### 1.3 Tech Stack Compatibility

`N/A` — Markdown only.

---

## 2. Architecture Overview

### 2.1 Module List

| Module Key | Responsibility | Owned Artifacts |
|---|---|---|
| `README.md` | Project entry doc; retains a short Automator pointer | summary + link block |
| `docs/automator.md` | Full Automator Quick Action setup guide | the moved content |

### 2.2 Boundaries

- **Entry points**: `N/A` (documentation).
- **Trust boundary**: `None`.

### 2.3 Target vs Baseline

| | Baseline | Target |
|---|---|---|
| README | Full ~60-line Automator section (heading at `README.md:310`) | 2–3 line summary + link to `docs/automator.md` |
| `docs/automator.md` | does not exist | contains the guide verbatim |

---

## 3. Interaction Design

**None.** Documentation-only; no code coupling. The one cross-reference to watch: `cli.py` epilog (`cli.py:42`) currently says *"See README.md for Finder right-click integration"* — after the move that README line links onward, so the prose stays correct. (Optional polish: repoint it directly at `docs/automator.md` — see Trade-offs.)

---

## 4. External Dependencies

**None** — Markdown only.

---

## 5. Data Persistence

**None.**

---

## 6. System Invariants

| Invariant | How Architecture Could Violate It | Symptoms of Violation |
|---|---|---|
| No content loss | Editing instead of moving | Missing setup steps |
| Image links still resolve | Moving markdown without adjusting relative image paths | Broken images in `docs/automator.md` |
| No broken in-page links | Leaving a TOC/anchor pointing at the removed section | 404 anchor jumps in README |

---

## 7. Technical Trade-offs

| Decision | Rejected Alternatives | Lock-in Effect |
|---|---|---|
| Verbatim move; summary = 2–3 lines + link | (a) Trim/rewrite the guide — rejected (out of scope; risk of losing steps); (b) delete entirely — rejected (feature still documented) | Guide lives at `docs/automator.md` |
| Leave `cli.py` epilog as-is | Repoint to `docs/automator.md` — **deferred** as optional polish (the README still links onward, so nothing breaks) | No CLI change required for #8 |

---

## 8. Design-Time Refactoring

**None.** No code changed; documentation only.

---

## 9. Architecture Diff

**N/A (justified).** Documentation restructure; no product feature/container/component/module change; atlas empty.

---

## 10. References

- **Designed file paths**: `README.md` (Automator section, heading at `:310`), `docs/automator.md` (to create)
- **Related documents**: `issue-8-automator-doc-extract/SPEC.md`, `PROPOSAL.md`
