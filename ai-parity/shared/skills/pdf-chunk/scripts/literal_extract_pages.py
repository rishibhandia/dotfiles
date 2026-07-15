#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=6,<7"]
# ///
"""Extract bounded physical page ranges with optional local OCR."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pdf_common import (
    DEFAULT_MAX_PAGES,
    DEFAULT_STDOUT_CHARS,
    PdfToolError,
    atomic_text,
    available_backends,
    input_pdf,
    output_path,
    parse_pages,
    sha256_file,
    text_quality,
    validate_language,
)


def run_command(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))


def lit_text(path: Path, page: int, ocr: bool, language: str) -> str | None:
    with tempfile.TemporaryDirectory(prefix="pdf-chunk-lit-") as temporary:
        output = Path(temporary) / "page.txt"
        command = [
            "lit", "parse", "-q", "--format", "text", "--target-pages", str(page),
            "--max-pages", str(page), "--num-workers", "4", "--ocr-language", language,
            "-o", str(output),
        ]
        if not ocr:
            command.insert(3, "--no-ocr")
        result = run_command([*command, str(path)])
        if result.returncode == 0 and output.is_file():
            return output.read_text(encoding="utf-8", errors="replace")
    return None


def poppler_text(path: Path, page: int) -> str | None:
    result = run_command(
        ["pdftotext", "-f", str(page), "-l", str(page), "-enc", "UTF-8", str(path), "-"]
    )
    return result.stdout if result.returncode == 0 else None


def python_text(path: Path, page: int) -> str:
    try:
        from pypdf import PdfReader

        return PdfReader(str(path), strict=False).pages[page - 1].extract_text() or ""
    except Exception as exc:
        raise PdfToolError(f"Python extraction failed on physical page {page}: {exc}") from exc


def tesseract_text(path: Path, page: int, language: str) -> str | None:
    with tempfile.TemporaryDirectory(prefix="pdf-chunk-ocr-") as temporary:
        prefix = Path(temporary) / "page"
        render = run_command([
            "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
            "-r", "200", "-png", str(path), str(prefix),
        ])
        image = prefix.with_suffix(".png")
        if render.returncode != 0 or not image.is_file():
            return None
        ocr = run_command(["tesseract", str(image), "stdout", "-l", language], timeout=180)
        return ocr.stdout if ocr.returncode == 0 else None


def extract_one(path: Path, page: int, ocr_mode: str, language: str, backends: dict[str, bool]):
    attempts: list[str] = []
    text: str | None = None
    backend = ""
    if ocr_mode != "always":
        if backends["lit"]:
            attempts.append("lit-no-ocr")
            text = lit_text(path, page, False, language)
            backend = "lit"
        if text is None and backends["pdftotext"]:
            attempts.append("pdftotext")
            text = poppler_text(path, page)
            backend = "pdftotext"
        if text is None:
            attempts.append("pypdf")
            text = python_text(path, page)
            backend = "pypdf"

    quality = text_quality(text or "")
    should_ocr = ocr_mode == "always" or (
        ocr_mode == "auto" and quality["quality"] != "good"
    )
    used_ocr = False
    if should_ocr:
        recovered: str | None = None
        if backends["lit"]:
            attempts.append("lit-ocr")
            recovered = lit_text(path, page, True, language)
            if recovered is not None:
                backend = "lit-ocr"
        if recovered is None and backends["pdftoppm"] and backends["tesseract"]:
            attempts.append("pdftoppm+tesseract")
            recovered = tesseract_text(path, page, language)
            if recovered is not None:
                backend = "pdftoppm+tesseract"
        if recovered is None and ocr_mode == "always":
            raise PdfToolError(f"no local OCR backend succeeded for physical page {page}")
        if recovered is not None:
            text = recovered
            used_ocr = True
            quality = text_quality(text)
        elif quality["quality"] != "good":
            quality["warnings"].append("local OCR unavailable or unsuccessful")
    return text or "", {
        "page": page,
        "backend": backend,
        "ocr": used_ocr,
        "quality": quality["quality"],
        "characters": len((text or "").strip()),
        "warnings": quality["warnings"],
        "attempts": attempts,
    }


def resolve_arguments(args, parser) -> tuple[str, str | None]:
    if args.pages and args.legacy:
        parser.error("use either --pages or the legacy positional page arguments")
    if args.pages:
        return args.pages, args.output
    if not args.legacy:
        parser.error("provide --pages RANGE or legacy START [END] [OUTPUT]")
    if len(args.legacy) > 3:
        parser.error("legacy syntax is START [END] [OUTPUT]")
    start = args.legacy[0]
    end = args.legacy[1] if len(args.legacy) >= 2 and args.legacy[1].isdigit() else start
    output = args.output
    if len(args.legacy) == 2 and not args.legacy[1].isdigit():
        output = args.legacy[1]
    elif len(args.legacy) == 3:
        output = args.legacy[2]
    return f"{start}-{end}" if start != end else start, output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("legacy", nargs="*")
    parser.add_argument("--pages")
    parser.add_argument("--output")
    parser.add_argument("--manifest")
    parser.add_argument("--ocr", choices=("auto", "never", "always"), default="auto")
    parser.add_argument("--ocr-language", default="en")
    parser.add_argument("--allow-large", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        spec, raw_output = resolve_arguments(args, parser)
        language = validate_language(args.ocr_language)
        path = input_pdf(args.pdf, args.allow_large)
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            raise PdfToolError("encrypted PDFs are not supported")
        pages = parse_pages(spec, len(reader.pages))
        if len(pages) > DEFAULT_MAX_PAGES and not args.allow_large:
            raise PdfToolError(
                f"selection has {len(pages)} pages; use --output and --allow-large"
            )
        if len(pages) > DEFAULT_MAX_PAGES and not raw_output:
            raise PdfToolError("large extraction requires --output")
        output = output_path(raw_output, [path], args.force) if raw_output else None
        manifest = output_path(args.manifest, [path], args.force) if args.manifest else None
        if output and manifest and output == manifest:
            raise PdfToolError("text output and manifest paths must differ")

        backends = available_backends()
        sections: list[str] = []
        records: list[dict[str, object]] = []
        for page in pages:
            text, record = extract_one(path, page, args.ocr, language, backends)
            sections.append(f"--- Physical page {page} ---\n{text.strip()}")
            records.append(record)
        combined = "\n\n".join(sections) + "\n"
        if not output and len(combined) > DEFAULT_STDOUT_CHARS and not args.allow_large:
            raise PdfToolError(
                f"extracted text is {len(combined):,} characters; use --output"
            )
        if output:
            atomic_text(output, combined)
            print(f"Extracted {len(pages)} physical page(s) to {output}")
        else:
            sys.stdout.write(combined)
        if manifest:
            payload = {
                "schema_version": 1,
                "source": str(path),
                "source_sha256": sha256_file(path),
                "selected_pages": pages,
                "ocr_mode": args.ocr,
                "ocr_language": language,
                "characters": len(combined),
                "pages": records,
            }
            atomic_text(manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    except PdfToolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: cannot process PDF: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
