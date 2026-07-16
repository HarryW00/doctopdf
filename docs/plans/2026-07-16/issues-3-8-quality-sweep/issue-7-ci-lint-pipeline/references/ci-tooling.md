# Reference: CI tooling — ruff, mypy, GitHub Actions

Authoritative sources:
- Ruff config: https://docs.astral.sh/ruff/configuration/ · settings: https://docs.astral.sh/ruff/settings/
- mypy config: https://mypy.readthedocs.io/en/stable/config_file.html
- actions/setup-python: https://github.com/marketplace/actions/setup-python

## `pyproject.toml` additions (issue #7)

```toml
# under [project]
requires-python = ">=3.11"
# classifiers: keep "3.11" and "3.12"; REMOVE "3.9" and "3.10"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

> `target-version = "py311"` is the string form documented by Ruff for Python ≥3.11.
> `ignore_missing_imports = true` is a **global** mypy option (per-module override is also possible).

## GitHub Actions workflow (`.github/workflows/lint.yml`)

```yaml
name: Lint

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"      # pytest, pytest-cov, ruff, mypy (from #4)
      - run: ruff check doctopdf/
      - run: mypy doctopdf/ --ignore-missing-imports
      - run: pytest tests/
```

## README badge (issue #7)

Beneath the existing badge row:
```markdown
![CI](https://github.com/HarryW00/doctopdf/actions/workflows/lint.yml/badge.svg)
```
Also update the existing `Python-3.9+` badge to `Python-3.11+`.

## Constraints

- Install via `pip install -e ".[dev]"` so a single step provides ruff, mypy, pytest, pytest-cov (the `[dev]` extra is defined by #4).
- Keep lint scope to `ruff check` (+ `mypy`) per issue #7; `ruff format --check` is a deferred one-line future addition.
- CI must be green on the first run — clean all pre-existing `ruff`/`mypy` violations in `doctopdf/` before merging.
