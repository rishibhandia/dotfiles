#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pypdf", "pdfplumber"]
# ///
"""
Get PDF statistics without loading full content into memory.
Returns: page count, file size, text extractability, estimated word count.
"""

import sys
import os
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_pdf_stats(pdf_path: str) -> dict:
    """Get PDF metadata without loading full content."""
    path = Path(pdf_path)

    if not path.exists():
        return {"error": f"File not found: {pdf_path}"}

    if not path.suffix.lower() == ".pdf":
        return {"error": f"Not a PDF file: {pdf_path}"}

    file_size = path.stat().st_size

    stats = {
        "file": path.name,
        "path": str(path.absolute()),
        "size_bytes": file_size,
        "size_human": format_size(file_size),
    }

    # Try pypdf first (lighter weight)
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        stats["page_count"] = len(reader.pages)

        # Check if text is extractable by sampling first page
        if reader.pages:
            sample_text = reader.pages[0].extract_text() or ""
            stats["has_text"] = len(sample_text.strip()) > 0

            # Estimate total words by sampling
            if stats["has_text"]:
                words_page1 = len(sample_text.split())
                stats["estimated_words"] = words_page1 * stats["page_count"]
            else:
                stats["estimated_words"] = 0
                stats["note"] = "PDF may be scanned/image-based (no extractable text)"

        # Get metadata if available
        if reader.metadata:
            meta = reader.metadata
            if meta.title:
                stats["title"] = meta.title
            if meta.author:
                stats["author"] = meta.author

    except ImportError:
        # Fall back to pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                stats["page_count"] = len(pdf.pages)

                # Check text extractability
                if pdf.pages:
                    sample_text = pdf.pages[0].extract_text() or ""
                    stats["has_text"] = len(sample_text.strip()) > 0

                    if stats["has_text"]:
                        words_page1 = len(sample_text.split())
                        stats["estimated_words"] = words_page1 * stats["page_count"]
                    else:
                        stats["estimated_words"] = 0
                        stats["note"] = "PDF may be scanned/image-based"

        except ImportError:
            stats["error"] = "Neither pypdf nor pdfplumber installed. Run: uv pip install pypdf pdfplumber"
            return stats

    # Add recommendations
    if stats.get("page_count", 0) > 50 or file_size > 1_000_000:
        stats["recommendation"] = "Large PDF - consider loading specific page ranges"

    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: pdf_stats.py <pdf_file>")
        print("\nReturns PDF statistics without loading full content.")
        sys.exit(1)

    pdf_path = sys.argv[1]
    stats = get_pdf_stats(pdf_path)

    if "error" in stats:
        print(f"Error: {stats['error']}")
        sys.exit(1)

    # Pretty print stats
    print(f"File: {stats['file']}")
    print(f"Path: {stats['path']}")
    print(f"Size: {stats['size_human']} ({stats['size_bytes']:,} bytes)")
    print(f"Pages: {stats['page_count']}")
    print(f"Text extractable: {'Yes' if stats.get('has_text') else 'No'}")

    if stats.get("estimated_words"):
        print(f"Estimated words: ~{stats['estimated_words']:,}")

    if stats.get("title"):
        print(f"Title: {stats['title']}")

    if stats.get("author"):
        print(f"Author: {stats['author']}")

    if stats.get("note"):
        print(f"Note: {stats['note']}")

    if stats.get("recommendation"):
        print(f"\n>> {stats['recommendation']}")


if __name__ == "__main__":
    main()
