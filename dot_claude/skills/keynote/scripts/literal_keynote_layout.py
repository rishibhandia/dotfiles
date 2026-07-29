#!/usr/bin/env python3
"""Precise, argv-safe layout operations for Apple Keynote presentations."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


TRANSITIONS = {
    "none": "no transition effect",
    "dissolve": "dissolve",
    "fade-and-move": "fade and move",
    "magic-move": "magic move",
    "push": "push",
    "wipe": "wipe",
}


class LayoutError(ValueError):
    """A user-facing layout validation error."""


def run_applescript(
    script: str,
    arguments: Sequence[Any],
    timeout: int = 120,
) -> tuple[bool, str]:
    """Run AppleScript from stdin and pass all external values through argv."""
    try:
        result = subprocess.run(
            ["osascript", "-", *[str(value) for value in arguments]],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "AppleScript timed out"
    except OSError as exc:
        return False, str(exc)
    if result.returncode:
        return False, result.stderr.strip() or result.stdout.strip()
    output = result.stdout.strip()
    if output.startswith("Error "):
        return False, output
    return True, output or "Success"


def normalized_deck(path: str) -> tuple[Path, list[str]]:
    deck = Path(path).expanduser().resolve()
    if not deck.exists():
        raise LayoutError(f"presentation not found: {path}")
    if deck.suffix.lower() != ".key":
        raise LayoutError(f"presentation must be a .key file: {path}")
    return deck, [str(deck), deck.name]


def hex_color(value: str) -> tuple[int, int, int]:
    """Convert #RRGGBB to Keynote's 16-bit RGB channel values."""
    raw = value.strip().removeprefix("#")
    if len(raw) != 6:
        raise LayoutError("color must use #RRGGBB")
    try:
        channels = tuple(int(raw[index:index + 2], 16) * 257 for index in (0, 2, 4))
    except ValueError as exc:
        raise LayoutError("color must use #RRGGBB") from exc
    return channels


def bounded(value: int, minimum: int, maximum: int, label: str) -> int:
    if not minimum <= value <= maximum:
        raise LayoutError(f"{label} must be between {minimum} and {maximum}")
    return value


def mutation_script(assignments: Sequence[str], body: str) -> str:
    assignment_text = "\n    ".join(assignments)
    return f'''on run argv
    set deckPath to item 1 of argv
    set deckName to item 2 of argv
    set deckFile to POSIX file deckPath
    {assignment_text}
    tell application "Keynote"
        set openedHere to false
        try
            if exists document deckName then
                set d to document deckName
            else
                open deckFile
                set d to document deckName
                set openedHere to true
            end if
            {body}
            save d
            if openedHere then close d
            return "Success"
        on error errMsg number errNum
            if openedHere then
                try
                    close d without saving
                end try
            end if
            return "Error " & errNum & ": " & errMsg
        end try
    end tell
end run
'''


def add_text(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    red, green, blue = hex_color(args.color)
    values.extend([
        args.slide, args.text, args.x, args.y, args.width, args.height,
        args.font, args.size, red, green, blue, args.opacity, args.rotation,
        int(args.locked),
    ])
    assignments = [
        "set slideNumber to (item 3 of argv) as integer",
        "set contentText to item 4 of argv",
        "set xPosition to (item 5 of argv) as integer",
        "set yPosition to (item 6 of argv) as integer",
        "set itemWidth to (item 7 of argv) as integer",
        "set itemHeight to (item 8 of argv) as integer",
        "set fontName to item 9 of argv",
        "set fontSize to (item 10 of argv) as real",
        "set redValue to (item 11 of argv) as integer",
        "set greenValue to (item 12 of argv) as integer",
        "set blueValue to (item 13 of argv) as integer",
        "set itemOpacity to (item 14 of argv) as integer",
        "set itemRotation to (item 15 of argv) as integer",
        "set itemLocked to ((item 16 of argv) as integer) is 1",
    ]
    body = '''tell slide slideNumber of d
                set newText to make new text item with properties {object text:contentText, position:{xPosition, yPosition}, width:itemWidth, height:itemHeight, opacity:itemOpacity, rotation:itemRotation}
                set font of object text of newText to fontName
                set size of object text of newText to fontSize
                set color of object text of newText to {redValue, greenValue, blueValue}
                set locked of newText to itemLocked
            end tell'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    return success, f"Added text to slide {args.slide} in {deck}" if success else output


def style_text(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    values.extend([args.slide, args.target, args.match or ""])
    assignments = [
        "set slideNumber to (item 3 of argv) as integer",
        "set targetKind to item 4 of argv",
        "set matchText to item 5 of argv",
    ]
    commands = []

    def add_value(name: str, value: Any, coercion: str, command: str) -> None:
        if value is None:
            return
        values.append(value)
        index = len(values)
        assignments.append(f"set {name} to (item {index} of argv){coercion}")
        commands.append(command)

    if args.font is not None:
        values.append(args.font)
        assignments.append(f"set fontName to item {len(values)} of argv")
        commands.append("set font of object text of matchedItem to fontName")
    add_value("fontSize", args.size, " as real", "set size of object text of matchedItem to fontSize")
    if args.color is not None:
        for name, channel in zip(("redValue", "greenValue", "blueValue"), hex_color(args.color)):
            add_value(name, channel, " as integer", "")
        commands = [command for command in commands if command]
        commands.append("set color of object text of matchedItem to {redValue, greenValue, blueValue}")
    if args.x is not None or args.y is not None:
        if args.x is not None:
            values.append(args.x)
            assignments.append(f"set xPosition to (item {len(values)} of argv) as integer")
        if args.y is not None:
            values.append(args.y)
            assignments.append(f"set yPosition to (item {len(values)} of argv) as integer")
        commands.append("set currentPosition to position of matchedItem")
        if args.x is None:
            commands.append("set xPosition to item 1 of currentPosition")
        if args.y is None:
            commands.append("set yPosition to item 2 of currentPosition")
        commands.append("set position of matchedItem to {xPosition, yPosition}")
    add_value("itemWidth", args.width, " as integer", "set width of matchedItem to itemWidth")
    add_value("itemHeight", args.height, " as integer", "set height of matchedItem to itemHeight")
    add_value("itemOpacity", args.opacity, " as integer", "set opacity of matchedItem to itemOpacity")
    add_value("itemRotation", args.rotation, " as integer", "set rotation of matchedItem to itemRotation")
    if not commands:
        raise LayoutError("specify at least one style or geometry option")
    command_text = "\n                ".join(commands)
    body = f'''tell slide slideNumber of d
                if targetKind is "title" then
                    set matchedItem to default title item
                else if targetKind is "body" then
                    set matchedItem to default body item
                else
                    set matchedItem to missing value
                    repeat with candidate in text items
                        if (object text of candidate as text) contains matchText then
                            set matchedItem to candidate
                            exit repeat
                        end if
                    end repeat
                    if matchedItem is missing value then error "No custom text item contains the requested match text"
                end if
                set originalLockState to locked of matchedItem
                if originalLockState then set locked of matchedItem to false
                {command_text}
                set locked of matchedItem to originalLockState
            end tell'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    target_label = "custom text" if args.target == "text" else f"{args.target} text"
    return success, f"Styled {target_label} on slide {args.slide} in {deck}" if success else output


def load_table(path: str) -> list[list[Any]]:
    source = Path(path).expanduser().resolve()
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LayoutError(f"cannot read table JSON: {exc}") from exc
    if not isinstance(value, list) or not value or not all(isinstance(row, list) for row in value):
        raise LayoutError("table JSON must be a non-empty array of row arrays")
    width = len(value[0])
    if width == 0 or any(len(row) != width for row in value):
        raise LayoutError("table rows must be non-empty and rectangular")
    if len(value) > 100 or width > 30:
        raise LayoutError("table is limited to 100 rows and 30 columns")
    for row in value:
        for cell in row:
            if cell is not None and not isinstance(cell, (str, int, float, bool)):
                raise LayoutError("table cells must be strings, numbers, booleans, or null")
    return value


def add_table(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    rows = load_table(args.json)
    row_count = len(rows)
    column_count = len(rows[0])
    if args.header_rows > row_count or args.header_columns > column_count:
        raise LayoutError("header counts cannot exceed table dimensions")
    values.extend([
        args.slide, args.x, args.y, args.width, args.height, row_count,
        column_count, args.header_rows, args.header_columns, args.font, args.size,
    ])
    assignments = [
        "set slideNumber to (item 3 of argv) as integer",
        "set xPosition to (item 4 of argv) as integer",
        "set yPosition to (item 5 of argv) as integer",
        "set itemWidth to (item 6 of argv) as integer",
        "set itemHeight to (item 7 of argv) as integer",
        "set rowCount to (item 8 of argv) as integer",
        "set columnCount to (item 9 of argv) as integer",
        "set headerRows to (item 10 of argv) as integer",
        "set headerColumns to (item 11 of argv) as integer",
        "set fontName to item 12 of argv",
        "set fontSize to (item 13 of argv) as real",
    ]
    cell_commands = []
    for row_index, row in enumerate(rows, 1):
        for column_index, cell in enumerate(row, 1):
            values.append("" if cell is None else cell)
            arg_index = len(values)
            variable = f"cellValue{row_index}_{column_index}"
            assignments.append(f"set {variable} to item {arg_index} of argv")
            cell_commands.append(
                f"set value of cell {column_index} of row {row_index} of newTable to {variable}"
            )
    cells = "\n                ".join(cell_commands)
    body = f'''tell slide slideNumber of d
                set newTable to make new table with properties {{row count:rowCount, column count:columnCount, header row count:headerRows, header column count:headerColumns, position:{{xPosition, yPosition}}, width:itemWidth, height:itemHeight}}
                {cells}
                set font name of cell range of newTable to fontName
                set font size of cell range of newTable to fontSize
            end tell'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    return success, f"Added {row_count}x{column_count} table to slide {args.slide} in {deck}" if success else output


def add_image(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    image = Path(args.image).expanduser().resolve()
    if not image.is_file():
        raise LayoutError(f"image not found: {args.image}")
    values.extend([
        args.slide, str(image), args.x, args.y, args.width, args.height,
        args.description or "", args.opacity, args.rotation, int(args.locked),
    ])
    assignments = [
        "set slideNumber to (item 3 of argv) as integer",
        "set imagePath to item 4 of argv",
        "set imageFile to POSIX file imagePath",
        "set xPosition to (item 5 of argv) as integer",
        "set yPosition to (item 6 of argv) as integer",
        "set itemWidth to (item 7 of argv) as integer",
        "set itemHeight to (item 8 of argv) as integer",
        "set altText to item 9 of argv",
        "set itemOpacity to (item 10 of argv) as integer",
        "set itemRotation to (item 11 of argv) as integer",
        "set itemLocked to ((item 12 of argv) as integer) is 1",
    ]
    body = '''tell slide slideNumber of d
                set newImage to make new image with properties {file:imageFile, position:{xPosition, yPosition}, width:itemWidth, height:itemHeight, opacity:itemOpacity, rotation:itemRotation}
                if altText is not "" then set description of newImage to altText
                set locked of newImage to itemLocked
            end tell'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    return success, f"Added image to slide {args.slide} in {deck}" if success else output


def style_image(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    values.extend([args.slide, args.index])
    assignments = [
        "set slideNumber to (item 3 of argv) as integer",
        "set imageIndex to (item 4 of argv) as integer",
    ]
    commands = []

    def add_value(name: str, value: Any, coercion: str, command: str) -> None:
        if value is None:
            return
        values.append(value)
        assignments.append(f"set {name} to (item {len(values)} of argv){coercion}")
        commands.append(command)

    if args.x is not None or args.y is not None:
        if args.x is not None:
            values.append(args.x)
            assignments.append(f"set xPosition to (item {len(values)} of argv) as integer")
        if args.y is not None:
            values.append(args.y)
            assignments.append(f"set yPosition to (item {len(values)} of argv) as integer")
        commands.append("set currentPosition to position of targetImage")
        if args.x is None:
            commands.append("set xPosition to item 1 of currentPosition")
        if args.y is None:
            commands.append("set yPosition to item 2 of currentPosition")
        commands.append("set position of targetImage to {xPosition, yPosition}")
    add_value("itemWidth", args.width, " as integer", "set width of targetImage to itemWidth")
    add_value("itemHeight", args.height, " as integer", "set height of targetImage to itemHeight")
    add_value("itemOpacity", args.opacity, " as integer", "set opacity of targetImage to itemOpacity")
    add_value("itemRotation", args.rotation, " as integer", "set rotation of targetImage to itemRotation")
    if args.description is not None:
        values.append(args.description)
        assignments.append(f"set altText to item {len(values)} of argv")
        commands.append("set description of targetImage to altText")
    if not commands and args.locked is None:
        raise LayoutError("specify at least one image style, geometry, description, or lock option")
    command_text = "\n            ".join(commands)
    if args.locked is None:
        final_lock = "set locked of targetImage to originalLockState"
    else:
        final_lock = f"set locked of targetImage to {str(args.locked).lower()}"
    body = f'''set targetImage to image imageIndex of slide slideNumber of d
            set originalLockState to locked of targetImage
            if originalLockState then set locked of targetImage to false
            {command_text}
            {final_lock}'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    return success, f"Styled image {args.index} on slide {args.slide} in {deck}" if success else output


def configure_slide(args: argparse.Namespace) -> tuple[bool, str]:
    deck, values = normalized_deck(args.file)
    values.append(args.slide)
    assignments = ["set slideNumber to (item 3 of argv) as integer"]
    commands = []
    if args.layout is not None:
        values.append(args.layout)
        assignments.append(f"set layoutName to item {len(values)} of argv")
        commands.append("set base slide of targetSlide to slide layout layoutName of d")
    for attr, apple_property in (
        ("skipped", "skipped"),
        ("title_showing", "title showing"),
        ("body_showing", "body showing"),
    ):
        value = getattr(args, attr)
        if value is not None:
            commands.append(f"set {apple_property} of targetSlide to {str(value).lower()}")
    if args.transition is not None:
        effect = TRANSITIONS[args.transition]
        automatic = str(args.automatic).lower()
        commands.append(
            "set transition properties of targetSlide to "
            f"{{transition effect:{effect}, transition duration:{args.duration}, "
            f"transition delay:{args.delay}, automatic transition:{automatic}}}"
        )
    if not commands:
        raise LayoutError("specify at least one slide configuration option")
    command_text = "\n            ".join(commands)
    body = f'''set targetSlide to slide slideNumber of d
            {command_text}'''
    success, output = run_applescript(mutation_script(assignments, body), values)
    return success, f"Configured slide {args.slide} in {deck}" if success else output


def add_geometry_options(parser: argparse.ArgumentParser, *, defaults: tuple[int, int, int, int]) -> None:
    parser.add_argument("--x", type=int, default=defaults[0])
    parser.add_argument("--y", type=int, default=defaults[1])
    parser.add_argument("--width", type=int, default=defaults[2])
    parser.add_argument("--height", type=int, default=defaults[3])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precise Keynote layout operations with argv-safe text and paths"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    text_parser = subparsers.add_parser("add-text", help="Add a positioned, styled text box")
    text_parser.add_argument("file")
    text_parser.add_argument("slide", type=int)
    text_parser.add_argument("--text", required=True)
    add_geometry_options(text_parser, defaults=(100, 100, 600, 100))
    text_parser.add_argument("--font", default="Helvetica Neue")
    text_parser.add_argument("--size", type=float, default=32)
    text_parser.add_argument("--color", default="#FFFFFF")
    text_parser.add_argument("--opacity", type=int, default=100)
    text_parser.add_argument("--rotation", type=int, default=0)
    text_parser.add_argument("--locked", action="store_true")

    style_parser = subparsers.add_parser("style-text", help="Style or reposition existing text")
    style_parser.add_argument("file")
    style_parser.add_argument("slide", type=int)
    style_parser.add_argument("--target", choices=["title", "body", "text"], required=True)
    style_parser.add_argument("--match", help="Substring selecting a custom text item")
    style_parser.add_argument("--font")
    style_parser.add_argument("--size", type=float)
    style_parser.add_argument("--color")
    style_parser.add_argument("--x", type=int)
    style_parser.add_argument("--y", type=int)
    style_parser.add_argument("--width", type=int)
    style_parser.add_argument("--height", type=int)
    style_parser.add_argument("--opacity", type=int)
    style_parser.add_argument("--rotation", type=int)

    table_parser = subparsers.add_parser("add-table", help="Add a native table from JSON rows")
    table_parser.add_argument("file")
    table_parser.add_argument("slide", type=int)
    table_parser.add_argument("json")
    add_geometry_options(table_parser, defaults=(100, 300, 700, 300))
    table_parser.add_argument("--header-rows", type=int, default=1)
    table_parser.add_argument("--header-columns", type=int, default=0)
    table_parser.add_argument("--font", default="Helvetica Neue")
    table_parser.add_argument("--size", type=float, default=18)

    image_parser = subparsers.add_parser("add-image", help="Add an image with accessibility metadata")
    image_parser.add_argument("file")
    image_parser.add_argument("slide", type=int)
    image_parser.add_argument("image")
    add_geometry_options(image_parser, defaults=(100, 100, 500, 300))
    image_parser.add_argument("--description", help="VoiceOver accessibility description")
    image_parser.add_argument("--opacity", type=int, default=100)
    image_parser.add_argument("--rotation", type=int, default=0)
    image_parser.add_argument("--locked", action="store_true")

    image_style_parser = subparsers.add_parser("style-image", help="Update an existing image by inventory index")
    image_style_parser.add_argument("file")
    image_style_parser.add_argument("slide", type=int)
    image_style_parser.add_argument("--index", type=int, required=True)
    image_style_parser.add_argument("--x", type=int)
    image_style_parser.add_argument("--y", type=int)
    image_style_parser.add_argument("--width", type=int)
    image_style_parser.add_argument("--height", type=int)
    image_style_parser.add_argument("--description")
    image_style_parser.add_argument("--opacity", type=int)
    image_style_parser.add_argument("--rotation", type=int)
    image_lock_group = image_style_parser.add_mutually_exclusive_group()
    image_lock_group.add_argument("--locked", dest="locked", action="store_true")
    image_lock_group.add_argument("--unlocked", dest="locked", action="store_false")
    image_style_parser.set_defaults(locked=None)

    slide_parser = subparsers.add_parser("configure-slide", help="Change layout, visibility, skip state, or transition")
    slide_parser.add_argument("file")
    slide_parser.add_argument("slide", type=int)
    slide_parser.add_argument("--layout")
    skip_group = slide_parser.add_mutually_exclusive_group()
    skip_group.add_argument("--skip", dest="skipped", action="store_true")
    skip_group.add_argument("--unskip", dest="skipped", action="store_false")
    title_group = slide_parser.add_mutually_exclusive_group()
    title_group.add_argument("--show-title", dest="title_showing", action="store_true")
    title_group.add_argument("--hide-title", dest="title_showing", action="store_false")
    body_group = slide_parser.add_mutually_exclusive_group()
    body_group.add_argument("--show-body", dest="body_showing", action="store_true")
    body_group.add_argument("--hide-body", dest="body_showing", action="store_false")
    slide_parser.set_defaults(skipped=None, title_showing=None, body_showing=None)
    slide_parser.add_argument("--transition", choices=sorted(TRANSITIONS))
    slide_parser.add_argument("--duration", type=float, default=0.5)
    slide_parser.add_argument("--delay", type=float, default=0.0)
    slide_parser.add_argument("--automatic", action="store_true")

    args = parser.parse_args()
    try:
        if hasattr(args, "slide") and args.slide < 1:
            raise LayoutError("slide number must be at least 1")
        if hasattr(args, "index") and args.index is not None and args.index < 1:
            raise LayoutError("item index must be at least 1")
        for dimension in ("width", "height"):
            value = getattr(args, dimension, None)
            if value is not None and value <= 0:
                raise LayoutError(f"{dimension} must be positive")
        if hasattr(args, "size") and args.size is not None and args.size <= 0:
            raise LayoutError("font size must be positive")
        if args.command == "add-table" and (args.header_rows < 0 or args.header_columns < 0):
            raise LayoutError("header counts cannot be negative")
        if args.command == "configure-slide" and (args.duration < 0 or args.delay < 0):
            raise LayoutError("transition duration and delay cannot be negative")
        if hasattr(args, "opacity") and args.opacity is not None:
            bounded(args.opacity, 0, 100, "opacity")
        if hasattr(args, "rotation") and args.rotation is not None:
            bounded(args.rotation, 0, 359, "rotation")
        if args.command == "add-text":
            result = add_text(args)
        elif args.command == "style-text":
            if args.target == "text" and not args.match:
                raise LayoutError("--match is required with --target text")
            result = style_text(args)
        elif args.command == "add-table":
            result = add_table(args)
        elif args.command == "add-image":
            result = add_image(args)
        elif args.command == "style-image":
            result = style_image(args)
        elif args.command == "configure-slide":
            result = configure_slide(args)
        else:
            raise LayoutError(f"unknown command: {args.command}")
    except LayoutError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    success, message = result
    print(message, file=sys.stdout if success else sys.stderr)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
