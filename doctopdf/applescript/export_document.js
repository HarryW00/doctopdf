#!/usr/bin/env osascript -l JavaScript
/**
 * export_document.js — JXA bridge to Microsoft Word
 *
 * Opens a document in Microsoft Word on macOS and exports it as PDF.
 * Returns a JSON-encoded result object to stdout so the Python
 * orchestrator can parse it reliably.
 *
 * Usage (via osascript):
 *   osascript -l JavaScript export_document.js <inputPath> <outputPath> [timeoutSec]
 *
 * Output (stdout):
 *   {"status":"success","input":"...","output":"..."}
 *   {"status":"error","input":"...","error":"..."}
 *
 * Exit codes:
 *   0 — JSON result written to stdout (check "status" key)
 *   1 — osascript-level failure (script error, not Word error)
 */

function run(argv) {
    // ── Parse arguments ────────────────────────────────────────
    if (argv.length < 2) {
        return JSON.stringify({
            status: 'error',
            error: 'Missing arguments. Usage: export_document.js <inputPath> <outputPath> [timeoutSec]'
        });
    }

    var inputPath  = String(argv[0]);
    var outputPath = String(argv[1]);
    var timeoutSec = argv.length > 2 ? parseInt(argv[2], 10) : 60;

    if (isNaN(timeoutSec) || timeoutSec < 1) {
        timeoutSec = 60;
    }

    // ── Validate file exists ───────────────────────────────────
    var fm = $.NSFileManager.defaultManager;
    if (!fm.fileExistsAtPath(inputPath)) {
        return JSON.stringify({
            status: 'error',
            input: inputPath,
            error: 'File not found: ' + inputPath
        });
    }

    // ── Perform conversion ─────────────────────────────────────
    try {
        var app = Application('Microsoft Word');
        app.includeStandardAdditions = true;

        // -- Open the document -----------------------------------
        var doc = app.open(inputPath);
        if (!doc) {
            return JSON.stringify({
                status: 'error',
                input: inputPath,
                error: 'Word returned null when opening document'
            });
        }

        // -- Export as PDF ---------------------------------------
        // The 'as' parameter value may vary by Word locale/version.
        // Common values: 'PDF', 'Microsoft Word Document (*.pdf)', or
        // internal constant. We default to 'PDF'.
        var exportResult = doc.export({
            to: outputPath,
            as: 'PDF'
        });

        // -- Close without saving changes to original ------------
        doc.close({ saving: 'no' });

        // -- Verify output was created ---------------------------
        if (!fm.fileExistsAtPath(outputPath)) {
            return JSON.stringify({
                status: 'error',
                input: inputPath,
                error: 'Word reported success but PDF was not created at: ' + outputPath
            });
        }

        return JSON.stringify({
            status: 'success',
            input: inputPath,
            output: outputPath
        });

    } catch (e) {
        // ── Cleanup ────────────────────────────────────────────
        // Attempt to close any document that may still be open.
        try {
            var activeDoc = app.activeDocument;
            if (activeDoc) {
                activeDoc.close({ saving: 'no' });
            }
        } catch (ignore) {
            // Best-effort cleanup; ignore further errors.
        }

        var errorMsg = String(e.message || e);
        // Detect common macOS permission error
        if (errorMsg.indexOf('-1743') !== -1) {
            errorMsg = 'macOS Automation permission denied (-1743). ' +
                'Grant Terminal/automation access to control Microsoft Word.';
        } else if (errorMsg.indexOf('Microsoft Word') === -1 && errorMsg.indexOf('Error') === -1) {
            // Some JXA errors omit the app name — prefix for clarity
            errorMsg = 'Microsoft Word: ' + errorMsg;
        }

        return JSON.stringify({
            status: 'error',
            input: inputPath,
            error: errorMsg,
            suggestions: [
                'Ensure the document is not already open in Word',
                'Ensure the output path is writable',
                'Check the document is not corrupt'
            ]
        });
    }
}
