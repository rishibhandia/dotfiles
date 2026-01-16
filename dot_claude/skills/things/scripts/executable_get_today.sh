#!/bin/bash
# Get today's tasks from Things 3
# Usage: get_today.sh [--limit N]

THINGS3_CLI="$HOME/.cargo/bin/things3"

if [[ ! -x "$THINGS3_CLI" ]]; then
    echo "Error: things3 CLI not found at $THINGS3_CLI"
    echo "Install with: cargo install things3"
    exit 1
fi

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
    "$THINGS3_CLI" today --limit "$limit"
else
    "$THINGS3_CLI" today
fi
