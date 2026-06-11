---
name: keynote
description: "Apple Keynote presentation creation, editing, and PDF export. When Claude needs to work with Keynote (.key files) for: (1) Creating new presentations, (2) Editing existing presentations, (3) Exporting to PDF, (4) Template-based workflows. macOS only - requires Keynote.app installed."
---

# Keynote Presentation Skill

## Overview

Create, edit, and export Apple Keynote presentations (.key files) on macOS. This skill uses AppleScript (via osascript) for all operations.

**Requirements**: macOS with Keynote.app installed.

## Quick Reference

| Task | Command |
|------|---------|
| Export to PDF | `keynote_bridge.py export input.key output.pdf` |
| Create presentation | `keynote_bridge.py create output.key --theme "Gradient"` |
| Add slide | `keynote_bridge.py add-slide file.key --title "Title"` |
| Edit slide | `keynote_bridge.py edit-slide file.key 1 --title "New Title"` |
| Delete slide | `keynote_bridge.py delete-slide file.key 3` |
| Move slide | `keynote_bridge.py move-slide file.key 3 1` |
| Duplicate slide | `keynote_bridge.py duplicate-slide file.key 2` |
| Add image | `keynote_bridge.py add-image file.key 1 image.png` |
| Bulk replace | `keynote_bridge.py replace file.key replacements.json` |
| Extract text | `keynote_inventory.py presentation.key` |
| Preview slides (downscaled) | `keynote_preview.sh file.key 4 5 13` |

## Exporting to PDF

### Basic export
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    presentation.key output.pdf
```

### Export with quality options
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    presentation.key output.pdf --format pdf --quality best
```

### Export to other formats
```bash
# PowerPoint
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    presentation.key output.pptx --format pptx

# Images (PNG folder)
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    presentation.key slides_folder --format images

# HTML
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    presentation.key output_folder --format html
```

## Creating Presentations

### Create with theme and title
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py create \
    new_presentation.key \
    --theme "Gradient" \
    --title "My Presentation" \
    --subtitle "By Author Name"
```

### List available themes
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py list-themes
```

### List master slides for a theme
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py list-masters --theme "Gradient"
```

## Adding Slides

### Add slide at end
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py add-slide \
    presentation.key \
    --master "Title & Bullets" \
    --title "New Slide" \
    --body "• First point
• Second point
• Third point"
```

### Add slide at specific position
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py add-slide \
    presentation.key \
    --master "Title & Bullets" \
    --title "Inserted Slide" \
    --position 2
```

## Editing Slides

### Edit slide text (1-indexed)
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py edit-slide \
    presentation.key 1 \
    --title "Updated Title" \
    --body "Updated body content"
```

### Add presenter notes
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py edit-slide \
    presentation.key 1 \
    --notes "Speaker notes for this slide"
```

## Slide Operations

### Delete a slide
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py delete-slide \
    presentation.key 3
```

### Move a slide
```bash
# Move slide 3 to position 1
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py move-slide \
    presentation.key 3 1
```

### Duplicate a slide
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py duplicate-slide \
    presentation.key 2
```

### Get slide count
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py count presentation.key
```

## Adding Images

### Add image with position
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py add-image \
    presentation.key 1 image.png \
    --x 100 --y 100
```

### Add image with size
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py add-image \
    presentation.key 1 chart.png \
    --x 200 --y 150 \
    --width 500 --height 300
```

## Template-Based Workflow

Use an existing presentation as a template by duplicating and replacing text.

### Step 1: Extract inventory from template
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_inventory.py \
    template.key template-inventory.json
```

Output:
```json
{
  "source_file": "template.key",
  "slide_count": 5,
  "slides": {
    "slide-0": {
      "master_slide": "Title - Center",
      "shapes": [
        {"type": "title", "text": "Template Title"},
        {"type": "body", "text": "Template subtitle"}
      ]
    }
  }
}
```

### Step 2: Create replacement JSON
Create `replacements.json`:
```json
{
  "slides": {
    "1": {
      "title": "My New Presentation",
      "body": "Custom subtitle here"
    },
    "2": {
      "title": "Second Slide Title",
      "body": "• Point one\n• Point two\n• Point three"
    },
    "3": {
      "title": "Third Slide",
      "notes": "Remember to mention X, Y, Z"
    }
  }
}
```

### Step 3: Apply replacements
```bash
# Create new file from template
cp template.key output.key

# Apply replacements
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py replace \
    output.key replacements.json

# Or save to new file directly
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py replace \
    template.key replacements.json --output output.key
```

### Step 4: Export to PDF
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_bridge.py export \
    output.key final.pdf --quality best
```

## Reading Presentations

### Extract text as JSON
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_inventory.py \
    presentation.key inventory.json
```

### Extract text as simple format
```bash
python3 ~/.claude/skills/keynote/scripts/keynote_inventory.py \
    --raw presentation.key
```

Output:
```
Slide 1:
  Title: First Slide
  Body: Content here

Slide 2:
  Title: Second Slide
  Body: More content
```

## Common Master Slides

Master slide names vary by theme. Common ones include:

| Master | Use Case |
|--------|----------|
| `Title` | Title slide with subtitle |
| `Title - Center` | Centered title slide |
| `Title - Top` | Title at top |
| `Title & Bullets` | Title with bullet list |
| `Bullets` | Bullets only |
| `Photo` | Full slide photo |
| `Quote` | Quote layout |
| `Blank` | Empty slide |

## Common Themes

| Theme | Style |
|-------|-------|
| `Basic White` | Clean, minimal white |
| `Basic Black` | Clean, minimal dark |
| `Gradient` | Modern gradient backgrounds |
| `Modern Portfolio` | Professional portfolio style |
| `Showcase` | Bold showcase style |
| `Classic` | Traditional style |

## AppleScript Direct Usage

For operations not covered by the bridge script:

### Run custom AppleScript
```bash
osascript -e '
tell application "Keynote"
    set theDoc to open POSIX file "/path/to/presentation.key"
    -- Your commands here
    save theDoc
    close theDoc
end tell'
```

### Get all text items on a slide
```bash
osascript -e '
tell application "Keynote"
    set theDoc to open POSIX file "/path/to/presentation.key"
    tell slide 1 of theDoc
        set allItems to every text item
        repeat with t in allItems
            log object text of t
        end repeat
    end tell
    close theDoc
end tell'
```

## Error Handling

The bridge script includes error handling. Common errors:

| Error | Cause | Solution |
|-------|-------|----------|
| "document could not be opened" | Invalid path | Use absolute paths |
| "AppleScript timed out" | Keynote busy | Close other Keynote windows |
| "slide X doesn't exist" | Invalid index | Slides are 1-indexed |

## Dependencies

**System Requirements:**
- macOS 10.15+ (Catalina or later)
- Keynote.app (free from Mac App Store)
- Python 3.9+

No additional Python packages required - uses only standard library and osascript.

## Verifying Slides Efficiently (IMPORTANT)

After editing, visually verify only the slides you changed — and never
Read full-resolution exports directly. Use the one-shot helper, which
exports once, downscales to ≤1000 px, prints the paths to Read, and
reopens the deck:

```bash
bash ~/.claude/skills/keynote/scripts/keynote_preview.sh deck.key 4 5 13
# no slide numbers = all slides
```

Why downscale: image inspection rejects any PNG over 2000 px per
dimension once a session contains many images, and a single oversized
image in the conversation blocks ALL later image reads. 1920×1080
exports are safe alone but accumulate; embedded source figures often
are not. Always `sips -Z 1000 in.png --out /tmp/x.png` before Reading
anything you aren't sure about.

**Embedded figure rule:** keep source PNGs you insert with
`add-image`/`make new image` under 2000 px per dimension too (MATLAB:
`exportgraphics(fig, path, 'Resolution', 144)` for a 13.5-in figure),
or you won't be able to inspect them later.

**Export closes the document.** `keynote_bridge.py export` (any format)
closes the deck when finished. If the user is reviewing the deck live,
always reopen + activate afterward (`keynote_preview.sh` does this
automatically):

```bash
osascript -e 'tell application "Keynote"' -e 'activate' \
    -e 'open POSIX file "/abs/path/deck.key"' -e 'end tell'
```

## AppleScript Editing Pitfalls

**Phantom master shapes — never address shapes by index.** Themed decks
(university themes especially) carry invisible master-derived shapes on
every slide, so `shape 1` is usually NOT the shape you added. Always
match by content:

```applescript
repeat with i from 1 to (count of shapes of s)
    set t to (object text of shape i of s) as string
    if t contains "MARKER TEXT" then
        set object text of shape i of s to "new text"
    end if
end repeat
```

**Swapping an image in place.** Keynote embeds a copy at insert time —
if the source PNG changes on disk, the slide does NOT update. Re-embed,
matching by `file name` and preserving geometry:

```applescript
set pos to position of image 1 of s
set w to width of image 1 of s
delete image 1 of s
tell s
    set img to make new image with properties {file:POSIX file newPath}
    set width of img to w
    set position of img to pos
end tell
```

(`file name of image j` gives the original basename — use it to find
which image to swap when a slide could hold several.)

**LaTeX equations cannot be scripted.** Insert > Equation has no
AppleScript API. Add a grey placeholder shape containing the literal
LaTeX source (prefixed "EQ - Insert > Equation:") for the user to
convert manually, and duplicate the LaTeX into presenter notes.

**String splitting fails inside `tell application "Keynote"`.**
Keynote defines its own `text item` class (slide text boxes), which
shadows AppleScript's `text item delimiters` mechanism — `every text
item of myString` errors with -1728 inside the tell block. Read the
value inside the tell, do all string manipulation outside, then write
back inside a second tell.

**Setting fonts** must target `object text`, and must hit text items,
shapes, AND the default title/body items separately (wrap each in
`try` — not every slide has every item):

```applescript
set font of object text of text item j of s to "Helvetica"
set font of object text of default title item of s to "Helvetica-Bold"
```
