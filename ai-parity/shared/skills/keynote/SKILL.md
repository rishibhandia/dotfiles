---
name: keynote
description: "Create, edit, inspect, audit, preview, and export Apple Keynote presentations (.key files). Use for building or redesigning decks; editing slides, layouts, text styling, presenter notes, tables, and images; inspecting item geometry and accessibility metadata; finding overlaps, edge violations, small text, or missing alt text; applying template-based replacements; or exporting to PDF, PowerPoint, images, HTML, or movie. macOS only; requires Keynote.app."
---

# Keynote presentations

Create and manipulate `.key` decks through Keynote's installed AppleScript interface. Use the
bundled scripts for deterministic operations and visually verify every changed slide.

Requirements: macOS, Keynote.app, Python 3.9+, `osascript`, and `sips`.

## Resolve the bundled tools

Set `KEYNOTE_SKILL_DIR` to the directory containing this `SKILL.md`. Use the exact path supplied
by the current agent environment; do not assume a Claude- or Codex-specific home directory.

```bash
KEYNOTE_SKILL_DIR="/absolute/path/to/keynote"
BRIDGE="$KEYNOTE_SKILL_DIR/scripts/keynote_bridge.py"
LAYOUT="$KEYNOTE_SKILL_DIR/scripts/keynote_layout.py"
INVENTORY="$KEYNOTE_SKILL_DIR/scripts/keynote_inventory.py"
AUDIT="$KEYNOTE_SKILL_DIR/scripts/keynote_audit.py"
PREVIEW="$KEYNOTE_SKILL_DIR/scripts/keynote_preview.sh"
```

## Choose the right helper

| Need | Helper |
|---|---|
| Create/export decks; add/edit/delete/move/duplicate slides; bulk replace | `keynote_bridge.py` |
| Add or style positioned text, native tables, accessible images, layouts, and transitions | `keynote_layout.py` |
| Extract semantic content, canvas dimensions, item geometry/style, notes, and slide state | `keynote_inventory.py` |
| Flag off-canvas items, tight margins, small text, missing alt text, crowding, and overlaps | `keynote_audit.py` |
| Export selected slides, downscale them, print preview paths, and reopen the deck | `keynote_preview.sh` |

The layout helper passes external text and paths through AppleScript argv. Prefer it for custom
content containing quotes, backslashes, LaTeX, Unicode, or newlines. The bridge safely escapes
those characters for its existing commands.

## Core workflow

1. Preserve the source deck. Work on a copy unless the user explicitly wants in-place changes.
2. Inventory the deck and run the audit before substantial edits.
3. Read [references/design-workflow.md](references/design-workflow.md) for design, typography,
   accessibility, and scientific-figure guidance when creating or redesigning slides.
4. Use theme layouts and duplicated slides before rebuilding a branded composition from scratch.
5. Use bridge commands for slide structure and the layout helper for precise geometry/style.
6. Preview only changed slides and inspect every returned PNG.
7. Re-inventory and audit after geometry, typography, or accessibility changes.
8. Export the final artifact and verify its page/slide count and parseability.

For custom AppleScript, first read
[references/applescript-pitfalls.md](references/applescript-pitfalls.md).

## Inspect and audit

Create a rich JSON inventory:

```bash
python3 "$INVENTORY" deck.key inventory.json
```

The inventory includes:

- canvas width and height;
- slide count, base layout, skipped state, and title/body visibility;
- title, body, notes, and custom text;
- item position and size;
- text font and size;
- image filename, opacity, rotation, lock state, and accessibility description;
- table dimensions and header counts; and
- chart geometry.

Audit it:

```bash
python3 "$AUDIT" inventory.json
python3 "$AUDIT" inventory.json --json
python3 "$AUDIT" inventory.json --strict
```

Treat audit findings as review targets. Overlaps can be intentional, so confirm them visually.

Extract a compact text-only view when geometry is unnecessary:

```bash
python3 "$INVENTORY" --raw deck.key
```

## Create and structure a deck

List installed themes and layouts rather than assuming names:

```bash
python3 "$BRIDGE" list-themes
python3 "$BRIDGE" list-masters --theme "Gradient"
```

Create a presentation:

```bash
python3 "$BRIDGE" create deck.key \
  --theme "Gradient" \
  --title "Main claim" \
  --subtitle "Evidence and context"
```

Add a slide at the end or at a position:

```bash
python3 "$BRIDGE" add-slide deck.key \
  --master "Title & Bullets" \
  --title "Result" \
  --body $'First point\nSecond point'

python3 "$BRIDGE" add-slide deck.key \
  --master "Title - Center" \
  --title "Section" \
  --position 2
```

Edit title, body, or presenter notes:

```bash
python3 "$BRIDGE" edit-slide deck.key 2 \
  --title 'A title with "quotes" and π' \
  --body $'Line one\nLine two' \
  --notes 'Mention the uncertainty and control measurement.'
```

Reorder and manage slides:

```bash
python3 "$BRIDGE" duplicate-slide deck.key 2
python3 "$BRIDGE" move-slide deck.key 3 1
python3 "$BRIDGE" delete-slide deck.key 4
python3 "$BRIDGE" count deck.key
```

## Precise text and layout

Add a positioned, styled text box:

```bash
python3 "$LAYOUT" add-text deck.key 2 \
  --text $'Peak shift: 2.4 cm⁻¹\n95% CI: 1.8–3.0 cm⁻¹' \
  --x 90 --y 520 --width 560 --height 110 \
  --font "Avenir Next" --size 26 --color "#00AEEF"
```

Style or reposition a placeholder:

```bash
python3 "$LAYOUT" style-text deck.key 2 \
  --target title --font "Avenir Next Demi Bold" --size 42 --color "#FFFFFF"
```

Select custom text by a distinctive substring:

```bash
python3 "$LAYOUT" style-text deck.key 2 \
  --target text --match "Peak shift" \
  --x 110 --y 500 --width 600 --height 120 --size 28
```

Change the theme layout, visibility, skipped state, or transition:

```bash
python3 "$LAYOUT" configure-slide deck.key 2 \
  --layout "Title & Bullets" --show-title --show-body --unskip \
  --transition dissolve --duration 0.6
```

Supported transition names are `none`, `dissolve`, `fade-and-move`, `magic-move`, `push`,
and `wipe`. Use transitions sparingly and consistently.

## Native tables

Create a rectangular JSON array:

```json
[
  ["Metric", "Before", "After"],
  ["Accuracy", "91%", "98%"],
  ["Latency", "72 ms", "42 ms"]
]
```

Add it as a native Keynote table:

```bash
python3 "$LAYOUT" add-table deck.key 2 table.json \
  --x 620 --y 430 --width 330 --height 220 \
  --header-rows 1 --font "Avenir Next" --size 17
```

Keep tables compact. Split or simplify them instead of shrinking type below readable sizes.

## Accessible images

Add an image with deterministic geometry and VoiceOver description:

```bash
python3 "$LAYOUT" add-image deck.key 2 figure.png \
  --x 520 --y 180 --width 420 --height 300 \
  --description "Measured spectrum with a peak at 2.1 THz" \
  --opacity 100 --rotation 0 --locked
```

Use the image index from the rich inventory to update an existing image in place. Locked images
are temporarily unlocked and their prior lock state is restored unless explicitly changed:

```bash
python3 "$LAYOUT" style-image deck.key 2 --index 1 \
  --x 560 --y 190 --width 390 --height 280 \
  --description "Updated spectrum with confidence interval" \
  --opacity 100 --rotation 0 --locked
```

Use the legacy bridge only when the extra metadata is unnecessary:

```bash
python3 "$BRIDGE" add-image deck.key 2 figure.png \
  --x 520 --y 180 --width 420 --height 300
```

Keynote embeds images at insertion time. Reinsert a changed source image; it does not refresh
automatically from disk.

## Template replacement

Inventory the template, duplicate it, and prepare replacements keyed by 1-based slide number:

```json
{
  "slides": {
    "1": {"title": "New title", "body": "Subtitle"},
    "2": {"title": "Result", "body": "Evidence", "notes": "Explain the control."}
  }
}
```

Apply without overwriting the template:

```bash
python3 "$BRIDGE" replace template.key replacements.json --output deck.key
```

Duplicate whole slides when preserving exact theme styling. Keynote cannot reliably duplicate an
individual shape through AppleScript.

## Preview and export

Preview changed slides only:

```bash
bash "$PREVIEW" deck.key 2 4 7
# Omit slide numbers to preview all slides.
```

The helper exports once, downsizes previews to at most 1000 px, prints their paths, and reopens
the deck. Inspect those images; do not load uncertain full-resolution exports directly.

Export deliverables:

```bash
python3 "$BRIDGE" export deck.key final.pdf --format pdf --quality best
python3 "$BRIDGE" export deck.key final.pptx --format pptx
python3 "$BRIDGE" export deck.key slides --format images
python3 "$BRIDGE" export deck.key web --format html
```

The bridge export closes the deck. Use the preview helper when the user is actively reviewing it.

## Known limits

- Keynote's Insert > Equation feature has no supported AppleScript API. Use a labeled placeholder
  and presenter note for manual equation insertion.
- Build animations are not exposed with enough control for a reliable general helper.
- Shape fill and detailed line styling are limited in the installed scripting dictionary.
- For publication-quality data plots, create and verify the figure in the scientific plotting
  environment, then insert the resulting vector or appropriately sized raster asset.
