#!/bin/bash
# Search tasks in Things 3
# Usage: search.sh <query> [--limit N]

THINGS3_CLI="$HOME/.cargo/bin/things3"

if [[ ! -x "$THINGS3_CLI" ]]; then
    echo "Error: things3 CLI not found at $THINGS3_CLI"
    echo "Install with: cargo install things3"
    exit 1
fi

if [[ -z "$1" ]]; then
    echo "Usage: search.sh <query> [--limit N]"
    exit 1
fi

query="$1"
shift

limit=""

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

if [[ -n "$limit" ]]; then
    "$THINGS3_CLI" search "$query" --limit "$limit"
else
    "$THINGS3_CLI" search "$query"
fi
