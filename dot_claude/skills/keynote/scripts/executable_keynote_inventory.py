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
from typing import Any, Dict, List, Optional


def run_applescript(script: str) -> tuple[bool, str, str]:
    """Run AppleScript and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Error: AppleScript timed out"
    except Exception as e:
        return False, "", f"Error: {e}"


def get_slide_count(key_path: str) -> tuple[bool, int, str]:
    """Get the number of slides in a presentation."""
    script = f'''
tell application "Keynote"
    set theDoc to open POSIX file "{key_path}"
    set slideCount to count of slides of theDoc
    close theDoc
    return slideCount
end tell
'''
    success, output, error = run_applescript(script)
    if success:
        try:
            return True, int(output), ""
        except ValueError:
            return False, 0, f"Invalid slide count: {output}"
    return False, 0, error


def extract_slide_text(key_path: str, slide_num: int) -> tuple[bool, Dict[str, Any], str]:
    """Extract text from a specific slide (1-indexed).

    Returns a dictionary with shape information.
    """
    script = f'''
tell application "Keynote"
    set theDoc to open POSIX file "{key_path}"
    set theSlide to slide {slide_num} of theDoc

    set slideInfo to ""

    -- Get default title item text if exists
    try
        set titleText to object text of default title item of theSlide
        set slideInfo to slideInfo & "TITLE:" & titleText & "|||"
    end try

    -- Get default body item text if exists
    try
        set bodyText to object text of default body item of theSlide
        set slideInfo to slideInfo & "BODY:" & bodyText & "|||"
    end try

    -- Get master slide name
    try
        set masterName to name of base slide of theSlide
        set slideInfo to slideInfo & "MASTER:" & masterName & "|||"
    end try

    -- Get presenter notes if exists
    try
        set notesText to presenter notes of theSlide
        if notesText is not "" then
            set slideInfo to slideInfo & "NOTES:" & notesText & "|||"
        end if
    end try

    close theDoc
    return slideInfo
end tell
'''
    success, output, error = run_applescript(script)

    if not success:
        return False, {}, error

    # Parse the output
    shapes = []
    master = None

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

    result = {"shapes": shapes}
    if master:
        result["master_slide"] = master

    return True, result, ""


def create_inventory(key_path: str) -> tuple[bool, Dict[str, Any], str]:
    """Create a full inventory of a Keynote presentation.

    Returns:
        (success, inventory_dict, error_message)
    """
    key_abs = str(Path(key_path).resolve())

    # Get slide count
    success, slide_count, error = get_slide_count(key_abs)
    if not success:
        return False, {}, error

    if slide_count == 0:
        return True, {
            "source_file": Path(key_path).name,
            "slide_count": 0,
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
        "slides": slides
    }

    return True, result, ""


def extract_all_text_simple(key_path: str) -> tuple[bool, str, str]:
    """Extract all text from presentation as simple formatted string."""
    key_abs = str(Path(key_path).resolve())

    script = f'''
tell application "Keynote"
    set theDoc to open POSIX file "{key_abs}"
    set allText to ""

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

        set allText to allText & linefeed
    end repeat

    close theDoc
    return allText
end tell
'''
    return run_applescript(script)


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
