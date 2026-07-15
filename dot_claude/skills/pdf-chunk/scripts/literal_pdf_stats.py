#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=6,<7"]
# ///
"""Inspect a PDF without printing its document text."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from pdf_common import (
    PdfToolError,
    available_backends,
    distributed_pages,
    input_pdf,
    sha256_file,
    text_quality,
)


def pdfinfo_pages(path) -> int | None:
    if not available_backends()["pdfinfo"]:
        return None
    result = subprocess.run(
        ["pdfinfo", str(path)], text=True, capture_output=True, timeout=30
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def inspect_pdf(raw_path: str, sample_count: int, allow_large: bool) -> dict[str, object]:
    path = input_pdf(raw_path, allow_large)
    backends = available_backends()
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=False)
    except Exception as exc:
        raise PdfToolError(f"cannot parse PDF: {exc}") from exc

    encrypted = bool(reader.is_encrypted)
    pypdf_pages = len(reader.pages) if not encrypted else None
    fast_pages = pdfinfo_pages(path)
    page_count = fast_pages if fast_pages is not None else pypdf_pages
    result: dict[str, object] = {
        "schema_version": 1,
        "file": path.name,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "page_count": page_count,
        "encrypted": encrypted,
        "page_count_backend": "pdfinfo" if fast_pages is not None else "pypdf",
        "available_backends": backends,
        "samples": [],
        "warnings": [],
    }
    if encrypted:
        result["warnings"] = ["encrypted PDF; text was not sampled"]
        return result
    if page_count is None or page_count < 1:
        raise PdfToolError("PDF contains no pages")
    if pypdf_pages != page_count:
        result["warnings"] = [
            f"backend page counts disagree: pdfinfo={page_count}, pypdf={pypdf_pages}"
        ]
        page_count = pypdf_pages
        result["page_count"] = pypdf_pages

    samples = []
    for page_number in distributed_pages(page_count, sample_count):
        try:
            text = reader.pages[page_number - 1].extract_text() or ""
            quality = text_quality(text)
        except Exception as exc:
            quality = {
                "quality": "suspect",
                "characters": 0,
                "warnings": [f"text extraction failed: {exc}"],
            }
        samples.append({"page": page_number, **quality})
    result["samples"] = samples
    if any(sample["quality"] != "good" for sample in samples):
        result["warnings"].append("one or more sampled pages may require OCR")
    return result


def human_report(report: dict[str, object]) -> str:
    backends = report["available_backends"]
    lines = [
        f"File: {report['file']}",
        f"Path: {report['path']}",
        f"SHA-256: {report['sha256']}",
        f"Size: {report['size_bytes']:,} bytes",
        f"Pages: {report['page_count'] if report['page_count'] is not None else 'unknown'}",
        f"Encrypted: {'yes' if report['encrypted'] else 'no'}",
        "Optional backends: " + ", ".join(
            f"{name}={'yes' if present else 'no'}" for name, present in backends.items()
        ),
    ]
    for sample in report["samples"]:
        warning = "; ".join(sample["warnings"])
        suffix = f" ({warning})" if warning else ""
        lines.append(
            f"Physical page {sample['page']}: {sample['quality']}, "
            f"{sample['characters']} characters{suffix}"
        )
    lines.extend(f"Warning: {warning}" for warning in report["warnings"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--sample-pages", type=int, default=5)
    parser.add_argument("--allow-large", action="store_true")
    args = parser.parse_args()
    if args.sample_pages < 1 or args.sample_pages > 25:
        parser.error("--sample-pages must be between 1 and 25")
    try:
        report = inspect_pdf(args.pdf, args.sample_pages, args.allow_large)
    except PdfToolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True) if args.as_json else human_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
