# DocToPDF — Offline macOS Batch Document Converter

**Convert .doc and .docx files to PDF using Microsoft Word as the rendering engine.**  
Runs entirely offline with zero cloud dependencies.

## How It Works

```
Input (.doc/.docx)  ──→  Microsoft Word (JXA automation)  ──→  Output (.pdf)
```

The tool uses AppleScript/JXA (JavaScript for Automation) to tell Microsoft Word to open each document and export it as PDF. This guarantees **maximum formatting fidelity** — the PDF looks exactly as it would if you manually opened the file in Word and chose File → Export as PDF.

## Requirements

- **macOS** 11 (Big Sur) or later
- **Python** 3.9 or later (no extra pip packages needed)
- **Microsoft Word** for macOS (Office 2019, Microsoft 365, or later)
- **Automation permission**: Terminal → Microsoft Word (first run prompts automatically)

## Installation

### 1. Install via pip

```bash
pip install .
```

This installs the `convert-word-pdf` command globally.

### 2. Or run directly (no install)

```bash
python -m doctopdf --input ./docs --output ./pdfs
```

### 3. Verify Word is detected

```bash
convert-word-pdf --check
```

Expected output:
```
✓ Microsoft Word is installed (version: 16.72)
  The automation bridge is operational.
```

## Quick Start

```bash
# Convert all .doc/.docx files in ~/Documents/reports recursively
convert-word-pdf --input ~/Documents/reports --output ~/Documents/pdfs

# Same, but with abbreviated flags
convert-word-pdf -i ./docs -o ./pdfs -r

# Flat output (all PDFs in one folder)
convert-word-pdf -i ./docs -o ./pdfs --flat

# Top-level only (no subdirectory recursion)
convert-word-pdf -i ./docs -o ./pdfs --no-recursive

# Dry run — see what would be converted without doing it
convert-word-pdf -i ./docs -o ./pdfs --dry-run

# Custom timeout and retry for large/complex documents
convert-word-pdf -i ./docs -o ./pdfs --timeout 120 --retry 3

# Export results to a structured log
convert-word-pdf -i ./docs -o ./pdfs --log-file ./conversion-log.json
```

## Output Structure

### Mirrored Tree (Default)

The input directory structure is preserved under the output folder:

```
Input:                              Output:
./docs/                             ./pdfs/
├── report.docx            ──→      ├── report.pdf
├── subdir/                         ├── subdir/
│   ├── notes.docx         ──→      │   ├── notes.pdf
│   └── deep/                       │   └── deep/
│       └── final.docx     ──→      │       └── final.pdf
```

### Flat Mode (`--flat`)

All PDFs are written directly into the output folder. If filenames collide, a `_1`, `_2`, etc. suffix is appended.

```
./pdfs/
├── report.pdf
├── notes.pdf
├── notes_1.pdf
```

## CLI Reference

| Argument | Short | Default | Description |
|---|---|---|---|
| `--input` | `-i` | — | Input directory (`.doc`/`.docx` files) |
| `--output` | `-o` | — | Output directory for PDFs |
| `--recursive` | `-r` | `True` | Scan subdirectories |
| `--no-recursive` | — | — | Top-level scan only |
| `--flat` | — | `False` | Flat output (no mirrored tree) |
| `--timeout` | — | `60` | Seconds per document before timeout |
| `--retry` | — | `2` | Retries per failed conversion |
| `--restart-every` | — | `0` | Restart Word every N conversions (0 = never). Use for 100+ file batches |
| `--dry-run` | `-n` | `False` | Scan only, no conversion |
| `--log-file` | — | — | Export log to `.json` or `.csv` |
| `--quiet` | `-q` | `False` | Suppress per-file status |
| `--check` | — | — | Probe for Word installation |
| `--version` | `-v` | — | Show version |

## Error Handling

| Problem | What Happens | User Action |
|---|---|---|
| **Word not installed** | Clear error on startup | Install Microsoft Word |
| **Permission denied (-1743)** | Error with fix instructions | System Settings → Automation |
| **File locked / open in Word** | Retries 2×, then skips | Close the file in Word |
| **Corrupt document** | Skips with error message | Repair the source file |
| **Export failure** | Retries 2×, then skips | Try converting manually in Word |
| **Timeout** | Skips after `--timeout` seconds | Increase `--timeout` for large files |
| **File not writable** | Error with path details | Check output directory permissions |
| **Word crashes** | Detects crash, restarts Word, retries | Rare; check for Word updates |

### Retry Policy

The converter retries only **recoverable errors** (timeouts, transient export failures, Word crashes). It does **not** retry:
- Corrupt/unreadable documents (will always fail)
- Permission errors (user must fix)
- File access errors (disk or path issues)

## macOS Permissions

### Automation Permission

The first time you run the tool (or the Automator Quick Action), macOS will show a dialog:

> **"Terminal" wants access to control "Microsoft Word".**
> [Deny] [Allow]

Click **Allow**. If you accidentally deny, fix it:

1. Open **System Settings** (or System Preferences)
2. Go to **Privacy & Security → Automation**
3. Find **Terminal** (or your app — e.g., iTerm2, Automator)
4. Toggle **ON** the checkbox next to **"Microsoft Word"**

### File Access

The tool needs read access to the input directory and write access to the output directory. Standard macOS file permissions apply. For directories under `~/Documents`, your terminal app typically already has access.

### No Network/Accessibility Permissions

This tool requires:
- ✅ Automation (Terminal → Microsoft Word)
- ❌ No network/Internet access
- ❌ No Accessibility/Screen Recording permissions
- ❌ No Full Disk Access

## Automator Quick Action (Finder Right-Click)

Create a Finder service to right-click files/folders and convert them:

### Setup Steps

1. Open **Automator.app** (from `/Applications/Utilities/`)
2. **File → New → Quick Action**
3. Configure the workflow:
   - **Workflow receives:** `files or folders`
   - **In:** `Finder`
   - **Image:** pick a document/PDF icon

4. Add a **"Run Shell Script"** action (drag from the library):
   - **Shell:** `/bin/zsh`
   - **Pass input:** `as arguments`

5. Paste the following script:

```bash
#!/bin/zsh
# Automator Quick Action — Convert selected documents to PDF via Word

PROJECT_DIR="$HOME/Documents/doctopdf"
OUTPUT_BASE="$HOME/Documents/PDF_Conversions"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
OUTPUT_DIR="${OUTPUT_BASE}/batch_${TIMESTAMP}"

# Collect files into a temp input directory
INPUT_DIR=$(mktemp -d)
for item in "$@"; do
    if [ -d "$item" ]; then
        ln -s "$item"/* "$INPUT_DIR/" 2>/dev/null
    elif [ -f "$item" ]; then
        ln -s "$item" "$INPUT_DIR/"
    fi
done

mkdir -p "$OUTPUT_DIR"

cd "$PROJECT_DIR" || exit 1
python3 -m doctopdf --input "$INPUT_DIR" --output "$OUTPUT_DIR" --recursive

open "$OUTPUT_DIR"
rm -rf "$INPUT_DIR"
```

6. Save as **"Convert to PDF (Word)"**
7. Close Automator

### Usage

- Select files or folders in Finder
- **Right-click → Quick Actions → Convert to PDF (Word)**
- Or: **Right-click → Services → Convert to PDF (Word)**

The output folder opens in Finder when conversion completes.

## Comparison with Other Tools

| Dimension | DocToPDF (Word) | LibreOffice | Pandoc | python-docx |
|---|---|---|---|---|
| **Rendering fidelity** | ★★★★★ (Word's engine) | ★★★★ (good, minor diffs) | ★★ (markdown-centric) | ★ (no layout engine) |
| **Speed** | ★★★ (Word launch overhead) | ★★★★ (fast headless) | ★★★★★ | ★★★★★ |
| **License cost** | Requires Microsoft Word | Free | Free | Free |
| **Offline** | ✅ Fully | ✅ Fully | ✅ Fully | ✅ Fully |
| **VBA macros** | ✅ Executed | ⚠️ Partial | ❌ | ❌ |
| **Complex formatting** | ✅ Full Word fidelity | ⚠️ Minor regressions | ❌ | ❌ |
| **PDF bookmarks/TOC** | ✅ Word-native | ⚠️ Varies | ❌ | ❌ |
| **Batch-friendly** | ✅ Sequential | ✅ Parallel-capable | ✅ | ✅ |
| **macOS native** | ✅ AppleScript/JXA | ⚠️ X11 or headless | ✅ | ✅ |

### When to Use This Tool

- **Fidelity matters**: Legal documents, official submissions, contracts, academic papers
- **Complex formatting**: Multi-column layouts, embedded fonts, tracked changes, SmartArt
- **Security constraints**: The environment blocks cloud uploads and web APIs
- **Workflow integration**: You want a Finder right-click option

### When to Use LibreOffice Instead

- You don't have a Microsoft Word license
- You need to run headless on a server (Linux/CI)
- You need parallel batch conversion for hundreds of files
- Minor rendering differences are acceptable

## Performance Notes

### Expected Conversion Times

| File Type | Size | Typical Time |
|---|---|---|
| Simple text (.docx) | ~50 KB | 3–8 s |
| With images/tables | ~5 MB | 8–20 s |
| Large legacy (.doc) | ~20 MB | 15–45 s |
| Very large + complex | ~100 MB | 60–120 s |

**Cold start** (first conversion): includes Word launch time (+3–8s).  
**Subsequent conversions** are faster (2–5s typical) because Word stays warm.

### Keep Word Warm Strategy

The converter **never restarts Word between conversions** by default. This is deliberate — keeping Word running for the entire batch eliminates the 5–15s relaunch penalty and avoids the reliability issues that come with killing and restarting the application.

For very large batches (100+ files), use `--restart-every N` to periodically restart Word and prevent any accumulated state degradation. A good rule of thumb is `--restart-every 50`.

### No Parallelism

Microsoft Word on macOS is a single-instance application. Running parallel conversions would create race conditions on Word's internal state. This tool processes files **one at a time**, which is the reliable default.

### Batch Size

Tested with batches of 100+ files. For very large batches (1000+), consider splitting into smaller groups and running sequentially.

## Project Structure

```
doctopdf/
├── pyproject.toml            # Package build configuration
├── DESIGN.md                 # Architecture design document
├── README.md                 # This file
└── doctopdf/                 # Python package
    ├── __init__.py           # Package metadata
    ├── __main__.py           # `python -m doctopdf` entry
    ├── cli.py                # CLI argument parsing and dispatch
    ├── config.py             # Constants and defaults
    ├── converter.py          # Word automation bridge (JXA)
    ├── errors.py             # Exception hierarchy
    ├── logger.py             # Structured logging
    ├── orchestrator.py       # Batch coordination
    ├── scanner.py            # File discovery and path mapping
    └── applescript/          # JXA/AppleScript bridge files
        ├── check_word.applescript
        └── export_document.js
```

## Development

```bash
# Install in development mode
pip install -e .

# Run directly
python -m doctopdf --check
python -m doctopdf -i ./test_docs -o ./test_pdfs --dry-run

# Test with real files
python -m doctopdf -i ./test_docs -o ./test_pdfs
```

## Logging

### Per-file output (stdout)
```
  ✓ report.docx → report.pdf [4.2s]
  ✓ notes.docx → notes.pdf [3.1s]
  ✗ broken.docx → broken.pdf [5.0s] — Corrupt document: File format error
```

### Summary (end of run)
```
── Summary ──────────────────────────────────
  Total processed: 15
  Successful:      14  (62.3s spent on successful conversions)
  Errors:           1
  Average:         4.4s per file
  Total wall time: 67.8s

  Failed files (1):
    ✗ broken.docx: Corrupt document — File format error
```

### Structured log (--log-file)
Use `--log-file results.json` or `--log-file results.csv` for post-hoc analysis.

## License

MIT
