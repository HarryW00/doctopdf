# Spec: Unit Test Suite (#4)

- **Date**: 2026-07-16
- **Feature**: unit-test-suite
- **Batch**: issues-3-8-quality-sweep — **sequence position 3 of 5** (order: #6 → #3 → #4 → #7 → #8)
- **Source issue**: GitHub #4 (testing)

## Goal

Establish the project's first automated test suite so regressions in file discovery, error classification, and retry behaviour are caught without manual runs and **without Microsoft Word installed**.

## Scope

### In Scope

- **Extend** the `dev` optional-dependency group (bootstrapped with `pytest` by #6) to add `pytest-cov`, `ruff`, `mypy`.
- **Fix the `CorruptDocumentError` construction bug (issue #9)** so the class is instantiable and stores `input_path` — a one-line change in `errors.py`. #4 closes #9. *(Discovered while planning this spec's error tests.)*
- `tests/test_scanner.py` — discovery, filtering, output-path mapping, and collision resolution.
- `tests/test_errors.py` — exception messages and the full class hierarchy.
- `tests/test_converter.py` — `subprocess.run` mocked to exercise the conversion result-classification and retry policy without real Word.

### Out of Scope

- Integration tests that invoke real Microsoft Word.
- End-to-end CLI tests (separate effort).
- A coverage **fail-under threshold** — coverage is reported only, per the agreed decision (no gate).
- Tests for `ConversionLogger` summary/CSV/JSON rendering (not required by the issue; future work).

## Functional Behaviors (BDD)

### Requirement 1: Scanner discovery is correct and deterministic
**GIVEN** a temporary input tree containing `.doc`, `.docx`, `.pdf`, `.txt`, a hidden (dot-prefixed) file, a `~$` Word lock file, and a 0-byte file, spread across nested and top-level directories
**WHEN** `find_documents` is called with `recursive=True` and again with `recursive=False`
**THEN** only the `.doc`/`.docx` files (excluding hidden, `~$`, and sub-`MIN_FILE_SIZE_BYTES` files) are returned
**AND** results are sorted deterministically
**AND** `recursive=False` omits files in nested subdirectories

**Uncertainty Level**: Known

### Requirement 2: Output mapping and collision resolution are correct
**GIVEN** an input file located under a nested input root
**WHEN** `map_output_path` is called with `flat=True` and with `flat=False`
**THEN** flat mode yields `output_root/<stem>.pdf` and mirrored mode preserves the relative subdirectory with the suffix changed to `.pdf`
**AND WHEN** `resolve_collision` is given a path that already exists (and sequential `_1`, `_2` siblings)
**THEN** it returns the first non-existent `<stem>_N.pdf`, never returning a path that already exists

**Uncertainty Level**: Known

### Requirement 3: Exception hierarchy and messages are correct
**GIVEN** the custom exception classes in `errors.py`
**WHEN** each is constructed with representative arguments
**THEN** it carries the expected human-readable message and (where applicable) the originating `input_path`
**AND** `CorruptDocumentError` is a subclass of `DocumentOpenError`, which is a subclass of `DocToPDFError`, which is a subclass of the built-in `Exception`

**Uncertainty Level**: Known

### Requirement 4: Retry policy classifies errors correctly (mocked subprocess)
**GIVEN** `convert_with_retry` with `subprocess.run` (and `time.sleep`) mocked
**WHEN** a terminal error (`CorruptDocumentError`, `WordPermissionError`, `DocumentOpenError`, or `FileAccessError`) is raised on the first attempt
**THEN** it is re-raised immediately with no retry and no backoff sleep
**AND WHEN** a retriable error (`ExportError`, `ConversionTimeoutError`, or `WordCrashError`) is raised
**THEN** it is retried up to `retry_count` additional times with linear backoff (`retry_delay × attempt`) between attempts
**AND** when all attempts fail it raises `ExportError("Failed after N attempts…")`

**Uncertainty Level**: Known

### Requirement 5: The suite runs Word-free and is installable via the dev extra
**GIVEN** `pyproject.toml` declares the `dev` optional-dependency group with `pytest`, `pytest-cov`, `ruff`, `mypy`
**WHEN** a contributor runs `pip install -e ".[dev]"` then `pytest tests/`
**THEN** the suite runs to completion **without Microsoft Word installed** (the converter is fully mocked)
**AND** exits 0 with a coverage report emitted (no fail-under threshold enforced)

**Uncertainty Level**: Known

## Error and Edge Cases

- Mocked `subprocess.run` returning success JSON missing the `attempts` key → defaults to `1`.
- Mocked `subprocess.run` raising `TimeoutExpired` → `ConversionTimeoutError` (retriable).
- Bridge returns `status='error'` containing the keyword `corrupt` → `CorruptDocumentError` (terminal, not retried).
- `convert` stderr containing `-1743` / `not allowed` → `WordPermissionError` (terminal).
- `resolve_collision` when `_1`…`_1000` all exist → falls back to the timestamp path (edge case).
- `find_documents` on a non-existent directory → returns `[]`.
- `map_output_path` on a path outside `input_root` → uses the filename only.

## Clarification Questions

- None. All requirements are Known. The Python baseline is **3.11** (resolved in the **#7** spec, which also bumps `requires-python` to `>=3.11`).

## References

- **Key code file paths** affected by this spec:
  - `doctopdf/scanner.py` — `find_documents:15`, `map_output_path:61`, `resolve_collision:103`, `resolve_input_paths:130`
  - `doctopdf/errors.py` — full hierarchy (`DocToPDFError:12` … `WordCrashError:93`)
  - `doctopdf/converter.py` — `convert:133`, `convert_with_retry:270` (terminal tuple at 292–297, linear backoff at 314)
  - `doctopdf/config.py` — `SUPPORTED_EXTENSIONS:11` (`{'.doc', '.docx'}`), `MIN_FILE_SIZE_BYTES:14` (`1`)
  - `pyproject.toml` — `[project.optional-dependencies] dev` bootstrapped by #6 (`pytest`); extended by #4 (`pytest-cov`, `ruff`, `mypy`)
- Related project context files:
  - `docs/plans/2026-07-16/issues-3-8-quality-sweep/PROPOSAL.md`
