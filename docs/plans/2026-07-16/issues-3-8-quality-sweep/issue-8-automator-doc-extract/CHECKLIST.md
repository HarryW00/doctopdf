# Checklist: Extract Automator Guide to Its Own Doc (#8)

- **Date**: 2026-07-16
- **Feature**: automator-doc-extract
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-8-automator-doc-extract/SPEC.md`

> **Purpose:** Documentation-only change. No automated test coverage required (per spec skill: documentation changes are exempt from mandatory test coverage). Verification is structural/manual.

---

## Behavior-to-Test Checklist

| ID | Observable Behavior | SPEC Requirement | Corresponding Check | Result |
|---|---|---|---|---|
| CL-01 | `docs/automator.md` exists and contains the full Automator guide verbatim | Req 1 | Manual diff: content matches the removed README block | `[pending]` |
| CL-02 | README contains a short "Automator Quick Action (Finder Right-Click)" summary + a link to `docs/automator.md` | Req 2 | Manual / `grep` for the link | `[pending]` |
| CL-03 | README no longer contains the full step-by-step setup | Req 2 | Manual | `[pending]` |
| CL-04 | No broken image links / in-page anchors | Invariant | Optional link-check script; manual render review | `[pending]` |

---

## Hardening Checklist

- [x] Regression tests — `N/A` (documentation); structural checks above suffice.
- All other hardening items — `N/A` (no logic, no external services, no auth/concurrency).

---

## E2E / Integration Decisions

| Flow / Risk | Test Level | Rationale |
|---|---|---|
| Doc structure correctness | Manual / optional `grep`-based check | Markdown content; no runtime behavior to exercise. |

---

## References

- **Designed file paths**: `README.md`, `docs/automator.md`
- **Related documents**: `issue-8-automator-doc-extract/SPEC.md`, `issue-8-automator-doc-extract/DESIGN.md`
