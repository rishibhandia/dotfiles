#!/bin/bash
# Open Fantastical to a specific date
# Usage: show_date.sh 2026-01-20

if [[ -z "$1" ]]; then
    echo "Usage: show_date.sh <YYYY-MM-DD>"
    echo "Example: show_date.sh 2026-01-20"
    exit 1
fi

open "x-fantastical3://show?date=$1"
