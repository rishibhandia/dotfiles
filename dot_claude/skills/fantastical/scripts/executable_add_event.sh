#!/bin/bash
# Add an event to Fantastical using natural language
# Usage: add_event.sh "Meeting with John tomorrow at 3pm"

if [[ -z "$*" ]]; then
    echo "Usage: add_event.sh <event description>"
    echo "Example: add_event.sh \"Meeting with John tomorrow at 3pm\""
    exit 1
fi

osascript -e "tell application \"Fantastical\" to parse sentence \"$*\" with add immediately"
