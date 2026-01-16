#!/bin/bash
# Open Things 3 to a specific view
# Usage: show.sh <view>
# Views: inbox, today, upcoming, anytime, someday, logbook

if [[ -z "$1" ]]; then
    echo "Usage: show.sh <view>"
    echo "Views: inbox, today, upcoming, anytime, someday, logbook"
    exit 1
fi

view="$1"

case "$view" in
    inbox|today|upcoming|anytime|someday|logbook)
        open "things:///show?id=$view"
        echo "Opened Things to: $view"
        ;;
    *)
        echo "Unknown view: $view"
        echo "Valid views: inbox, today, upcoming, anytime, someday, logbook"
        exit 1
        ;;
esac
