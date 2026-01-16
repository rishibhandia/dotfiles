#!/bin/bash
# Add a todo to Things 3 via URL scheme
# Usage: add_todo.sh <title> [--deadline DATE] [--when DATE] [--list PROJECT] [--notes TEXT] [--tags TAGS]

set -e

urlencode() {
    python3 -c "import urllib.parse; print(urllib.parse.quote('''$1''', safe=''))"
}

if [[ -z "$1" ]]; then
    echo "Usage: add_todo.sh <title> [options]"
    echo "Options:"
    echo "  --deadline DATE   Due date (YYYY-MM-DD or: tomorrow, next friday)"
    echo "  --when DATE       Start date (today, tomorrow, evening, someday, YYYY-MM-DD)"
    echo "  --list PROJECT    Target project name"
    echo "  --notes TEXT      Task description"
    echo "  --tags TAGS       Comma-separated tags"
    exit 1
fi

title="$1"
shift

deadline=""
when=""
list=""
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
        --list)
            list="$2"
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

url="things:///add?title=$(urlencode "$title")&reveal=true"

[[ -n "$deadline" ]] && url="$url&deadline=$(urlencode "$deadline")"
[[ -n "$when" ]] && url="$url&when=$(urlencode "$when")"
[[ -n "$list" ]] && url="$url&list=$(urlencode "$list")"
[[ -n "$notes" ]] && url="$url&notes=$(urlencode "$notes")"
[[ -n "$tags" ]] && url="$url&tags=$(urlencode "$tags")"

open "$url"
echo "Added todo: $title"
