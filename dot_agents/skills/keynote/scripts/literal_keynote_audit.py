#!/usr/bin/env python3
"""Audit a rich Keynote inventory for common layout and accessibility issues."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    """A malformed inventory or invalid audit option."""


def load_inventory(path: str) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    try:
        inventory = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read inventory JSON: {exc}") from exc
    if not isinstance(inventory, dict):
        raise AuditError("inventory root must be an object")
    canvas = inventory.get("canvas")
    slides = inventory.get("slides")
    if not isinstance(canvas, dict) or not isinstance(slides, dict):
        raise AuditError("inventory must contain canvas and slides objects")
    for key in ("width", "height"):
        if not isinstance(canvas.get(key), (int, float)) or canvas[key] <= 0:
            raise AuditError(f"canvas.{key} must be a positive number")
    return inventory


def box(item: dict[str, Any]) -> tuple[float, float, float, float] | None:
    position = item.get("position")
    size = item.get("size")
    if (
        not isinstance(position, list) or len(position) != 2
        or not isinstance(size, list) or len(size) != 2
        or not all(isinstance(value, (int, float)) for value in position + size)
    ):
        return None
    x, y = position
    width, height = size
    return float(x), float(y), float(x + width), float(y + height)


def intersection_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    first_area = max(1.0, (first[2] - first[0]) * (first[3] - first[1]))
    second_area = max(1.0, (second[2] - second[0]) * (second[3] - second[1]))
    return intersection / min(first_area, second_area)


def item_label(item: dict[str, Any]) -> str:
    kind = item.get("type", "item")
    index = item.get("index")
    if index is not None:
        return f"{kind} {index}"
    return str(kind)


def audit_inventory(
    inventory: dict[str, Any],
    margin: int = 32,
    overlap_threshold: float = 0.20,
) -> list[dict[str, Any]]:
    width = float(inventory["canvas"]["width"])
    height = float(inventory["canvas"]["height"])
    findings: list[dict[str, Any]] = []

    def add(slide: str, severity: str, code: str, message: str) -> None:
        findings.append({
            "slide": slide,
            "severity": severity,
            "code": code,
            "message": message,
        })

    for slide_key, slide in inventory["slides"].items():
        if not isinstance(slide, dict):
            add(slide_key, "error", "invalid-slide", "slide entry is not an object")
            continue
        items = slide.get("items", [])
        if not isinstance(items, list):
            add(slide_key, "error", "invalid-items", "items entry is not an array")
            continue

        custom_items = [item for item in items if item.get("type") not in ("title", "body")]
        if len(custom_items) > 12:
            add(
                slide_key, "warning", "crowded-slide",
                f"slide has {len(custom_items)} custom items; consider simplifying",
            )

        for item in items:
            if not isinstance(item, dict):
                continue
            item_box = box(item)
            label = item_label(item)
            if item_box is not None:
                if item_box[0] < 0 or item_box[1] < 0 or item_box[2] > width or item_box[3] > height:
                    add(slide_key, "error", "off-canvas", f"{label} extends outside the slide canvas")
                elif item.get("type") not in ("title", "body") and (
                    item_box[0] < margin or item_box[1] < margin
                    or item_box[2] > width - margin or item_box[3] > height - margin
                ):
                    add(slide_key, "warning", "tight-margin", f"{label} is within {margin} pt of a slide edge")

            if item.get("type") == "image" and not str(item.get("description", "")).strip():
                add(slide_key, "warning", "missing-alt-text", f"{label} has no accessibility description")

            if item.get("type") in ("title", "body", "text"):
                font_size = item.get("font_size")
                minimum = 28 if item.get("type") == "title" else 18
                if isinstance(font_size, (int, float)) and font_size < minimum:
                    add(
                        slide_key, "warning", "small-text",
                        f"{label} uses {font_size:g} pt text; recommended minimum is {minimum} pt",
                    )

        overlap_items = [item for item in custom_items if box(item) is not None]
        for index, first in enumerate(overlap_items):
            for second in overlap_items[index + 1:]:
                ratio = intersection_ratio(box(first), box(second))
                if ratio >= overlap_threshold:
                    add(
                        slide_key, "warning", "overlap",
                        f"{item_label(first)} and {item_label(second)} overlap by {ratio:.0%} of the smaller item",
                    )

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit Keynote inventory geometry, typography, and accessibility"
    )
    parser.add_argument("inventory", help="JSON produced by keynote_inventory.py")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when findings exist")
    parser.add_argument("--margin", type=int, default=32, help="Recommended edge margin in points")
    parser.add_argument(
        "--overlap-threshold", type=float, default=0.20,
        help="Minimum overlap ratio to report (default: 0.20)",
    )
    args = parser.parse_args()

    try:
        if args.margin < 0:
            raise AuditError("margin cannot be negative")
        if not 0 < args.overlap_threshold <= 1:
            raise AuditError("overlap threshold must be greater than 0 and at most 1")
        inventory = load_inventory(args.inventory)
        findings = audit_inventory(inventory, args.margin, args.overlap_threshold)
    except AuditError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    if args.json:
        print(json.dumps({"finding_count": len(findings), "findings": findings}, indent=2))
    elif findings:
        for finding in findings:
            print(
                f"{finding['severity'].upper()} {finding['slide']} "
                f"[{finding['code']}]: {finding['message']}"
            )
        print(f"{len(findings)} finding(s)")
    else:
        print("No layout or accessibility findings.")

    raise SystemExit(1 if args.strict and findings else 0)


if __name__ == "__main__":
    main()
