#!/usr/bin/env python3
"""
Keynote Bridge - Python wrapper for AppleScript Keynote operations.

Provides a command-line interface for common Keynote operations:
- export: Export presentations to PDF, PPTX, or images
- create: Create new presentations
- add-slide: Add slides to existing presentations
- edit-slide: Edit text on existing slides
- delete-slide: Delete slides from presentations
- move-slide: Reorder slides in presentations
- add-image: Add images to slides
- replace: Bulk text replacement from JSON file
- list-themes: List available Keynote themes
- list-masters: List master slides for a theme

Usage:
    python3 keynote_bridge.py export input.key output.pdf --format pdf
    python3 keynote_bridge.py create output.key --theme "Gradient" --title "My Title"
    python3 keynote_bridge.py add-slide presentation.key --master "Title & Bullets" --title "Slide Title"
    python3 keynote_bridge.py edit-slide presentation.key 1 --title "New Title" --body "New content"
    python3 keynote_bridge.py delete-slide presentation.key 3
    python3 keynote_bridge.py move-slide presentation.key 3 1
    python3 keynote_bridge.py add-image presentation.key 1 image.png --x 100 --y 100 --width 400
    python3 keynote_bridge.py replace presentation.key replacements.json --output new.key
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any


def applescript_string(value: Any) -> str:
    """Return a safely escaped AppleScript string literal."""
    escaped = str(value)
    escaped = escaped.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    return f'"{escaped}"'


def run_applescript(script: str, timeout: int = 60) -> tuple[bool, str]:
    """Run AppleScript and return (success, output/error)."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Error: AppleScript timed out"
    except Exception as e:
        return False, f"Error: {e}"


def export_presentation(
    input_path: str,
    output_path: str,
    format: str = "pdf",
    quality: str = "best"
) -> tuple[bool, str]:
    """Export a Keynote presentation to various formats."""
    input_abs = str(Path(input_path).resolve())
    output_abs = str(Path(output_path).resolve())

    format_map = {
        "pdf": "PDF",
        "pptx": "Microsoft PowerPoint",
        "html": "HTML",
        "images": "slide images",
        "movie": "QuickTime movie",
    }

    quality_map = {
        "good": "Good",
        "better": "Better",
        "best": "Best",
    }

    if format not in format_map:
        return False, f"Unknown format: {format}. Use: {list(format_map.keys())}"

    export_format = format_map[format]
    pdf_quality = quality_map.get(quality, "Best")

    if format == "pdf":
        props = f"with properties {{PDF image quality:{pdf_quality}}}"
    elif format == "images":
        props = "with properties {image format:PNG}"
    else:
        props = ""

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(input_abs)}
        export theDoc to POSIX file {applescript_string(output_abs)} as {export_format} {props}
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Exported to {output_path}"
    elif success:
        return False, output
    else:
        return False, output


def create_presentation(
    output_path: str,
    theme: str = "Gradient",
    title: Optional[str] = None,
    subtitle: Optional[str] = None
) -> tuple[bool, str]:
    """Create a new Keynote presentation."""
    output_abs = str(Path(output_path).resolve())

    title_script = ""
    if title:
        title_script += f'set object text of default title item to {applescript_string(title)}\n'
    if subtitle:
        title_script += f'set object text of default body item to {applescript_string(subtitle)}\n'

    slide_config = ""
    if title_script:
        slide_config = f'''
        tell slide 1 of theDoc
            {title_script}
        end tell
'''

    script = f'''
try
    tell application "Keynote"
        set theDoc to make new document with properties {{document theme:theme {applescript_string(theme)}}}
        {slide_config}
        save theDoc in POSIX file {applescript_string(output_abs)}
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Created {output_path}"
    elif success:
        return False, output
    else:
        return False, output


def add_slide(
    file_path: str,
    master: str = "Title & Bullets",
    title: Optional[str] = None,
    body: Optional[str] = None,
    position: Optional[int] = None
) -> tuple[bool, str]:
    """Add a slide to an existing presentation."""
    file_abs = str(Path(file_path).resolve())

    content_script = ""
    if title:
        content_script += f'set object text of default title item to {applescript_string(title)}\n'
    if body:
        content_script += f'set object text of default body item to {applescript_string(body)}\n'

    slide_content = ""
    if content_script:
        slide_content = f'''
            tell newSlide
                {content_script}
            end tell
'''

    # Position handling
    if position:
        make_slide = f'set newSlide to make new slide at after slide {position - 1} with properties {{base slide:master slide {applescript_string(master)}}}'
        if position == 1:
            make_slide = f'set newSlide to make new slide at beginning with properties {{base slide:master slide {applescript_string(master)}}}'
    else:
        make_slide = f'set newSlide to make new slide with properties {{base slide:master slide {applescript_string(master)}}}'

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        tell theDoc
            {make_slide}
            {slide_content}
        end tell
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        pos_msg = f" at position {position}" if position else ""
        return True, f"Added slide{pos_msg} to {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def edit_slide(
    file_path: str,
    slide_num: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    notes: Optional[str] = None
) -> tuple[bool, str]:
    """Edit text on an existing slide (1-indexed)."""
    file_abs = str(Path(file_path).resolve())

    edit_commands = []
    if title is not None:
        edit_commands.append(f'set object text of default title item to {applescript_string(title)}')
    if body is not None:
        edit_commands.append(f'set object text of default body item to {applescript_string(body)}')
    if notes is not None:
        edit_commands.append(f'set presenter notes to {applescript_string(notes)}')

    if not edit_commands:
        return False, "No edits specified. Use --title, --body, or --notes"

    edit_script = "\n            ".join(edit_commands)

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        tell slide {slide_num} of theDoc
            {edit_script}
        end tell
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Edited slide {slide_num} in {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def delete_slide(file_path: str, slide_num: int) -> tuple[bool, str]:
    """Delete a slide from a presentation (1-indexed)."""
    file_abs = str(Path(file_path).resolve())

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        delete slide {slide_num} of theDoc
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Deleted slide {slide_num} from {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def move_slide(file_path: str, from_pos: int, to_pos: int) -> tuple[bool, str]:
    """Move a slide from one position to another (1-indexed)."""
    file_abs = str(Path(file_path).resolve())

    # Determine move direction
    if to_pos == 1:
        move_cmd = f"move slide {from_pos} of theDoc to beginning of theDoc"
    elif to_pos < from_pos:
        move_cmd = f"move slide {from_pos} of theDoc to before slide {to_pos} of theDoc"
    else:
        move_cmd = f"move slide {from_pos} of theDoc to after slide {to_pos} of theDoc"

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        {move_cmd}
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Moved slide {from_pos} to position {to_pos} in {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def add_image(
    file_path: str,
    slide_num: int,
    image_path: str,
    x: int = 100,
    y: int = 100,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> tuple[bool, str]:
    """Add an image to a slide at specified position."""
    file_abs = str(Path(file_path).resolve())
    image_abs = str(Path(image_path).resolve())

    # Build size properties
    size_props = ""
    if width:
        size_props += f", width:{width}"
    if height:
        size_props += f", height:{height}"

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        tell slide {slide_num} of theDoc
            set theImage to make new image with properties {{file:POSIX file {applescript_string(image_abs)}, position:{{{x}, {y}}}{size_props}}}
        end tell
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Added image to slide {slide_num} in {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def duplicate_slide(file_path: str, slide_num: int) -> tuple[bool, str]:
    """Duplicate a slide in a presentation (1-indexed)."""
    file_abs = str(Path(file_path).resolve())

    script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        duplicate slide {slide_num} of theDoc
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    success, output = run_applescript(script)

    if success and output == "Success":
        return True, f"Duplicated slide {slide_num} in {file_path}"
    elif success:
        return False, output
    else:
        return False, output


def replace_from_json(
    file_path: str,
    json_path: str,
    output_path: Optional[str] = None
) -> tuple[bool, str]:
    """Replace text in slides based on a JSON file.

    JSON format:
    {
        "slides": {
            "1": {
                "title": "New Title",
                "body": "New body text"
            },
            "2": {
                "title": "Slide 2 Title"
            }
        }
    }
    """
    file_abs = str(Path(file_path).resolve())
    output_abs = str(Path(output_path).resolve()) if output_path else file_abs

    # Load JSON
    try:
        with open(json_path, 'r') as f:
            replacements = json.load(f)
    except Exception as e:
        return False, f"Failed to load JSON: {e}"

    slides_data = replacements.get("slides", {})
    if not slides_data:
        return False, "No slides data found in JSON"

    # Build AppleScript for each slide
    edit_blocks = []
    for slide_num, content in slides_data.items():
        try:
            slide_index = int(slide_num)
        except (TypeError, ValueError):
            return False, f"Invalid slide number in JSON: {slide_num!r}"
        if slide_index < 1 or str(slide_index) != str(slide_num):
            return False, f"Invalid slide number in JSON: {slide_num!r}"
        if not isinstance(content, dict):
            return False, f"Slide {slide_num} replacement must be an object"
        edit_commands = []
        if "title" in content and content["title"] is not None:
            edit_commands.append(
                f'set object text of default title item to {applescript_string(content["title"])}'
            )
        if "body" in content and content["body"] is not None:
            edit_commands.append(
                f'set object text of default body item to {applescript_string(content["body"])}'
            )
        if "notes" in content and content["notes"] is not None:
            edit_commands.append(
                f'set presenter notes to {applescript_string(content["notes"])}'
            )

        if edit_commands:
            edit_script = "\n                ".join(edit_commands)
            edit_blocks.append(f'''
            tell slide {slide_index} of theDoc
                {edit_script}
            end tell''')

    if not edit_blocks:
        return False, "No valid edits found in JSON"

    all_edits = "\n".join(edit_blocks)

    # If output is different from input, duplicate first
    if output_path and output_path != file_path:
        script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        {all_edits}
        save theDoc in POSIX file {applescript_string(output_abs)}
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''
    else:
        script = f'''
try
    tell application "Keynote"
        set theDoc to open POSIX file {applescript_string(file_abs)}
        {all_edits}
        save theDoc
        close theDoc
        return "Success"
    end tell
on error errMsg number errNum
    return "Error " & errNum & ": " & errMsg
end try
'''

    success, output = run_applescript(script, timeout=120)

    if success and output == "Success":
        slides_edited = len([s for s in slides_data.values() if s])
        dest = output_path if output_path else file_path
        return True, f"Replaced text in {slides_edited} slides, saved to {dest}"
    elif success:
        return False, output
    else:
        return False, output


def list_themes() -> tuple[bool, str]:
    """List all available Keynote themes."""
    script = '''
tell application "Keynote"
    return name of every theme
end tell
'''
    return run_applescript(script)


def list_masters(theme: str = "Gradient") -> tuple[bool, str]:
    """List master slides for a given theme."""
    script = f'''
tell application "Keynote"
    set theDoc to make new document with properties {{document theme:theme {applescript_string(theme)}}}
    set masterNames to name of every master slide of theDoc
    close theDoc without saving
    return masterNames
end tell
'''
    return run_applescript(script)


def get_slide_count(file_path: str) -> tuple[bool, str]:
    """Get the number of slides in a presentation."""
    file_abs = str(Path(file_path).resolve())

    script = f'''
tell application "Keynote"
    set theDoc to open POSIX file {applescript_string(file_abs)}
    set slideCount to count of slides of theDoc
    close theDoc
    return slideCount
end tell
'''
    return run_applescript(script)


def main():
    parser = argparse.ArgumentParser(
        description="Keynote Bridge - Python wrapper for AppleScript Keynote operations"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export presentation")
    export_parser.add_argument("input", help="Input .key file")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument(
        "--format", "-f",
        choices=["pdf", "pptx", "html", "images", "movie"],
        default="pdf",
        help="Export format (default: pdf)"
    )
    export_parser.add_argument(
        "--quality", "-q",
        choices=["good", "better", "best"],
        default="best",
        help="PDF quality (default: best)"
    )

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new presentation")
    create_parser.add_argument("output", help="Output .key file path")
    create_parser.add_argument("--theme", "-t", default="Gradient", help="Theme name")
    create_parser.add_argument("--title", help="Title slide text")
    create_parser.add_argument("--subtitle", help="Subtitle text")

    # Add slide command
    add_slide_parser = subparsers.add_parser("add-slide", help="Add slide to presentation")
    add_slide_parser.add_argument("file", help="Presentation .key file")
    add_slide_parser.add_argument("--master", "-m", default="Title & Bullets", help="Master slide name")
    add_slide_parser.add_argument("--title", help="Slide title")
    add_slide_parser.add_argument("--body", help="Slide body text")
    add_slide_parser.add_argument("--position", "-p", type=int, help="Position to insert (1-indexed)")

    # Edit slide command
    edit_parser = subparsers.add_parser("edit-slide", help="Edit text on existing slide")
    edit_parser.add_argument("file", help="Presentation .key file")
    edit_parser.add_argument("slide", type=int, help="Slide number (1-indexed)")
    edit_parser.add_argument("--title", help="New title text")
    edit_parser.add_argument("--body", help="New body text")
    edit_parser.add_argument("--notes", help="New presenter notes")

    # Delete slide command
    delete_parser = subparsers.add_parser("delete-slide", help="Delete a slide")
    delete_parser.add_argument("file", help="Presentation .key file")
    delete_parser.add_argument("slide", type=int, help="Slide number to delete (1-indexed)")

    # Move slide command
    move_parser = subparsers.add_parser("move-slide", help="Move slide to new position")
    move_parser.add_argument("file", help="Presentation .key file")
    move_parser.add_argument("from_pos", type=int, help="Current slide position (1-indexed)")
    move_parser.add_argument("to_pos", type=int, help="New slide position (1-indexed)")

    # Duplicate slide command
    dup_parser = subparsers.add_parser("duplicate-slide", help="Duplicate a slide")
    dup_parser.add_argument("file", help="Presentation .key file")
    dup_parser.add_argument("slide", type=int, help="Slide number to duplicate (1-indexed)")

    # Add image command
    img_parser = subparsers.add_parser("add-image", help="Add image to slide")
    img_parser.add_argument("file", help="Presentation .key file")
    img_parser.add_argument("slide", type=int, help="Slide number (1-indexed)")
    img_parser.add_argument("image", help="Image file path")
    img_parser.add_argument("--x", type=int, default=100, help="X position (default: 100)")
    img_parser.add_argument("--y", type=int, default=100, help="Y position (default: 100)")
    img_parser.add_argument("--width", "-w", type=int, help="Image width")
    img_parser.add_argument("--height", "-H", type=int, help="Image height")

    # Replace from JSON command
    replace_parser = subparsers.add_parser("replace", help="Bulk text replacement from JSON")
    replace_parser.add_argument("file", help="Presentation .key file")
    replace_parser.add_argument("json", help="JSON file with replacements")
    replace_parser.add_argument("--output", "-o", help="Output file (default: overwrite input)")

    # List themes command
    subparsers.add_parser("list-themes", help="List available themes")

    # List masters command
    masters_parser = subparsers.add_parser("list-masters", help="List master slides for theme")
    masters_parser.add_argument("--theme", "-t", default="Gradient", help="Theme name")

    # Slide count command
    count_parser = subparsers.add_parser("count", help="Get slide count")
    count_parser.add_argument("file", help="Presentation .key file")

    args = parser.parse_args()

    if args.command == "export":
        success, msg = export_presentation(
            args.input, args.output, args.format, args.quality
        )
    elif args.command == "create":
        success, msg = create_presentation(
            args.output, args.theme, args.title, args.subtitle
        )
    elif args.command == "add-slide":
        success, msg = add_slide(
            args.file, args.master, args.title, args.body, args.position
        )
    elif args.command == "edit-slide":
        success, msg = edit_slide(
            args.file, args.slide, args.title, args.body, args.notes
        )
    elif args.command == "delete-slide":
        success, msg = delete_slide(args.file, args.slide)
    elif args.command == "move-slide":
        success, msg = move_slide(args.file, args.from_pos, args.to_pos)
    elif args.command == "duplicate-slide":
        success, msg = duplicate_slide(args.file, args.slide)
    elif args.command == "add-image":
        success, msg = add_image(
            args.file, args.slide, args.image,
            args.x, args.y, args.width, args.height
        )
    elif args.command == "replace":
        success, msg = replace_from_json(args.file, args.json, args.output)
    elif args.command == "list-themes":
        success, msg = list_themes()
    elif args.command == "list-masters":
        success, msg = list_masters(args.theme)
    elif args.command == "count":
        success, msg = get_slide_count(args.file)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    print(msg)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
