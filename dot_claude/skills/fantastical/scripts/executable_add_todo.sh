#!/bin/bash
# Add a todo/reminder to Fantastical
# Usage: add_todo.sh "Review PR by Friday"

if [[ -z "$*" ]]; then
    echo "Usage: add_todo.sh <todo description>"
    echo "Example: add_todo.sh \"Review PR by Friday\""
    exit 1
fi

osascript -e "tell application \"Fantastical\" to parse sentence \"todo $*\" with add immediately"
