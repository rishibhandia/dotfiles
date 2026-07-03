---
name: llm-pdf-processing
description: Feeding PDF content to an LLM at scale (Gemini/Claude) for classify/tag/extract/summarize. Use when deciding how to get PDF text to a model — pypdf text vs sending page-images, OCR fallback for scanned PDFs, and detecting broken text layers.
---

# Getting PDF content into an LLM cheaply and reliably

## Send extracted TEXT, not page-images
- Extract locally with **pypdf** (`PdfReader(path).pages[i].extract_text()`), cache it,
  send as text. Free, fast, reusable across passes.
- Gemini bills a PDF *page* at a flat ~258 tokens; a dense page of extracted *text* is a
  comparable token count — so page-images are **not** cheaper, and text is cacheable +
  faster. (Measured ~equal input cost; text ≥ quality on classification tasks.)
- First ~2–3 pages of text are plenty for type/topic/method classification (intro +
  methods carry the signal).

## Scanned / broken PDFs
- pypdf returns **nothing** for scanned PDFs (no text layer) and **garbage** for broken
  font maps.
- Detect a bad text layer: empty; contains `(cid:` markers (unmapped glyphs); very low
  space-ratio (`spaces/len < ~0.06`, i.e. jammed words); too few chars per page; or many
  `�` replacement chars.
- OCR fallback: **liteparse** (Homebrew, Tesseract-based) —
  ```
  liteparse parse FILE --format text --target-pages 1-3 --num-workers 2 -o out.txt
  ```
  Only OCR the bad subset (~5s/page); keep pypdf for the ~90% that have a clean text
  layer. Then re-run classification on just the recovered ones.

## If you must send the PDF itself (no text available)
- Attach only the first N pages — extract them to a temp PDF, don't ship the whole file.

## Related
- Cost/throughput and empty-response failures: see the `gemini-billing-blocks` skill.

## When to use
Batch classification / tagging / summarization / extraction over many PDFs with an LLM.
