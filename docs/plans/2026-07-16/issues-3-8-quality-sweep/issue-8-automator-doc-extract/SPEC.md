# Spec: Extract Automator Guide to Its Own Doc (#8)

- **Date**: 2026-07-16
- **Feature**: automator-doc-extract
- **Batch**: issues-3-8-quality-sweep — **sequence position 5 of 5** (order: #6 → #3 → #4 → #7 → #8)
- **Source issue**: GitHub #8 (documentation)

## Goal

Keep the README focused on the common terminal workflow by moving the long, advanced Automator Quick Action guide into its own document — preserving all content — so most readers reach Performance Notes and Troubleshooting faster.

## Scope

### In Scope

- Create `docs/automator.md` containing the current README "Automator Quick Action" section **verbatim** (full step-by-step, no edits to the instructions).
- Replace the README section with a concise summary (one or two lines stating what it does) plus a prominent link to `docs/automator.md`.
- Update any README table-of-contents entry or in-page cross-reference that points to the old Automator anchor so it still resolves.

### Out of Scope

- Rewriting or improving the Automator guide's content (verbatim move only).
- Removing the Automator capability from documentation (it stays fully documented, just relocated).
- Restructuring other README sections.

## Functional Behaviors (BDD)

### Requirement 1: The full guide lives in its own document
**GIVEN** the README currently contains the full "Automator Quick Action" section (~60 lines)
**WHEN** the content is moved
**THEN** `docs/automator.md` exists and contains that guide verbatim, with no steps lost and no instructional edits

**Uncertainty Level**: Known

### Requirement 2: The README retains a short pointer to the guide
**GIVEN** the README previously embedded the full section
**WHEN** it is replaced
**THEN** the README contains a brief "Automator Quick Action (Finder Right-Click)" summary stating that users can create a macOS Finder right-click service
**AND** a clearly visible link to `docs/automator.md`
**AND** the README no longer contains the full step-by-step setup

**Uncertainty Level**: Known

## Error and Edge Cases

- A README table of contents or cross-link referencing the old `#automator-…` anchor → repoint it to `docs/automator.md` (or remove it) so no broken in-page link remains.
- The `docs/` directory does not yet exist → it must be created.
- The moved content references image/screenshot paths that are relative to the README → those image links must remain valid after relocation (paths may need adjusting relative to `docs/`).

## Clarification Questions

- None. All requirements are Known.

## References

- **Key file paths** affected by this spec:
  - `README.md` — current "Automator Quick Action" section (to be summarised + linked)
  - `docs/automator.md` — to create
- Related project context files:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
