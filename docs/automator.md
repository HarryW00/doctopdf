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
