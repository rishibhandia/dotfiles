---
name: zotero
description: "Query the user's local Zotero library (sqlite) for citations, DOIs, authors, and bibliography entries. Use when the user asks to cite papers, find references 'in my Zotero', build citation lists for presentations/manuscripts, or check whether a paper is in their library."
---

# Zotero Library Lookup

Search the local Zotero SQLite database without an API key or plugin. Never
query the live database in place; the bundled script copies it to a temporary
file, opens that copy read-only, and removes it afterward.

The default database is `~/Zotero/zotero.sqlite`. Run:

```bash
python3 ~/.agents/skills/zotero/scripts/zotero_query.py <terms>
```

Useful forms:

```bash
python3 ~/.agents/skills/zotero/scripts/zotero_query.py yamada 2020
python3 ~/.agents/skills/zotero/scripts/zotero_query.py ferron --max 5
python3 ~/.agents/skills/zotero/scripts/zotero_query.py terms --db /path/zotero.sqlite
```

Whitespace-separated terms are ANDed across title, authors, journal, date,
DOI, URL, and `extra`, using case-insensitive substring matching. Results show
the item type and ID, a formatted citation, the full title, and `extra` when
present.

## Workflow

1. Search for each requested paper using distinctive author, year, or title
   terms.
2. If nothing matches, retry with fewer terms, then clearly report that the
   paper is not in the library.
3. When both a preprint and published article match, prefer the published
   version and say which record was used. Preprints commonly have an arXiv ID
   in `extra`; journal records commonly have `publicationTitle` and a DOI.
4. Use `--db` only for an explicitly supplied alternate library. Do not inspect
   unrelated databases or copy the Zotero database outside a temporary path.

## Caveats

- The database can be about 0.5 GB, so preserve the script's copy/query/delete
  lifecycle and do not leave copies behind.
- Zotero dates are strings; the citation formatter uses their first four
  characters as the year.
- Notes, attachments, and annotations are excluded because citation metadata
  belongs to the parent item.
