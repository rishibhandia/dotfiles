#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=6,<7"]
# ///
"""Perform bounded, atomic PDF merge, selection, and rotation operations."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 512 * 1024 * 1024
PAGE_SPEC = re.compile(r"^[0-9][0-9,\-]*$")


class PdfError(RuntimeError):
    pass


def source(raw: str, allow_large: bool) -> Path:
    path = Path(raw).expanduser()
    if not path.exists() or not path.is_file():
        raise PdfError(f"not a regular file: {path}")
    if path.suffix.lower() != ".pdf":
        raise PdfError(f"not a PDF filename: {path}")
    if not allow_large and path.stat().st_size > MAX_BYTES:
        raise PdfError("PDF exceeds 512 MiB; pass --allow-large after inspection")
    return path.resolve()


def destination(raw: str, inputs: list[Path], force: bool) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_symlink():
        raise PdfError(f"refusing output symlink: {candidate}")
    path = candidate.resolve(strict=False)
    if path.suffix.lower() != ".pdf":
        raise PdfError("output must have a .pdf extension")
    if path in inputs:
        raise PdfError("output path must differ from every input path")
    if path.exists() and not force:
        raise PdfError(f"output already exists (use --force): {path}")
    if not path.parent.is_dir():
        raise PdfError(f"output directory does not exist: {path.parent}")
    return path


def pages(spec: str, total: int) -> list[int]:
    if not PAGE_SPEC.fullmatch(spec):
        raise PdfError(f"invalid page selection: {spec!r}")
    selected: list[int] = []
    seen: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            first_text, last_text = part.split("-", 1)
            first, last = int(first_text), int(last_text)
            if first > last:
                raise PdfError(f"descending range is not allowed: {part}")
            values = range(first, last + 1)
        else:
            values = (int(part),)
        for value in values:
            if value < 1 or value > total:
                raise PdfError(f"page {value} is outside 1-{total}")
            if value not in seen:
                seen.add(value)
                selected.append(value)
    return selected


def readable(path: Path):
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            raise PdfError(f"encrypted PDFs are not supported: {path}")
        len(reader.pages)
        return reader
    except PdfError:
        raise
    except Exception as exc:
        raise PdfError(f"cannot parse {path}: {exc}") from exc


def qpdf(command: list[str]) -> None:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PdfError(f"qpdf failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise PdfError(f"qpdf failed: {detail or 'unknown error'}")


def atomic_target(path: Path):
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".pdf", dir=path.parent)
    os.fchmod(descriptor, 0o600)
    os.close(descriptor)
    return Path(raw)


def validate_result(path: Path, expected_pages: int) -> None:
    reader = readable(path)
    if len(reader.pages) != expected_pages:
        raise PdfError(f"output validation failed: expected {expected_pages} pages")


def python_write(args, inputs: list[Path], selected: list[int] | None, temporary: Path) -> int:
    from pypdf import PdfWriter

    writer = PdfWriter()
    if args.action == "merge":
        for path in inputs:
            for page in readable(path).pages:
                writer.add_page(page)
    else:
        reader = readable(inputs[0])
        if args.action == "select":
            chosen = selected
        else:
            # rotate keeps every page; `selected` only marks which ones turn
            chosen = list(range(1, len(reader.pages) + 1))
        for number in chosen:
            page = reader.pages[number - 1]
            if args.action == "rotate" and number in selected:
                page.rotate(args.degrees)
            writer.add_page(page)
    with temporary.open("wb") as stream:
        writer.write(stream)
        stream.flush()
        os.fsync(stream.fileno())
    return len(writer.pages)


def execute(args) -> Path:
    inputs = [source(item, args.allow_large) for item in args.inputs]
    output = destination(args.output, inputs, args.force)
    readers = [readable(path) for path in inputs]
    selected = None
    if args.action in {"select", "rotate"}:
        selected = pages(args.pages, len(readers[0].pages))
    expected = (
        sum(len(reader.pages) for reader in readers)
        if args.action == "merge"
        else len(selected) if args.action == "select"
        else len(readers[0].pages)
    )
    temporary = atomic_target(output)
    try:
        if shutil.which("qpdf"):
            if args.action == "merge":
                qpdf(["qpdf", "--empty", "--pages", *map(str, inputs), "--", str(temporary)])
            elif args.action == "select":
                qpdf(["qpdf", str(inputs[0]), "--pages", ".", args.pages, "--", str(temporary)])
            else:
                qpdf(["qpdf", str(inputs[0]), str(temporary), f"--rotate=+{args.degrees}:{args.pages}"])
        else:
            python_write(args, inputs, selected, temporary)
        validate_result(temporary, expected)
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
        return output
    finally:
        if temporary.exists():
            temporary.unlink()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="action", required=True)
    merge = subcommands.add_parser("merge")
    merge.add_argument("inputs", nargs="+")
    select = subcommands.add_parser("select")
    select.add_argument("inputs", nargs=1)
    select.add_argument("--pages", required=True)
    rotate = subcommands.add_parser("rotate")
    rotate.add_argument("inputs", nargs=1)
    rotate.add_argument("--pages", required=True)
    rotate.add_argument("--degrees", type=int, choices=(90, 180, 270), required=True)
    for command in (merge, select, rotate):
        command.add_argument("--output", required=True)
        command.add_argument("--force", action="store_true")
        command.add_argument("--allow-large", action="store_true")
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        output = execute(args)
        print(f"Wrote {output}")
        return 0
    except PdfError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
