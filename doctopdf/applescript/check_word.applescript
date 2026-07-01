(*
 check_word.applescript — Probe for Microsoft Word installation.

 Returns JSON to stdout indicating whether Word is installed and
 scriptable via AppleScript/JXA.

 Output:
   {"installed": true, "version": "16.72"}
   {"installed": false, "error": "…"}
*)

try
    tell application "Microsoft Word"
        set ver to version
    end tell
    return "{\"installed\":true,\"version\":\"" & ver & "\"}"
on error errMsg
    return "{\"installed\":false,\"error\":\"" & errMsg & "\"}"
end try
