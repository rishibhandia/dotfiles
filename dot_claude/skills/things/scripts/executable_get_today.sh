#!/bin/bash
# Get today's tasks from Things 3 via AppleScript
# Usage: get_today.sh [--limit N]

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

limit=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)
            limit="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

osascript << APPLESCRIPT
tell application "Things3"
    set todayTodos to to dos of list "Today"
    set output to ""
    set taskCount to 0
    set lim to $limit

    repeat with t in todayTodos
        if lim > 0 and taskCount >= lim then exit repeat

        set taskName to name of t
        set taskLine to "- [ ] " & taskName

        try
            set projName to name of project of t
            set taskLine to taskLine & "  |  Project: " & projName
        end try

        set dueDate to due date of t
        if dueDate is not missing value then
            set taskLine to taskLine & "  |  Due: " & (short date string of dueDate)
        end if

        set taskTags to tag names of t
        if taskTags is not {} and taskTags is not "" then
            set taskLine to taskLine & "  |  Tags: " & taskTags
        end if

        set output to output & taskLine & linefeed
        set taskCount to taskCount + 1
    end repeat

    if output is "" then
        return "No tasks for today."
    end if
    return output
end tell
APPLESCRIPT
