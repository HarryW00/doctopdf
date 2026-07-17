# issue-8-automator-doc-extract implementation plan

- `<spec_dir>` = `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-8-automator-doc-extract` — Context
- `<checklist_dir>` = same — `CHECKLIST.md`

## ROLE

You are the **coordinator** for issue #8 (Automator doc extract). Your job is to relocate the long Automator guide from the README into `docs/automator.md` (verbatim, no content loss) and leave a short summary + link — by **dispatching a worker** and verifying. Documentation-only; you do not edit the docs yourself.

## RULES

### ALWAYS
- Read PREPARATION files; dispatch the worker with its full prompt; run the verification gate.
- Confirm the move is **verbatim** (no steps dropped/edited) and image links still resolve.

### ASK FIRST
- The section boundary is ambiguous, or moving reveals broken cross-links/anchors the worker cannot safely resolve.
- Any file beyond `README.md` / `docs/automator.md` needs editing.
- Worker fails its gate twice.

### NEVER
- Edit docs yourself; rewrite or trim the guide content; delete the section without preserving it; skip the gate; spawn nested workers.

### Failure handling
- Re-dispatch the same prompt once; on second failure, STOP and escalate.

## WORKING STEPS

### 1. PREPARATION
Read: `SPEC.md` (Req 1–2), `DESIGN.md` (verbatim move; image-path invariant; `cli.py` epilog left as-is), `CHECKLIST.md` (CL-01…CL-04), `plan/T1.1-move-automator-guide.md`.

### 2. COORDINATION
**Batch 1 — single worker** (one cohesive doc edit across `README.md` + new `docs/automator.md`):
- Dispatch Worker T1.1 with prompt `plan/T1.1-move-automator-guide.md`.

**Gate after Batch 1:**
- `test -f docs/automator.md && echo ok` → `ok`.
- `grep -c "Full setup guide: docs/automator.md" README.md` → `1`.
- Manual: full step-by-step content present in `docs/automator.md`; README retains the short summary; no broken image links.

### 3. FINAL VERIFICATION
- [ ] `docs/automator.md` exists with the verbatim guide (CL-01).
- [ ] README has the short summary + link, no full step-by-step (CL-02/03).
- [ ] No broken image links / in-page anchors (CL-04).
Report pass/fail, files changed, and the moved line span.
