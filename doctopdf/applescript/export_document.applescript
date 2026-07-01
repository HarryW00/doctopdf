(*
 export_document.applescript — Bridge between Python orchestrator and Microsoft Word.

 Opens a document file in Microsoft Word on macOS, exports it as PDF,
 and closes the document without saving changes to the original.

 Usage via osascript:
   osascript export_document.applescript "<inputPath>" "<outputPath>" [timeoutSec]

 Output (stdout):
   {"status":"success","input":"...","output":"..."}
   {"status":"error","input":"...","error":"..."}

 Returns JSON to stdout so the Python orchestrator can parse results reliably.

 Note: Paths must be absolute POSIX paths. The script converts them to
 Alias objects for Word using `POSIX file as alias` coercion.
*)

on run argv
    -- ── Parse arguments ────────────────────────────────────────
    if (count of argv) < 2 then
        return "{\"status\":\"error\",\"error\":\"Missing arguments. Usage: export_document.applescript <inputPath> <outputPath> [timeoutSec]\"}"
    end if

    set inputPath to item 1 of argv
    set outputPath to item 2 of argv

    -- ── Validate input file exists ─────────────────────────────
    try
        set inputFile to inputPath as POSIX file as alias
    on error
        return "{\"status\":\"error\",\"input\":\"" & inputPath & "\",\"error\":\"File not found: " & inputPath & "\"}"
    end try

    -- ── Convert ────────────────────────────────────────────────
    try
        tell application "Microsoft Word"
            -- Open the document
            open inputFile

            -- Wait briefly for Word to finish loading the document.
            -- The document may not be immediately scriptable after open().
            delay 1

            -- Capture a stable reference to the document before exporting.
            -- After save-as, active document may change, so we hold a
            -- persistent reference here.
            set targetDoc to active document
            if targetDoc is missing value then
                -- File needs more time to load
                delay 2
                set targetDoc to active document
            end if

            -- Export as PDF using Word's built-in PDF format constant
            save as targetDoc file name outputPath file format format PDF

            -- Close the document without saving changes to the original.
            -- We use the captured reference rather than 'active document'
            -- because after save-as the active document may have shifted.
            try
                close targetDoc saving no
            on error
                -- If the captured reference is stale, try active document
                try
                    close active document saving no
                end try
                -- If both fail, the document may have auto-closed after save.
                -- This is not a conversion failure — the PDF was already created.
            end try
        end tell

        -- ── Verify output was created ──────────────────────────
        try
            set outputFile to outputPath as POSIX file as alias
            return "{\"status\":\"success\",\"input\":\"" & inputPath & "\",\"output\":\"" & outputPath & "\"}"
        on error
            return "{\"status\":\"error\",\"input\":\"" & inputPath & "\",\"error\":\"PDF file was not created at: " & outputPath & "\"}"
        end try

    on error errMsg
        -- ── Cleanup ────────────────────────────────────────────
        -- Attempt to close any open document without saving
        try
            tell application "Microsoft Word"
                close active document saving no
            end tell
        end try

        -- Check for common permission error
        if errMsg contains "-1743" then
            return "{\"status\":\"error\",\"input\":\"" & inputPath & "\",\"error\":\"macOS Automation permission denied (-1743). Grant Terminal access to control Microsoft Word in System Settings → Privacy & Security → Automation.\"}"
        end if

        -- Escape quotes in the error message for JSON
        set escapedMsg to my escape_json(errMsg)
        return "{\"status\":\"error\",\"input\":\"" & inputPath & "\",\"error\":\"" & escapedMsg & "\"}"
    end try
end run

-- Helper: escape special characters for JSON output
on escape_json(str)
    set AppleScript's text item delimiters to "\\"
    set str to text items of str
    set AppleScript's text item delimiters to "\\\\"
    set str to str as string

    set AppleScript's text item delimiters to "\""
    set str to text items of str
    set AppleScript's text item delimiters to "\\\""
    set str to str as string

    set AppleScript's text item delimiters to ""
    return str
end escape_json
