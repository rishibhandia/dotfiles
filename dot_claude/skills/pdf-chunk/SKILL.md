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

Run the Python scripts in the `scripts/` directory.

### Stats Command

**macOS/Linux (with uv):**
```bash
uv run ~/.claude/skills/pdf-chunk/scripts/pdf_stats.py document.pdf
```

**macOS/Linux (without uv):**
```bash
python3 ~/.claude/skills/pdf-chunk/scripts/pdf_stats.py document.pdf
```

**Windows:**
```powershell
uv run $env:USERPROFILE\.claude\skills\pdf-chunk\scripts\pdf_stats.py document.pdf
# or without uv:
python $env:USERPROFILE\.claude\skills\pdf-chunk\scripts\pdf_stats.py document.pdf
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

Required Python packages:
- `pypdf` - for page count and metadata
- `pdfplumber` - for text extraction

**With uv (recommended):** Dependencies auto-install on first run via inline script metadata.

**Without uv / Work environments:** Pre-install dependencies:
```bash
pip install pypdf pdfplumber   # or: uv pip install pypdf pdfplumber
```

## Work/Restricted Environments

If you're in an environment where:
- `uv` is not available
- Network access to pypi.org is blocked
- You cannot install packages

**Options:**
1. Ask IT to pre-install `pypdf` and `pdfplumber` system-wide
2. Use CLI tools instead: `pdftotext -f 1 -l 10 document.pdf` (from poppler-utils)
3. Use the built-in `/pdf` skill which may have different dependencies

## Tips

- **Check stats first** - prevents accidentally loading a 500-page PDF
- **Use file extraction** for very large documents - extract to file, then grep
- **Load TOC first** - pages 1-5 often contain table of contents
- **Iterate** - start with small ranges, expand as needed
