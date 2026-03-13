#!/bin/bash
# Search tasks in Things 3 via AppleScript
# Usage: search.sh <query> [--limit N] [--all]
#   --all    Include completed and cancelled tasks (default: open only)

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

if [[ -z "$1" || "$1" == --* ]]; then
    echo "Usage: search.sh <query> [--limit N] [--all]"
    exit 1
fi

query="$1"
shift

limit=0
include_all=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)
            limit="$2"
            shift 2
            ;;
        --all)
            include_all=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Escape double quotes to prevent AppleScript injection
safe_query="${query//\"/\\\"}"

osascript << APPLESCRIPT
tell application "Things3"
    set q to "$safe_query"
    set allTodos to every to do
    set output to ""
    set taskCount to 0
    set lim to $limit
    set includeAll to $include_all

    repeat with t in allTodos
        if lim > 0 and taskCount >= lim then exit repeat

        set taskStatus to status of t
        if not includeAll and taskStatus is not open then
            -- skip non-open tasks unless --all
        else if name of t contains q then
            set taskName to name of t

            set statusMarker to ""
            if taskStatus is completed then
                set statusMarker to "[completed] "
            else if taskStatus is canceled then
                set statusMarker to "[canceled] "
            end if

            set taskLine to "- " & statusMarker & taskName

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
        end if
    end repeat

    if output is "" then
        return "No tasks matching: " & q
    end if
    return output
end tell
APPLESCRIPT
