#!/bin/bash
# Add a project to Things 3 via URL scheme
# Usage: add_project.sh <title> [--deadline DATE] [--area AREA] [--notes TEXT] [--tags TAGS]

set -e

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Things 3 is macOS only"
    exit 1
fi

urlencode() {
    printf '%s' "$1" | python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read(), safe=''))"
}

if [[ -z "$1" ]]; then
    echo "Usage: add_project.sh <title> [options]"
    echo "Options:"
    echo "  --deadline DATE   Project deadline (YYYY-MM-DD)"
    echo "  --when DATE       Start date (today, tomorrow, evening, someday, YYYY-MM-DD)"
    echo "  --area AREA       Target area name"
    echo "  --notes TEXT      Project description"
    echo "  --tags TAGS       Comma-separated tags"
    exit 1
fi

title="$1"
shift

deadline=""
when=""
area=""
notes=""
tags=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --deadline)
            deadline="$2"
            shift 2
            ;;
        --when)
            when="$2"
            shift 2
            ;;
        --area)
            area="$2"
            shift 2
            ;;
        --notes)
            notes="$2"
            shift 2
            ;;
        --tags)
            tags="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

url="things:///add-project?title=$(urlencode "$title")&reveal=true"

[[ -n "$deadline" ]] && url="$url&deadline=$(urlencode "$deadline")"
[[ -n "$when" ]] && url="$url&when=$(urlencode "$when")"
[[ -n "$area" ]] && url="$url&area=$(urlencode "$area")"
[[ -n "$notes" ]] && url="$url&notes=$(urlencode "$notes")"
[[ -n "$tags" ]] && url="$url&tags=$(urlencode "$tags")"

open "$url"
echo "Added project: $title"
