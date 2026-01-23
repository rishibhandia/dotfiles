#!/usr/bin/env python3
# /// script
# dependencies = ["pypdf", "pdfplumber"]
# ///
"""
Extract text from specific page range of a PDF.
Outputs to stdout or file, avoiding loading entire PDF into context.

Cross-platform usage:
  - With uv (auto-installs deps): uv run extract_pages.py document.pdf 1 10
  - With Python (requires deps):  python3 extract_pages.py document.pdf 1 10
  - Windows:                      python extract_pages.py document.pdf 1 10
"""

import sys
from pathlib import Path


def extract_pages(pdf_path: str, start_page: int, end_page: int, output_file: str | None = None) -> str | None:
    """
    Extract text from a specific page range.

    Args:
        pdf_path: Path to PDF file
        start_page: First page to extract (1-indexed)
        end_page: Last page to extract (1-indexed, inclusive)
        output_file: Optional file to write output to

    Returns:
        Extracted text if no output_file, None otherwise
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    # Convert to 0-indexed for internal use
    start_idx = start_page - 1
    end_idx = end_page  # Keep as-is since we use range() which is exclusive

    text_parts = []

    # Try pdfplumber first (better text extraction)
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Validate page range
            if start_idx < 0 or start_idx >= total_pages:
                raise ValueError(f"Start page {start_page} out of range (1-{total_pages})")
            if end_page > total_pages:
                raise ValueError(f"End page {end_page} out of range (1-{total_pages})")
            if start_page > end_page:
                raise ValueError(f"Start page ({start_page}) must be <= end page ({end_page})")

            for i in range(start_idx, min(end_idx, total_pages)):
                page = pdf.pages[i]
                page_text = page.extract_text() or ""

                if page_text.strip():
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                else:
                    text_parts.append(f"--- Page {i + 1} ---\n[No extractable text - may be image/scan]")

    except ImportError:
        # Fall back to pypdf
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            # Validate page range
            if start_idx < 0 or start_idx >= total_pages:
                raise ValueError(f"Start page {start_page} out of range (1-{total_pages})")
            if end_page > total_pages:
                raise ValueError(f"End page {end_page} out of range (1-{total_pages})")
            if start_page > end_page:
                raise ValueError(f"Start page ({start_page}) must be <= end page ({end_page})")

            for i in range(start_idx, min(end_idx, total_pages)):
                page = reader.pages[i]
                page_text = page.extract_text() or ""

                if page_text.strip():
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                else:
                    text_parts.append(f"--- Page {i + 1} ---\n[No extractable text - may be image/scan]")

        except ImportError:
            raise ImportError("Neither pdfplumber nor pypdf installed. Run: uv pip install pypdf pdfplumber")

    full_text = "\n\n".join(text_parts)

    if output_file:
        output_path = Path(output_file)
        output_path.write_text(full_text, encoding="utf-8")
        print(f"Extracted pages {start_page}-{end_page} to {output_file}")
        return None

    return full_text


def parse_page_range(range_str: str) -> tuple[int, int]:
    """Parse a page range string like '1-10' or '5'."""
    if "-" in range_str:
        parts = range_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid page range: {range_str}")
        return int(parts[0]), int(parts[1])
    else:
        page = int(range_str)
        return page, page


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_pages.py <pdf_file> <start_page> <end_page> [output_file]")
        print("       extract_pages.py <pdf_file> <page_range> [output_file]")
        print()
        print("Examples:")
        print("  extract_pages.py document.pdf 1 10           # Extract pages 1-10 to stdout")
        print("  extract_pages.py document.pdf 1-10           # Same, using range syntax")
        print("  extract_pages.py document.pdf 5 15 out.txt   # Extract pages 5-15 to file")
        print()
        print("Page numbers are 1-indexed (first page is 1).")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Determine if using range syntax or separate start/end
    try:
        if "-" in sys.argv[2] or (len(sys.argv) >= 4 and not sys.argv[3].isdigit()):
            # Range syntax: "1-10" or single page with output file
            start_page, end_page = parse_page_range(sys.argv[2])
            output_file = sys.argv[3] if len(sys.argv) > 3 else None
        else:
            # Separate start/end syntax
            start_page = int(sys.argv[2])
            end_page = int(sys.argv[3]) if len(sys.argv) > 3 else start_page
            output_file = sys.argv[4] if len(sys.argv) > 4 else None
    except ValueError as e:
        print(f"Error parsing arguments: {e}")
        sys.exit(1)

    try:
        result = extract_pages(pdf_path, start_page, end_page, output_file)
        if result:
            print(result)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
