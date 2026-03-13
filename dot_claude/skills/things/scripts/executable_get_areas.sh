#!/bin/bash
# List areas from Things 3 via AppleScript
# Usage: get_areas.sh

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

osascript << 'APPLESCRIPT'
tell application "Things3"
    set areaList to every area
    set output to ""

    repeat with a in areaList
        set output to output & "- " & name of a & linefeed
    end repeat

    if output is "" then
        return "No areas defined."
    end if
    return output
end tell
APPLESCRIPT
