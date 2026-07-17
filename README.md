# DocToPDF — Offline macOS Batch Document Converter

<div align="center">
  
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey?logo=apple&logoColor=black)
![Automation: AppleScript](https://img.shields.io/badge/Automation-AppleScript%20%2F%20JXA-purple)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version: 1.1.0](https://img.shields.io/badge/version-1.1.0-brightgreen)
![CI](https://github.com/HarryW00/doctopdf/actions/workflows/lint.yml/badge.svg)

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

There are **two ways** to use this tool. Choose whichever is easier for you:

- **Option A** (recommended): Install it once, then run `convert-word-pdf` anywhere
- **Option B** (no install): Run it directly from the project folder using `python3 -m doctopdf`

Both options do the same thing. Option A is more convenient for repeated use.

---

### Option A: Install the tool (recommended)

This installs a command called `convert-word-pdf` that you can use from any folder on your Mac.

#### Step 1: Open Terminal

- Press **Cmd + Space** to open Spotlight Search
- Type **"Terminal"** and press Enter

> **💡 Tip:** You can also **Option + Right-Click** a folder in Finder and select **Services → Open in Terminal** (or **New Terminal at Folder**). This opens Terminal already `cd`'d to that location — no need to type a path.

#### Step 2: Navigate to the project folder

You need to be inside the `doctopdf` folder (the one containing this README file). Type this in Terminal:

```bash
cd ~/Documents/doctopdf
```

If you saved the project somewhere else, use that path instead. For example:
- Desktop: `cd ~/Desktop/doctopdf`
- Downloads: `cd ~/Downloads/doctopdf`

#### Step 3: Install the package

Run this command:

```bash
pip3 install .
```

**What this does:** It tells Python to install the `doctopdf` package (the `.` means "the current folder"). The tool is now available as the `convert-word-pdf` command.

> **⚠️ You might see a warning like this:**
> ```
> WARNING: The script convert-word-pdf is installed in
> '/Users/yourname/Library/Python/3.9/bin' which is not on PATH.
> ```
> This is normal on macOS — Python's install folder isn't on your
> system's PATH by default. If you see this, the tool **is installed**
> but the terminal can't find the `convert-word-pdf` command yet.
> Skip to the **Troubleshooting** section below for how to fix this
> in one minute. Or use **Option B** (run without installing) instead.

#### Step 4: Verify it worked

```bash
convert-word-pdf --check
```

You should see:
```
✓ Microsoft Word is installed (version: 16.72)
  The automation bridge is operational.
```

If instead you see an error, skip down to the **Troubleshooting** section.

---

### Option B: Run directly (no installation)

If you don't want to install anything, you can run the tool directly from the project folder.

#### Step 1: Open Terminal

- Press **Cmd + Space** → type **"Terminal"** → Enter

> **💡 Tip:** Option + Right-Click a folder in Finder and pick **Open in Terminal** to skip typing the `cd` path entirely.

#### Step 2: Navigate to the project folder

```bash
cd ~/Documents/doctopdf
```

(Change the path if you saved the project elsewhere.)

#### Step 3: Run the tool

Instead of `convert-word-pdf`, you'll use:

```bash
python3 -m doctopdf --check
```

This tells Python to run the `doctopdf` package (`.m doctopdf`) from the current folder. Use this same pattern whenever you see `convert-word-pdf` in the examples below:

| Instead of this | Use this |
|---|---|
| `convert-word-pdf --check` | `python3 -m doctopdf --check` |
| `convert-word-pdf -i ./docs -o ./pdfs` | `python3 -m doctopdf -i ./docs -o ./pdfs` |
| `convert-word-pdf --version` | `python3 -m doctopdf --version` |

---

### Step for both options: Verify Word is detected

After installing (or if running directly), run the check command to make sure everything is set up correctly:

```bash
# If you did Option A (installed)
convert-word-pdf --check

# If you did Option B (no install, run from project folder)
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

#### Fix B: Skip PATH entirely — use Option B instead

If you don't want to edit configuration files, don't install the tool at
all. Run it directly from the project folder instead:

```bash
cd ~/Documents/doctopdf
python3 -m doctopdf --check
```

See **Option B** in the Installation section above for full instructions.
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
