#!/bin/bash
# List open projects from Things 3 via AppleScript
# Usage: get_projects.sh

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

osascript << 'APPLESCRIPT'
tell application "Things3"
    set projectList to every project whose status is open
    set output to ""

    repeat with p in projectList
        set projLine to "- " & name of p

        set areaName to ""
        try
            set areaName to name of area of p
            set projLine to projLine & "  (Area: " & areaName & ")"
        end try

        set output to output & projLine & linefeed
    end repeat

    if output is "" then
        return "No open projects."
    end if
    return output
end tell
APPLESCRIPT
