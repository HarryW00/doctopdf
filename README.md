# DocToPDF — Offline macOS Batch Document Converter

<div align="center">
  
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey?logo=apple&logoColor=black)
![Automation: AppleScript](https://img.shields.io/badge/Automation-AppleScript%20%2F%20JXA-purple)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version: 1.2.0](https://img.shields.io/badge/version-1.2.0-brightgreen)
![CI](https://github.com/HarryW00/doctopdf/actions/workflows/lint.yml/badge.svg)

</div>

<div align="center">

<!-- TODO: Add demo GIF — terminal recording showing batch conversion workflow (e.g. asciinema or QuickTime screen recording). Save to docs/images/demo.gif -->

</div>

**Convert .doc and .docx files to PDF using Microsoft Word as the rendering engine.**  
Runs entirely offline with zero cloud dependencies.

## How It Works

```
Input (.doc/.docx)  ──→  Microsoft Word (JXA automation)  ──→  Output (.pdf)
```

The tool uses AppleScript/JXA (JavaScript for Automation) to tell Microsoft Word to open each document and export it as PDF. This guarantees **maximum formatting fidelity** — the PDF looks exactly as it would if you manually opened the file in Word and chose File → Export as PDF.

## Requirements (what you need before starting)

Before you can use this tool, make sure you have everything listed below:

| Requirement | Why you need it | How to check you have it |
|---|---|---|
| **macOS 11 (Big Sur) or newer** | Only runs on Mac | Click the Apple menu  → About This Mac → look at macOS version |
| **Python 3.9 or later** | The tool is written in Python | Open Terminal and type `python3 --version`. You should see `Python 3.9.x` or higher. If you don't have Python, see the note below. |
| **Microsoft Word for Mac** | This is the engine that actually converts the files to PDF. You need Word 2019, Microsoft 365, or any newer version. | Open Word and go to Word menu → About Microsoft Word |
| **Automation permission** | macOS needs your permission before this tool can talk to Word. You'll be prompted on first use. | You don't need to check this in advance — see the Permissions section below. |

> **No Python?** macOS usually comes with Python 3 pre-installed. If `python3 --version` gives an error, install Python from [python.org](https://www.python.org/downloads/). Download the macOS installer, run it, and follow the steps.

## Installation (step by step)

There are **three ways** to use this tool. Choose whichever is easiest for you:

| Option | Method | Best for |
|--------|--------|----------|
| **A** | [Homebrew](https://brew.sh) — `brew install harryw00/doctopdf/doctopdf` | Everyone with Homebrew installed |
| **B** | pip — `pip3 install .` (from source) | Users who prefer pip / don't have Homebrew |
| **C** | Run without install — `python3 -m doctopdf` | Quick test, no installation wanted |

---

### Option A: Install via Homebrew (easiest)

If you have [Homebrew](https://brew.sh) installed, this is the one-command way:

```bash
brew install harryw00/doctopdf/doctopdf
```

Homebrew automatically sets up all paths — no `cd`, no `pip`, no PATH fixes needed.
It also keeps `doctopdf` up-to-date when you run `brew update && brew upgrade`.

#### Verify it worked

```bash
convert-word-pdf --check
```

---

### Option B: Install via pip

> **📦 PyPI package pending** — Once published, you'll be able to run `pip3 install doctopdf`.
> For now, install from the source checkout.

#### Step 1: Open Terminal

- Press **Cmd + Space** → type **"Terminal"** → Enter

#### Step 2: Get the source

```bash
git clone https://github.com/HarryW00/doctopdf.git
cd doctopdf
```

*(Or download the ZIP from GitHub and extract it.)*

#### Step 3: Install

```bash
pip3 install .
```

> **⚠️ You may see a warning like this:**
> ```
> WARNING: The script convert-word-pdf is installed in
> '/Users/yourname/Library/Python/3.9/bin' which is not on PATH.
> ```
> This is normal on macOS — Python's install folder isn't on your `PATH` by default.
> See the **Troubleshooting** section below to fix this in one minute.

#### Step 4: Verify it worked

```bash
convert-word-pdf --check
```

You should see:

```
✓ Microsoft Word is installed (version: 16.72)
  The automation bridge is operational.
```

---

### Option C: Run directly (no installation)

If you'd rather not install anything, run the tool straight from the project folder:

```bash
cd path/to/doctopdf
python3 -m doctopdf --check
```

Use `python3 -m doctopdf` wherever the docs say `convert-word-pdf`:

| Instead of this | Use this |
|-----------------|----------|
| `convert-word-pdf --check` | `python3 -m doctopdf --check` |
| `convert-word-pdf -i ./docs -o ./pdfs` | `python3 -m doctopdf -i ./docs -o ./pdfs` |
| `convert-word-pdf --version` | `python3 -m doctopdf --version` |

---

### After installing (all options)

Run the check to make sure Word is detected:

```bash
# Installed (Option A or B)
convert-word-pdf --check

# Direct run (Option C)
python3 -m doctopdf --check
```

**Expected output:**

```
✓ Microsoft Word is installed (version: 16.72)
  The automation bridge is operational.
```

**If you see "Word is NOT installed":**
1. Make sure Microsoft Word is actually installed (open it from Applications)
2. If Word opens but the check still fails, close Word completely (Word menu → Quit Microsoft Word) and try again
3. If you just installed Word, restart your Mac and try again

**If you see a permission error (-1743):**
This means macOS hasn't granted Automation permission yet. Run the command a second time — macOS should show a permission dialog. Click **Allow**. See the **macOS Permissions** section below if this doesn't happen.

> **⚠️ Data Safety — Important**
>
> DocToPDF is a **batch automation tool**. If you accidentally point it at the wrong folder or a file gets corrupted during conversion, documents could be lost or damaged.
>
> **Before running your first conversion:**
> 1. **Back up your documents** — copy your `.doc` / `.docx` files to a separate backup folder, or ensure you have Time Machine or cloud backup running
> 2. **Use a dedicated input folder** — copy the files you want to convert into a new folder rather than pointing the tool at your master document directory
> 3. **Try a dry run first** — add `--dry-run` to see which files will be processed before any conversion happens:
>    ```bash
>    convert-word-pdf -i ./docs -o ./pdfs --dry-run
>    ```

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

<!-- TODO: Add screenshot — macOS Automation Permission dialog ("Terminal" wants access to control "Microsoft Word"). Save to docs/images/automation-permission-dialog.png -->

Click **Allow**. If you accidentally deny, fix it:

1. Open **System Settings** (or System Preferences)
2. Go to **Privacy & Security → Automation**
3. Find **Terminal** (or your app — e.g., iTerm2, Automator)
4. Toggle **ON** the checkbox next to **"Microsoft Word"**

### File Access

The tool needs read access to the input directory and write access to the output directory. Standard macOS file permissions apply. For directories under `~/Documents`, your terminal app typically already has access.

When Microsoft Word opens a document from a folder it hasn't accessed before, macOS may show a **"Grant File Access"** dialog:

<!-- TODO: Add screenshot — see docs/images/file-access-dialog.png -->
```
Microsoft Word wants to access files in your "Downloads" folder.
[Deny] [Allow]
```

Click **Allow** so Word can read the source document and write the PDF. If you click Deny by accident, the conversion will fail with a file-access error — just re-run the tool and macOS will prompt again.

### No Network/Accessibility Permissions

This tool requires:
- ✅ Automation (Terminal → Microsoft Word)
- ❌ No network/Internet access
- ❌ No Accessibility/Screen Recording permissions
- ❌ No Full Disk Access

## Automator Quick Action (Finder Right-Click)

Create a macOS Finder right-click service that converts documents to PDF without opening Terminal. See the [full setup guide](docs/automator.md) for step-by-step instructions.

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

## Troubleshooting

### "convert-word-pdf: command not found" after installation

This is the most common issue on macOS. Here is what happened and how to fix it.

**Why this happens:** When you run `pip3 install .`, Python installs the
`convert-word-pdf` command into a folder like:

```
/Users/yourname/Library/Python/3.9/bin
```

That folder is a standard install location used by Python's `pip` on macOS.
However, macOS does not include this folder in your terminal's search path
(the technical term is `PATH`) by default. So even though the tool is
installed, your terminal doesn't know where to find it.

**How to fix it (two ways):**

#### Fix A: Add the folder to your PATH (do this once)

1. Find out which Python version you have:

   ```bash
   python3 --version
   ```

   This will show something like `Python 3.9.x`. Note the **major.minor**
   version number (e.g. `3.9`).

2. Open your shell configuration file:

   - If you use **zsh** (default on macOS Catalina and newer):

     ```bash
     nano ~/.zshrc
     ```

   - If you use **bash** (older macOS versions):

     ```bash
     nano ~/.bash_profile
     ```

3. Add this line at the bottom of the file (replace `3.9` with the Python
   version you saw in step 1):

   ```bash
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"
   ```

   **What this does:** It tells your terminal to look in the Python bin
   folder whenever you type a command, so it can find `convert-word-pdf`.

4. Save the file:
   - Press **Ctrl + O** → **Enter** to save
   - Press **Ctrl + X** to exit nano

5. Reload your configuration:

   ```bash
   source ~/.zshrc
   ```

   (If you used `~/.bash_profile` instead, run `source ~/.bash_profile`.)

6. Verify it worked:

   ```bash
   convert-word-pdf --version
   ```

   You should see `convert-word-pdf 1.0.0` instead of "command not found."

#### Fix B: Skip PATH entirely — use Option C instead

If you don't want to edit configuration files, don't install the tool at
all. Run it directly from the project folder instead:

```bash
cd ~/Documents/doctopdf
python3 -m doctopdf --check
```

See **Option C** in the Installation section above for full instructions.
The tool works identically either way — you just type a slightly longer
command.

### Check which Python is active

If you have multiple Python versions installed, `pip3 install` and
`python3 -m doctopdf` might use different Python installations, causing
confusion. Verify they match:

```bash
pip3 --version
python3 --version
```

Both should reference the same Python version (e.g. `Python 3.9.x`).
If they don't, use the full path to your desired Python, for example:

```bash
/usr/local/bin/python3 -m doctopdf --check
```

### Permission errors with osascript (-1743)

See the **macOS Permissions** section earlier in this document.

## License

MIT
