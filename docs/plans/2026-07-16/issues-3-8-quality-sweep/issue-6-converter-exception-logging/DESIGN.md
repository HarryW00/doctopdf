# Design: Converter Exception Logging (#6)

- **Date**: 2026-07-16
- **Feature**: converter-exception-logging
- **Source SPEC**: `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-6-converter-exception-logging/SPEC.md`

> **Purpose:** Technical design for surfacing silent Word cleanup/quit/restart failures via stdlib logging plus a CLI `--verbose` flag, without changing best-effort (non-fatal) behaviour.

---

## 1. Research Summary

### 1.1 Technical Feasibility

| Requirement | Feasibility | Risk |
|---|---|---|
| Req 1 — cleanup failures logged at debug | Feasible (stdlib `logging`) | None |
| Req 2 — graceful-quit failure logged before force-quit | Feasible | None |
| Req 3 — stalled relaunch logged at warning | Feasible | None |
| Req 4 — diagnostics observable via `--verbose` | Feasible (argparse flag + `basicConfig`) | Low — `-v` is already taken by `--version`; must use a long-only flag |

**Overall assessment**: ✅ All feasible. No new external dependencies; the change uses only the Python standard library (`logging`, `argparse`).

### 1.2 Existing Reference Implementations

| Source | Reusable Design Patterns |
|---|---|
| [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html) | Libraries use `logger = logging.getLogger(__name__)` per module and **do not** call `basicConfig`; the application configures the root logger once at startup. This maps exactly onto our split: `converter.py` owns a module logger; `cli.py` configures logging. |
| [Stack Overflow — logging best practice](https://stackoverflow.com/questions/22807972/python-best-practice-in-terms-of-logging) | Confirms `getLogger(__name__)` per module + single `basicConfig`/`dictConfig` at the app entry point as the canonical pattern. |
| [pytest logging docs](https://docs.pytest.org/en/stable/how-to/logging.html) | `caplog` fixture captures log records; `caplog.set_level(DEBUG)` is required to capture debug records (only WARNING+ captured by default). Use this to assert the new log calls. |

### 1.3 Tech Stack Compatibility

| Candidate | Repo Dependency Compatibility | License | Decision |
|---|---|---|---|
| stdlib `logging` | Built-in (Python 3.11) | PSF | ✅ Recommended — no new dependency |
| stdlib `argparse` | Built-in (already used by `cli.py`) | PSF | ✅ Add `--verbose` to existing parser |
| `pytest` (dev only) | New dev dependency | MIT | ✅ Add to `[project.optional-dependencies] dev` (extended later by #4) |

---

## 2. Architecture Overview

### 2.1 Module List

| Module Key | Responsibility (one sentence) | Owned Artifacts |
|---|---|---|
| `doctopdf.converter` | Microsoft Word automation bridge; now also emits operational diagnostics | module logger `_log = logging.getLogger("doctopdf.converter")` |
| `doctopdf.cli` | Argument parsing + dispatch; now also configures stdlib logging at entry | `--verbose` flag; `logging.basicConfig(...)` call |

### 2.2 Boundaries

- **Entry points**: CLI (`convert-word-pdf` → `cli.main`).
- **Trust boundary**: `None` — no new trust boundary; logging is local diagnostics to `stderr`.
- **External → Internal**: `User` → `cli.main` → (configures root logger) → `Orchestrator` → `WordConverter` (whose module logger propagates to the configured root).

### 2.3 Target vs Baseline

| | Baseline (current) | Target (after change) |
|---|---|---|
| Failure handling in cleanup helpers | `except Exception: pass` (silent) | `except Exception as e: _log.debug(...)` (visible when verbose); warning on stalled relaunch |
| Diagnostics channel | None (only `ConversionLogger` per-file status to stdout) | stdlib `logging` to **stderr**, independent of `ConversionLogger` |
| CLI | no `--verbose` | `--verbose` flag configures `basicConfig(level=DEBUG)` |

---

## 3. Interaction Design

### 3.1 Interaction Anchors (`INT-###`)

| ID | Intent (when this coupling matters) | Caller → Callee | Coupling Type | Information / State Crossing | Failure Propagation Expectation |
|---|---|---|---|---|---|
| `INT-001` | Logging must be configured before any converter diagnostic is emitted | `cli.main` → `logging.basicConfig` → (propagates to) `doctopdf.converter` logger | stdlib logger hierarchy (implicit, via root) | effective log level only | If `basicConfig` is not called, debug/warning records are dropped silently (acceptable — best-effort diagnostics must never break conversion) |

### 3.2 Ordering / Concurrency Constraints (Design Level)

- `logging.basicConfig` must run **once, early** in `cli.main` (after `parse_args`, before mode dispatch) so both `--check` and convert paths emit at the configured level. `basicConfig` is a no-op if the root logger is already configured, so a single call is safe.
- The converter's helpers run on the single conversion thread (sequential batch); no concurrency concerns for logging.

### 3.3 Requirement Links

- **Req 1, 2, 3 cluster**: module logger `_log` in `converter.py` emits debug/warning records (no INT needed beyond `INT-001`).
- **Req 4 cluster**: `INT-001` — `cli.main` configures the level from `--verbose`.

---

## 4. External Dependencies

### 4.1 Dependency Overview

| Dependency | Purpose | Official Documentation |
|---|---|---|
| Python stdlib `logging` | Emit operational diagnostics at debug/warning levels | https://docs.python.org/3/library/logging.html |

No third-party runtime dependency is introduced. `pytest` is a dev-only addition (see CHECKLIST).

### 4.2 Python `logging`

#### Factual Basis

| Required Capability | Documentation Location |
|---|---|
| `getLogger(__name__)` per module | `references/python-logging.md`; [logging docs](https://docs.python.org/3/library/logging.html#logger-objects) |
| `basicConfig(level, stream, format)` at app entry | `references/python-logging.md`; [basicConfig docs](https://docs.python.org/3/library/logging.html#logging.basicConfig) |
| DEBUG/WARNING level constants | `references/python-logging.md` |

**Version assumption**: stdlib (Python 3.11) — floating.

#### Limits and Failure Modes

| Category | Documented Fact | Coding Obligation |
|---|---|---|
| Default handler behaviour | With no `basicConfig`, library loggers have **no handler** → records are dropped | Configure in `cli.main`; never rely on logging being pre-configured |
| Call-time safety | Logging calls must not raise into callers | `_log.debug/warning` with `%`-style args; never log in a way that can throw |
| Stream separation | `basicConfig(stream=sys.stderr)` keeps logs off stdout | Use `stream=sys.stderr` so `ConversionLogger`'s stdout status lines are unaffected |

#### Integration Anchors (`EXT-###`)

| ID | Integration Surface | Non-Negotiable Handling | Prohibited Assumptions |
|---|---|---|---|
| `EXT-001` | `logging.basicConfig` | Called once at CLI entry | Do not call it from `converter.py` (library code) |
| `EXT-002` | `_log.debug` / `_log.warning` | Best-effort; never propagates as exception | Do not assume a handler exists |

---

## 5. Data Persistence

| Resource | Typical Readers / Writers | Consistency Expectation |
|---|---|---|
| `None` | — | This change introduces no persistence. Diagnostics are ephemeral (stderr). |

---

## 6. System Invariants

| Invariant | How Architecture Could Violate It | Symptoms of Violation |
|---|---|---|
| Cleanup/quit/restart must never raise into the conversion flow | A logging call that throws, or removing the `try/except` | Conversion aborts during best-effort cleanup |
| `ConversionLogger` stdout status lines must remain clean and separate | Configuring logging to write to **stdout** or adding a handler that intercepts stdout | Debug noise interleaves with `✓/✗` per-file lines |
| `_is_word_running` must still return `False` on error | Forgetting the `return False` after adding the debug log | Caller treats Word as running → wrong restart behaviour |

---

## 7. Technical Trade-offs

| Decision | Rejected Alternatives | Lock-in Effect on Implementation |
|---|---|---|
| Module-level `_log = logging.getLogger(__name__)`, keep methods `@staticmethod` | Instance `self._log` (would require de-staticmethod-ing 5 methods → large churn) | Minimal; logger name fixed as `doctopdf.converter` |
| `basicConfig` in `cli.main`; default level **WARNING**, DEBUG on `--verbose` | (a) configure only when `--verbose` (warnings invisible by default — defeats Req 3 user value); (b) `dictConfig` (overkill for one logger) | Warnings visible to real users without `--verbose`; debug opt-in |
| `--verbose` as a **long-only** flag | `-v` short flag (already taken by `--version`) | No short alias for verbose |
| `stream=sys.stderr` | default stream (also stderr, but be explicit) | Guarantees stream separation from `ConversionLogger` stdout |

---

## 8. Design-Time Refactoring

| Finding | Affected Module | Tier | Disposition | Test Evidence |
|---|---|---|---|---|
| Four helpers (`_cleanup_stale_word`, `quit_word`, `_force_quit_word`, `_is_word_running`) repeat `subprocess.run(...) except Exception: pass` with embedded AppleScript strings | `doctopdf/converter.py` | T1 | **Deferred** — out of scope for #6 (issue is observability, not DRY); each site now logs a *distinct* message, reducing the DRY benefit. Revisit as a standalone refactor. | N/A (not refactored here) |
| Replace silent `pass` with `_log.debug/warning` | `doctopdf/converter.py` | T1 | **Refactored** (this change) | `tests/test_converter_logging.py` (caplog) |
| Wire `--verbose` + `basicConfig` | `doctopdf/cli.py` | T2 (cross-file within same package) | **Scheduled** (this change) | parser unit test + caplog level test |

---

## 9. Architecture Diff

**N/A (justified).** The project architecture atlas is empty (`apltk architecture status` → Features: 0, never initialized), and #6 introduces **no new feature, container, component, or module boundary** — it modifies two existing files within the same package and adds a stdlib logging channel. Producing a C4 diff here would mean fabricating baseline architecture that belongs to a separate `init-project-html` effort, not this change. No architectural boundary is crossed.

---

## 10. Test Infrastructure Hand-off (sequencing note)

#6 sits at **sequence position 1**, before #4 (the test-suite issue). To keep #6 self-verifying as its own PR, #6 **bootstraps** the minimal test infrastructure:
- creates `tests/` with `tests/test_converter_logging.py` (caplog-based), and
- adds `[project.optional-dependencies] dev = ["pytest"]` to `pyproject.toml`.

**#4 then extends** (does not recreate) the `dev` group — adding `pytest-cov`, `ruff`, `mypy` — and adds the broader scanner/errors/converter suites. This avoids duplicate infrastructure while keeping every PR independently verifiable.

---

## 11. References

- **Designed code file paths**:
  - `doctopdf/converter.py` — `_cleanup_stale_word:332`, `quit_word:360`, `_force_quit_word:389`, `restart_word:401`, `_is_word_running:434` (add module `_log` near top)
  - `doctopdf/cli.py` — `build_parser:27` (add `--verbose`), `main:231` (add `logging.basicConfig`)
  - `pyproject.toml` — add `[project.optional-dependencies] dev`
  - `tests/test_converter_logging.py` — to create
- **Reference docs**:
  - `references/python-logging.md`
  - `references/pytest-caplog.md`
- **Related documents**:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/issue-6-converter-exception-logging/SPEC.md`
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
