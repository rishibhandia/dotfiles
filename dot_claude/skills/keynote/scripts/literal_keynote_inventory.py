#!/usr/bin/env python3
"""
Keynote Inventory - Extract text content from Keynote presentations.

Uses AppleScript to reliably extract text content and structure from .key files,
outputting a JSON inventory similar to the PPTX inventory format.

Usage:
    python3 keynote_inventory.py presentation.key inventory.json

Requirements:
    - macOS with Keynote.app installed
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


def run_applescript(
    script: str,
    arguments: Sequence[Any] = (),
) -> tuple[bool, str, str]:
    """Run AppleScript from stdin and pass external values through argv."""
    try:
        result = subprocess.run(
            ["osascript", "-", *[str(value) for value in arguments]],
            input=script,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode == 0 and output.startswith("Error "):
            return False, "", output
        return result.returncode == 0, output, error
    except subprocess.TimeoutExpired:
        return False, "", "Error: AppleScript timed out"
    except Exception as e:
        return False, "", f"Error: {e}"


def document_script(body: str) -> str:
    """Wrap read-only Keynote inspection while preserving existing open state."""
    return f'''on run argv
    set deckPath to item 1 of argv
    set deckName to item 2 of argv
    set deckFile to POSIX file deckPath
    tell application "Keynote"
        set openedHere to false
        try
            if exists document deckName then
                set theDoc to document deckName
            else
                open deckFile
                set theDoc to document deckName
                set openedHere to true
            end if
            {body}
            if openedHere then close theDoc
            return resultText
        on error errMsg number errNum
            if openedHere then
                try
                    close theDoc without saving
                end try
            end if
            return "Error " & errNum & ": " & errMsg
        end try
    end tell
end run
'''


def get_document_info(key_path: str) -> tuple[bool, dict[str, int], str]:
    """Get slide count and canvas dimensions."""
    deck = Path(key_path)
    body = '''set resultText to ((count of slides of theDoc) as text) & "," & ((width of theDoc) as text) & "," & ((height of theDoc) as text)'''
    success, output, error = run_applescript(
        document_script(body), [str(deck), deck.name]
    )
    if success:
        try:
            count, width, height = (int(value.strip()) for value in output.split(","))
            return True, {"slide_count": count, "width": width, "height": height}, ""
        except (ValueError, TypeError):
            return False, {}, f"Invalid document metadata: {output}"
    return False, {}, error


def extract_slide_text(key_path: str, slide_num: int) -> tuple[bool, dict[str, Any], str]:
    """Extract semantic content, custom items, and geometry from one slide."""
    deck = Path(key_path)
    body = f'''set theSlide to slide {int(slide_num)} of theDoc
            set slideInfo to ""
            set slideInfo to slideInfo & "STATE:" & (skipped of theSlide) & ":" & (title showing of theSlide) & ":" & (body showing of theSlide) & "|||"

            try
                set titleItem to default title item of theSlide
                set titleText to object text of titleItem
                set titlePosition to position of titleItem
                set titleFont to font of object text of titleItem
                set titleSize to size of object text of titleItem
                set slideInfo to slideInfo & "TITLE:" & titleText & "|||"
                set slideInfo to slideInfo & "PLACEHOLDER:title:" & (item 1 of titlePosition) & ":" & (item 2 of titlePosition) & ":" & (width of titleItem) & ":" & (height of titleItem) & ":" & titleFont & ":" & titleSize & ":" & titleText & "|||"
            end try

            try
                set bodyItem to default body item of theSlide
                set bodyText to object text of bodyItem
                set bodyPosition to position of bodyItem
                set bodyFont to font of object text of bodyItem
                set bodySize to size of object text of bodyItem
                set slideInfo to slideInfo & "BODY:" & bodyText & "|||"
                set slideInfo to slideInfo & "PLACEHOLDER:body:" & (item 1 of bodyPosition) & ":" & (item 2 of bodyPosition) & ":" & (width of bodyItem) & ":" & (height of bodyItem) & ":" & bodyFont & ":" & bodySize & ":" & bodyText & "|||"
            end try

            try
                set masterName to name of base slide of theSlide
                set slideInfo to slideInfo & "MASTER:" & masterName & "|||"
            end try

            try
                set notesText to presenter notes of theSlide
                if notesText is not "" then set slideInfo to slideInfo & "NOTES:" & notesText & "|||"
            end try

            repeat with itemIndex from 1 to count of text items of theSlide
                try
                    set textObject to text item itemIndex of theSlide
                    set textPosition to position of textObject
                    set textFont to font of object text of textObject
                    set textSize to size of object text of textObject
                    set slideInfo to slideInfo & "TEXTITEM:" & itemIndex & ":" & (item 1 of textPosition) & ":" & (item 2 of textPosition) & ":" & (width of textObject) & ":" & (height of textObject) & ":" & (opacity of textObject) & ":" & (rotation of textObject) & ":" & (locked of textObject) & ":" & textFont & ":" & textSize & ":" & (object text of textObject) & "|||"
                end try
            end repeat

            repeat with itemIndex from 1 to count of images of theSlide
                try
                    set imageObject to image itemIndex of theSlide
                    set imagePosition to position of imageObject
                    set imageDescription to description of imageObject
                    set slideInfo to slideInfo & "IMAGE:" & itemIndex & ":" & (item 1 of imagePosition) & ":" & (item 2 of imagePosition) & ":" & (width of imageObject) & ":" & (height of imageObject) & ":" & (opacity of imageObject) & ":" & (rotation of imageObject) & ":" & (locked of imageObject) & ":" & (file name of imageObject) & ":" & imageDescription & "|||"
                end try
            end repeat

            repeat with itemIndex from 1 to count of tables of theSlide
                try
                    set tableObject to table itemIndex of theSlide
                    set tablePosition to position of tableObject
                    set slideInfo to slideInfo & "TABLE:" & itemIndex & ":" & (item 1 of tablePosition) & ":" & (item 2 of tablePosition) & ":" & (width of tableObject) & ":" & (height of tableObject) & ":" & (locked of tableObject) & ":" & (row count of tableObject) & ":" & (column count of tableObject) & ":" & (header row count of tableObject) & ":" & (header column count of tableObject) & "|||"
                end try
            end repeat

            repeat with itemIndex from 1 to count of charts of theSlide
                try
                    set chartObject to chart itemIndex of theSlide
                    set chartPosition to position of chartObject
                    set slideInfo to slideInfo & "CHART:" & itemIndex & ":" & (item 1 of chartPosition) & ":" & (item 2 of chartPosition) & ":" & (width of chartObject) & ":" & (height of chartObject) & ":" & (locked of chartObject) & "|||"
                end try
            end repeat

            set resultText to slideInfo'''
    success, output, error = run_applescript(
        document_script(body), [str(deck), deck.name]
    )

    if not success:
        return False, {}, error

    # Parse the output
    shapes = []
    items = []
    master = None
    state = {"skipped": False, "title_showing": True, "body_showing": True}

    def integer(value: str) -> int:
        return int(float(value.strip()))

    def boolean(value: str) -> bool:
        return value.strip().lower() == "true"

    parts = output.split("|||")
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith("TITLE:"):
            text = part[6:].strip()
            if text:
                shapes.append({"type": "title", "text": text})
        elif part.startswith("BODY:"):
            text = part[5:].strip()
            if text:
                shapes.append({"type": "body", "text": text})
        elif part.startswith("MASTER:"):
            master = part[7:].strip()
        elif part.startswith("NOTES:"):
            text = part[6:].strip()
            if text:
                shapes.append({"type": "notes", "text": text})
        elif part.startswith("STATE:"):
            values = part.split(":", 3)
            if len(values) == 4:
                state = {
                    "skipped": boolean(values[1]),
                    "title_showing": boolean(values[2]),
                    "body_showing": boolean(values[3]),
                }
        elif part.startswith("PLACEHOLDER:"):
            values = part.split(":", 8)
            if len(values) == 9:
                items.append({
                    "type": values[1],
                    "position": [integer(values[2]), integer(values[3])],
                    "size": [integer(values[4]), integer(values[5])],
                    "font": values[6],
                    "font_size": float(values[7]),
                    "text": values[8],
                })
        elif part.startswith("TEXTITEM:"):
            values = part.split(":", 11)
            if len(values) == 12:
                items.append({
                    "type": "text",
                    "index": integer(values[1]),
                    "position": [integer(values[2]), integer(values[3])],
                    "size": [integer(values[4]), integer(values[5])],
                    "opacity": integer(values[6]),
                    "rotation": integer(values[7]),
                    "locked": boolean(values[8]),
                    "font": values[9],
                    "font_size": float(values[10]),
                    "text": values[11],
                })
        elif part.startswith("IMAGE:"):
            values = part.split(":", 10)
            if len(values) == 11:
                items.append({
                    "type": "image",
                    "index": integer(values[1]),
                    "position": [integer(values[2]), integer(values[3])],
                    "size": [integer(values[4]), integer(values[5])],
                    "opacity": integer(values[6]),
                    "rotation": integer(values[7]),
                    "locked": boolean(values[8]),
                    "file_name": values[9],
                    "description": values[10],
                })
        elif part.startswith("TABLE:"):
            values = part.split(":")
            if len(values) == 11:
                items.append({
                    "type": "table",
                    "index": integer(values[1]),
                    "position": [integer(values[2]), integer(values[3])],
                    "size": [integer(values[4]), integer(values[5])],
                    "locked": boolean(values[6]),
                    "rows": integer(values[7]),
                    "columns": integer(values[8]),
                    "header_rows": integer(values[9]),
                    "header_columns": integer(values[10]),
                })
        elif part.startswith("CHART:"):
            values = part.split(":")
            if len(values) == 7:
                items.append({
                    "type": "chart",
                    "index": integer(values[1]),
                    "position": [integer(values[2]), integer(values[3])],
                    "size": [integer(values[4]), integer(values[5])],
                    "locked": boolean(values[6]),
                })

    placeholder_signatures = {
        (item.get("text"), tuple(item["position"]), tuple(item["size"]))
        for item in items if item["type"] in ("title", "body")
    }
    items = [
        item for item in items
        if item["type"] != "text" or (
            item.get("text"), tuple(item["position"]), tuple(item["size"])
        ) not in placeholder_signatures
    ]

    result = {"shapes": shapes, "items": items, **state}
    if master:
        result["master_slide"] = master

    return True, result, ""


def create_inventory(key_path: str) -> tuple[bool, Dict[str, Any], str]:
    """Create a full inventory of a Keynote presentation.

    Returns:
        (success, inventory_dict, error_message)
    """
    key_abs = str(Path(key_path).resolve())

    # Get document and canvas metadata.
    success, document_info, error = get_document_info(key_abs)
    if not success:
        return False, {}, error
    slide_count = document_info["slide_count"]

    if slide_count == 0:
        return True, {
            "source_file": Path(key_path).name,
            "slide_count": 0,
            "canvas": {
                "width": document_info["width"],
                "height": document_info["height"],
            },
            "slides": {}
        }, ""

    # Extract text from each slide
    slides = {}
    for i in range(1, slide_count + 1):
        success, slide_data, error = extract_slide_text(key_abs, i)
        if not success:
            print(f"Warning: Failed to extract slide {i}: {error}", file=sys.stderr)
            continue

        # Store with 0-indexed key for consistency with PPTX skill
        slides[f"slide-{i-1}"] = slide_data

    result = {
        "source_file": Path(key_path).name,
        "slide_count": slide_count,
        "canvas": {
            "width": document_info["width"],
            "height": document_info["height"],
        },
        "slides": slides
    }

    return True, result, ""


def extract_all_text_simple(key_path: str) -> tuple[bool, str, str]:
    """Extract all text from presentation as simple formatted string."""
    deck = Path(key_path).resolve()
    body = '''set allText to ""
            repeat with i from 1 to count of slides of theDoc
                set theSlide to slide i of theDoc
                set allText to allText & "Slide " & i & ":" & linefeed
                try
                    set titleText to object text of default title item of theSlide
                    set allText to allText & "  Title: " & titleText & linefeed
                end try
                try
                    set bodyText to object text of default body item of theSlide
                    set allText to allText & "  Body: " & bodyText & linefeed
                end try
                repeat with textIndex from 1 to count of text items of theSlide
                    try
                        set customText to object text of text item textIndex of theSlide
                        set allText to allText & "  Text " & textIndex & ": " & customText & linefeed
                    end try
                end repeat
                set allText to allText & linefeed
            end repeat
            set resultText to allText'''
    return run_applescript(document_script(body), [str(deck), deck.name])


def main():
    parser = argparse.ArgumentParser(
        description="Extract text inventory from Keynote presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 keynote_inventory.py presentation.key inventory.json
    python3 keynote_inventory.py presentation.key -  # Output to stdout
    python3 keynote_inventory.py --raw presentation.key  # Simple text output

The output JSON structure:
{
    "source_file": "presentation.key",
    "slide_count": 5,
    "slides": {
        "slide-0": {
            "master_slide": "Title - Center",
            "shapes": [
                {"type": "title", "text": "Slide Title"},
                {"type": "body", "text": "Bullet point 1\\nBullet point 2"}
            ]
        },
        "slide-1": {...}
    }
}

Requirements:
    - macOS with Keynote.app installed
"""
    )

    parser.add_argument("input", help="Input Keynote file (.key)")
    parser.add_argument(
        "output",
        nargs="?",
        default="-",
        help="Output JSON file (use - for stdout, default: -)"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output simple formatted text instead of JSON"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == ".key":
        print("Warning: Input file does not have .key extension", file=sys.stderr)

    if args.raw:
        # Output simple formatted text
        success, output, error = extract_all_text_simple(args.input)
        if not success:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)
        if args.output == "-":
            print(output)
        else:
            Path(args.output).write_text(output)
        sys.exit(0)

    # Create structured inventory
    success, inventory, error = create_inventory(args.input)
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Output
    json_output = json.dumps(inventory, indent=2, ensure_ascii=False)

    if args.output == "-":
        print(json_output)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output)
        print(f"Inventory saved to: {args.output}", file=sys.stderr)
        print(f"Found {inventory['slide_count']} slides", file=sys.stderr)


if __name__ == "__main__":
    main()
