# Reference: pytest mocking patterns for the converter

Authoritative sources:
- monkeypatch: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- tmp_path: https://docs.pytest.org/en/stable/how-to/tmp_path.html

## Mocking `subprocess.run` to drive `convert()`

`WordConverter.convert` builds an osascript command, runs it via `subprocess.run`,
and parses JSON from stdout. To test classification without Word, patch
`doctopdf.converter.subprocess.run` to return a fake result.

```python
import subprocess

def _fake_completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=returncode,
                                       stdout=stdout, stderr=stderr)

def test_convert_success(monkeypatch):
    fake = _fake_completed(stdout='{"status": "ok"}', returncode=0)
    monkeypatch.setattr("doctopdf.converter.subprocess.run", lambda *a, **k: fake)
    # also create the expected output PDF so the post-checks pass, OR patch the
    # output-existence/header checks if focusing on classification.
```

Classification branches to cover (craft stdout/stderr accordingly):
- stderr contains `-1743` / `not allowed` / `permission` → `WordPermissionError`
- stderr contains `execution error` / `killed` → `WordCrashError`
- stdout JSON `{"status":"error","error":"...corrupt..."}` → `CorruptDocumentError`
- `subprocess.TimeoutExpired` raised → `ConversionTimeoutError`

## Testing `convert_with_retry` retry policy

Patch **both** `subprocess.run` (to raise/return) and `time.sleep` (no-op):

```python
def test_no_retry_terminal_errors(monkeypatch):
    calls = {"n": 0}
    def boom(*a, **k):
        calls["n"] += 1
        raise CorruptDocumentError(Path("x.docx"), "bad")
    monkeypatch.setattr("doctopdf.converter.WordConverter.convert", boom)
    monkeypatch.setattr("doctopdf.converter.time.sleep", lambda *a, **k: None)

    c = WordConverter(retry_count=2)
    with pytest.raises(CorruptDocumentError):
        c.convert_with_retry(Path("x.docx"), Path("x.pdf"))
    assert calls["n"] == 1          # terminal → no retry
```

For retriable errors, assert `calls["n"] == retry_count + 1` and that the final
raised exception is `ExportError("Failed after N attempts…")`. Backoff is linear:
`wait = retry_delay * attempt` (assert by spying on the patched `time.sleep` args).

## Constraints

- Always patch `time.sleep` in retry tests — never sleep for real.
- Prefer patching `WordConverter.convert` for pure retry-policy tests (faster, isolates the policy from classification); patch `subprocess.run` when testing classification inside `convert`.
