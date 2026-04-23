#!/bin/bash
# Open Things 3 to a specific view
# Usage: show.sh <view>
# Views: inbox, today, tomorrow, upcoming, anytime, someday, logbook, deadlines, repeating, all-projects, logged-projects

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

if [[ -z "$1" ]]; then
    echo "Usage: show.sh <view>"
    echo "Views: inbox, today, tomorrow, upcoming, anytime, someday, logbook, deadlines, repeating, all-projects, logged-projects"
    exit 1
fi

view="$1"

case "$view" in
    inbox|today|tomorrow|upcoming|anytime|someday|logbook|deadlines|repeating|all-projects|logged-projects)
        open "things:///show?id=$view"
        echo "Opened Things to: $view"
        ;;
    *)
        echo "Unknown view: $view"
        echo "Valid views: inbox, today, tomorrow, upcoming, anytime, someday, logbook, deadlines, repeating, all-projects, logged-projects"
        exit 1
        ;;
esac
