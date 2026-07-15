"""Shared, local-only helpers for the PDF bundle."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path


DEFAULT_MAX_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_PAGES = 50
DEFAULT_STDOUT_CHARS = 50_000
PAGE_SPEC = re.compile(r"^[0-9][0-9,\-]*$")
LANGUAGE = re.compile(r"^[A-Za-z0-9_+.-]+$")


class PdfToolError(RuntimeError):
    """Expected user-facing PDF processing failure."""


def input_pdf(raw: str, allow_large: bool = False) -> Path:
    path = Path(raw).expanduser()
    if not path.exists():
        raise PdfToolError(f"file not found: {path}")
    if not path.is_file():
        raise PdfToolError(f"not a regular file: {path}")
    if path.suffix.lower() != ".pdf":
        raise PdfToolError(f"not a PDF filename: {path}")
    if not allow_large and path.stat().st_size > DEFAULT_MAX_BYTES:
        raise PdfToolError("PDF exceeds 512 MiB; inspect it manually or pass --allow-large")
    return path.resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def available_backends() -> dict[str, bool]:
    return {
        name: shutil.which(name) is not None
        for name in ("lit", "pdfinfo", "pdftotext", "pdftoppm", "qpdf", "tesseract")
    }


def parse_pages(spec: str, total_pages: int) -> list[int]:
    if not PAGE_SPEC.fullmatch(spec):
        raise PdfToolError(f"invalid page selection: {spec!r}")
    result: list[int] = []
    seen: set[int] = set()
    for component in spec.split(","):
        if "-" in component:
            start_text, end_text = component.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise PdfToolError(f"descending page range is not allowed: {component}")
            values = range(start, end + 1)
        else:
            values = (int(component),)
        for page in values:
            if page < 1 or page > total_pages:
                raise PdfToolError(f"page {page} is outside 1-{total_pages}")
            if page not in seen:
                seen.add(page)
                result.append(page)
    if not result:
        raise PdfToolError("page selection is empty")
    return result


def distributed_pages(total_pages: int, count: int) -> list[int]:
    count = max(1, min(count, total_pages, 25))
    if count == 1:
        return [1]
    return sorted({1 + round(index * (total_pages - 1) / (count - 1)) for index in range(count)})


def text_quality(text: str) -> dict[str, object]:
    stripped = text.strip()
    warnings: list[str] = []
    if not stripped:
        return {"quality": "no-text", "characters": 0, "warnings": ["no extractable text"]}
    lowered = stripped.lower()
    if "(cid:" in lowered:
        warnings.append("unmapped (cid:) glyph markers")
    replacement_ratio = stripped.count("\ufffd") / len(stripped)
    if replacement_ratio > 0.005:
        warnings.append("many Unicode replacement characters")
    if len(stripped) >= 200:
        whitespace_ratio = sum(character.isspace() for character in stripped) / len(stripped)
        if whitespace_ratio < 0.06:
            warnings.append("unusually low whitespace ratio")
    return {
        "quality": "suspect" if warnings else "good",
        "characters": len(stripped),
        "warnings": warnings,
    }


def validate_language(language: str) -> str:
    if not LANGUAGE.fullmatch(language):
        raise PdfToolError(f"invalid OCR language: {language!r}")
    return language


def output_path(raw: str, inputs: list[Path], force: bool) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_symlink():
        raise PdfToolError(f"refusing output symlink: {candidate}")
    path = candidate.resolve(strict=False)
    if path in {item.resolve() for item in inputs}:
        raise PdfToolError("output path must differ from every input path")
    if path.exists() and not force:
        raise PdfToolError(f"output already exists (use --force): {path}")
    if not path.parent.is_dir():
        raise PdfToolError(f"output directory does not exist: {path.parent}")
    return path


def atomic_bytes(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_text(path: Path, text: str) -> None:
    atomic_bytes(path, text.encode("utf-8"))
