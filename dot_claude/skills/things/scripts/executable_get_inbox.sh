#!/bin/bash
# Get inbox tasks from Things 3 via AppleScript
# Usage: get_inbox.sh [--limit N]

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
    set inboxTodos to to dos of list "Inbox"
    set output to ""
    set taskCount to 0
    set lim to $limit

    repeat with t in inboxTodos
        if lim > 0 and taskCount >= lim then exit repeat

        set taskName to name of t
        set taskLine to "- [ ] " & taskName

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
        return "Inbox is empty."
    end if
    return output
end tell
APPLESCRIPT
