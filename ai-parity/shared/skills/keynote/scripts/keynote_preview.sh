#!/bin/bash
# keynote_preview.sh — export Keynote slides as PNGs, downscale for inspection,
# and reopen the deck (the bridge export closes it).
#
# Usage:
#   keynote_preview.sh deck.key            # preview ALL slides
#   keynote_preview.sh deck.key 4 5 13     # preview only slides 4, 5, 13
#
# Prints the downscaled (<=1000 px) PNG paths, one per line — Read those.
# Never Read the full-resolution exports: any image >2000 px per dimension
# breaks image inspection in image-heavy sessions.
set -euo pipefail

DECK="$1"
shift || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DECK_ABS="$(cd "$(dirname "$DECK")" && pwd)/$(basename "$DECK")"
EXPORT_DIR="$(mktemp -d /tmp/kn_export.XXXXXX)"
OUT_DIR="$(mktemp -d /tmp/kn_preview.XXXXXX)"

python3 "$SCRIPT_DIR/keynote_bridge.py" export "$DECK_ABS" "$EXPORT_DIR/slides" --format images >/dev/null

# bridge names exports <dirname>.NNN.png inside the export dir
shopt -s nullglob
FILES=()
if [ "$#" -eq 0 ]; then
    FILES=("$EXPORT_DIR"/slides/*.png)
else
    for n in "$@"; do
        pad=$(printf "%03d" "$n")
        FILES+=("$EXPORT_DIR"/slides/*."$pad".png)
    done
fi

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "no exported slides matched" >&2
    rm -rf "$EXPORT_DIR"
    exit 1
fi

for f in "${FILES[@]}"; do
    sips -Z 1000 "$f" --out "$OUT_DIR/$(basename "$f")" >/dev/null
done
rm -rf "$EXPORT_DIR"

# export closes the deck — reopen and foreground it so the user can keep reviewing
osascript >/dev/null \
    -e 'tell application "Keynote"' \
    -e 'activate' \
    -e "open POSIX file \"$DECK_ABS\"" \
    -e 'end tell'

for f in "$OUT_DIR"/*.png; do
    echo "$f"
done
