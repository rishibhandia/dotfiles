#!/bin/bash
# List projects from Things 3
# Usage: get_projects.sh

THINGS3_CLI="$HOME/.cargo/bin/things3"

if [[ ! -x "$THINGS3_CLI" ]]; then
    echo "Error: things3 CLI not found at $THINGS3_CLI"
    echo "Install with: cargo install things3"
    exit 1
fi

"$THINGS3_CLI" projects
