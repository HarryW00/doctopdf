# Spec: Converter Exception Logging (#6)

- **Date**: 2026-07-16
- **Feature**: converter-exception-logging
- **Batch**: issues-3-8-quality-sweep — **sequence position 1 of 5** (order: #6 → #3 → #4 → #7 → #8)
- **Source issue**: GitHub #6 (bug)

## Goal

Surface previously-silent Microsoft Word cleanup / quit / restart failures so intermittent best-effort failures become diagnosable, **without** changing the non-fatal best-effort behaviour of those paths.

## Scope

### In Scope

- Add a module-level stdlib logger to `converter.py`.
- Replace the silent `except Exception: pass` in `_cleanup_stale_word`, `quit_word`, `_force_quit_word`, and `_is_word_running` with debug-level logging that identifies the failing operation.
- Emit a **warning** when `restart_word` cannot relaunch Word within its polling window (currently returns silently).
- Add a `--verbose`/`--debug` flag to the CLI (`cli.py`) that enables debug-level logging via `logging.basicConfig(level=DEBUG)`, making the new diagnostics observable — **warnings visible by default, debug on demand** (spec-phase decision, see Resolved question).

### Out of Scope

- Changing best-effort semantics: cleanup/quit/restart must continue to **never raise** into the conversion flow.
- Routing these internal diagnostics through the user-facing `ConversionLogger` (they are operational, not per-file results).
- Adding retry logic to the cleanup helpers.
- Changing the restart polling duration or the `_force_quit_word` pkill strategy.

## Functional Behaviors (BDD)

### Requirement 1: Cleanup failures are logged, not silently swallowed
**GIVEN** `_cleanup_stale_word` invokes its cleanup `osascript` and the call raises an exception (e.g. `TimeoutExpired`, `FileNotFoundError`)
**WHEN** the exception is caught
**THEN** the exception is recorded at **debug** level via stdlib logging, with a message identifying it as stale-Word cleanup and marking it non-critical
**AND** no exception propagates (the method remains best-effort and returns normally)

**Uncertainty Level**: Known

### Requirement 2: Graceful-quit failure is logged before the force-quit fallback
**GIVEN** `quit_word`'s graceful `osascript` quit raises an exception
**WHEN** the exception is caught
**THEN** a **debug**-level message is logged noting that graceful quit failed and a force-quit will be attempted
**AND** `_force_quit_word()` still runs afterward exactly as today

**Uncertainty Level**: Known

### Requirement 3: Stalled Word relaunch emits a warning
**GIVEN** `restart_word` force-quits Word and polls `check_word_installed` waiting for relaunch
**WHEN** Word does not become responsive within the polling window (~30s)
**THEN** a **warning**-level message is logged stating that Word did not relaunch and the next conversion may fail
**AND** `restart_word` returns without raising

**Uncertainty Level**: Known

### Requirement 4: Diagnostics are observable via a `--verbose` flag
**GIVEN** a `--verbose`/`--debug` CLI flag exists and configures stdlib logging via `logging.basicConfig`
**WHEN** a user runs the tool normally versus with `--verbose`
**THEN** debug diagnostics are suppressed by default and visible only when the flag is passed
**AND** warning-level messages (e.g. stalled Word relaunch) are surfaced by default

**Uncertainty Level**: Known

## Error and Edge Cases

- `subprocess.TimeoutExpired` inside cleanup (osascript hangs) → logged debug, non-fatal.
- `FileNotFoundError` (osascript/pkill absent on a non-macOS host) → logged debug, non-fatal.
- A logging call itself misbehaves (e.g. a bad handler) → must **not** break the conversion; logging must never raise into the caller.
- `restart_word` invoked when Word was never installed → polling exhausts, warning logged, no crash.
- Warnings emitted mid-batch must not corrupt the per-file `✓/✗` status lines produced by `ConversionLogger`.
- `logging.basicConfig` must not capture/reformat the existing `ConversionLogger` stdout status lines (keep the two output channels independent).

## Clarification Questions

### Resolved: Diagnostic observability (decided during spec)
- **Decision**: Accept option **B** — add a minimal `--verbose`/`--debug` flag in `cli.py` that calls `logging.basicConfig(level=DEBUG)`, so the new debug/warning logs are actually observable (warnings visible by default, debug on demand). Folded into Requirement 4 and the In Scope list above.

## References

- **Key code file paths** affected by this spec:
  - `doctopdf/converter.py` — `_cleanup_stale_word:332`, `quit_word:360`, `_force_quit_word:389`, `restart_word:401`, `_is_word_running:434`
  - `doctopdf/cli.py` — entry point for the new `--verbose`/`--debug` flag and `logging.basicConfig` (no logging config exists today)
- Related project context files:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
