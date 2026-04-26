---
name: pdf-chunk
description: Handle large PDFs without filling context. Use when PDF is >1MB or >50 pages. Extracts text in chunks, provides stats, and allows selective page loading.
---

# Large PDF Handler

Handle large PDFs without overwhelming Claude Code's context window. This skill analyzes PDF size and page count before loading, then extracts only the pages you need.

## When to Use

- PDF files larger than 1MB
- PDFs with more than 50 pages
- When context is running low
- When you only need specific sections of a document

## Commands

### Get PDF Stats

Analyze a PDF without loading content into context:

```
/pdf-chunk stats document.pdf
```

Returns: page count, file size, whether text is extractable, estimated word count.

### Extract Page Range

Load only specific pages into context:

```
/pdf-chunk pages 1-10 document.pdf
```

Page numbers are 1-indexed. Supports ranges like `1-10`, `5-15`, or single pages like `7-7`.

### Extract All to File

Extract full text to a file (doesn't load into context):

```
/pdf-chunk extract document.pdf output.txt
```

Useful for saving the full content without using context, then searching or grepping the result.

## Workflow

1. **Always run `stats` first** on large PDFs to understand size
2. **Decide which pages** you actually need based on the stats
3. **Load incrementally** - start with a small range, expand if needed

## Example Session

```
User: I have a 200-page PDF manual. Help me find the installation instructions.

Claude: Let me check the PDF first.
> /pdf-chunk stats manual.pdf

Output: 200 pages, 4.2 MB, ~85,000 words

Claude: That's a large document. Let me check the first few pages for a table of contents.
> /pdf-chunk pages 1-5 manual.pdf

[Reviews TOC, finds Installation is on pages 12-25]

Claude: Found it. Let me extract just the installation section.
> /pdf-chunk pages 12-25 manual.pdf
```

## Implementation

**Preferred path: LiteParse `lit` CLI** if installed (`command -v lit`). It implements selective-page extraction natively via `--target-pages`, runs locally with built-in OCR, and avoids the Python dependency setup.

```bash
# Stats-equivalent: page count + text-layer presence (no full extraction)
lit parse --max-pages 1 --format json document.pdf | jq '{pages: .pageCount, hasText: (.pages[0].text | length > 0)}'

# Extract a page range only — equivalent to /pdf-chunk pages 1-10
lit parse --target-pages "1-10" --format text -o /dev/stdout document.pdf

# Multi-range, e.g. TOC + installation section
lit parse --target-pages "1-5,12-25" --format text -o out.txt document.pdf

# Full extraction to file (no context cost)
lit parse --format text -o out.txt document.pdf
```

When `lit` is unavailable (non-personal machines, restricted work environments), fall back to the Python scripts below.

### Stats Command

**macOS/Linux:**
```bash
uv run ~/.claude/skills/pdf-chunk/scripts/pdf_stats.py document.pdf
```

**Windows:**
```powershell
uv run $env:USERPROFILE\.claude\skills\pdf-chunk\scripts\pdf_stats.py document.pdf
```

### Extract Pages Command

**macOS/Linux:**
```bash
uv run ~/.claude/skills/pdf-chunk/scripts/extract_pages.py document.pdf 1 10
```

**Windows:**
```powershell
uv run $env:USERPROFILE\.claude\skills\pdf-chunk\scripts\extract_pages.py document.pdf 1 10
```

Arguments: `<pdf_file> <start_page> <end_page> [output_file]`

- If output_file is provided, writes to file
- If omitted, prints to stdout

## Dependencies

Both scripts declare their dependencies inline via PEP 723 script metadata (`pypdf`, `pdfplumber`). `uv run` provisions an isolated environment and auto-installs them on first invocation — no manual install step.

`uv` ships in the Brewfile / Scoopfile and is required across all machines for this skill.

## Work/Restricted Environments

If you're in an environment where `uv` is unavailable or network access to pypi.org is blocked:

1. Use **LiteParse** if available (`command -v lit`) — single binary via Homebrew tap on personal machines, no Python deps
2. Use CLI tools instead: `pdftotext -f 1 -l 10 document.pdf` (from poppler-utils)
3. Use the built-in `/pdf` skill which may have different dependencies

## Tips

- **Check stats first** - prevents accidentally loading a 500-page PDF
- **Use file extraction** for very large documents - extract to file, then grep
- **Load TOC first** - pages 1-5 often contain table of contents
- **Iterate** - start with small ranges, expand as needed
