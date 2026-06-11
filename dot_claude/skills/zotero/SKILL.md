---
name: zotero
description: "Query the user's local Zotero library (sqlite) for citations, DOIs, authors, and bibliography entries. Use when the user asks to cite papers, find references 'in my Zotero', build citation lists for presentations/manuscripts, or check whether a paper is in their library."
---

# Zotero Library Lookup

Query the local Zotero sqlite database directly — no Zotero API key, no
plugins, works while Zotero.app is running.

**Database:** `~/Zotero/zotero.sqlite` (~0.5 GB; locked while Zotero is
open — never query it in place).

## Quick Reference

| Task | Command |
|------|---------|
| Search library | `python3 ~/.claude/skills/zotero/scripts/zotero_query.py merlin coherent` |
| Search by author + year | `zotero_query.py yamada 2020` |
| Limit results | `zotero_query.py ferron --max 5` |
| Custom DB path | `zotero_query.py terms --db /path/zotero.sqlite` |

All whitespace-separated terms are ANDed across title, authors, journal,
date, DOI, and extra fields (case-insensitive substring match).

Output per item: itemID, type, formatted citation (`Lastname, F. et al.,
Journal vol, pages (year). doi:...`), full title, and the extra field
(where arXiv IDs live).

## Workflow

1. Run `zotero_query.py <terms>` for each paper the user mentions.
2. If nothing matches, retry with fewer/looser terms (last name only;
   distinctive title word). Report papers NOT in the library explicitly —
   the user may want to add them before citing.
3. Prefer the published version when both a preprint and the journal
   article are in the library (preprints have an arXiv ID in `extra` and
   usually no `publicationTitle`). Check both and say which you used.

## Raw SQL (when the script isn't enough)

The script copies the DB to a temp file automatically. For manual
queries do the same — the live DB is locked by Zotero:

```bash
cp ~/Zotero/zotero.sqlite /tmp/zotero_ro.sqlite
sqlite3 /tmp/zotero_ro.sqlite "<query>"
rm /tmp/zotero_ro.sqlite   # always clean up — it's ~0.5 GB
```

### Schema cheat sheet

- `items` — one row per item; join `itemTypes` for `typeName`
  (filter out `attachment`, `note`, `annotation`)
- `itemData` → `fields` (fieldName) + `itemDataValues` (value) —
  EAV layout: title, publicationTitle, volume, pages, date, DOI, url,
  extra all live here
- `itemCreators` → `creators` (lastName, firstName) — order authors by
  `itemCreators.orderIndex`
- `deletedItems` — trash; exclude with
  `itemID NOT IN (SELECT itemID FROM deletedItems)`
- `collections` + `collectionItems` — folder structure, if needed

### Example: title + DOI for items matching a word

```sql
SELECT i.itemID,
  MAX(CASE WHEN f.fieldName='title' THEN v.value END) AS title,
  MAX(CASE WHEN f.fieldName='DOI'   THEN v.value END) AS doi
FROM items i
JOIN itemData d  ON d.itemID = i.itemID
JOIN fields f    ON f.fieldID = d.fieldID
JOIN itemDataValues v ON v.valueID = d.valueID
WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
GROUP BY i.itemID
HAVING title LIKE '%ferron%';
```

### Example: ordered author list for one item

```sql
SELECT c.lastName, c.firstName
FROM itemCreators ic JOIN creators c ON c.creatorID = ic.creatorID
WHERE ic.itemID = 1234 ORDER BY ic.orderIndex;
```

## Caveats

- **Copy, query, delete.** Querying the live DB fails with "database is
  locked" while Zotero runs; leaving 0.5 GB copies in /tmp adds up.
- `date` is a string like `2025-02-21` or `2026-00-00` — take the first
  4 chars for the year.
- Preprint vs published duplicates are common; `extra` holds the arXiv
  ID, journal articles hold `publicationTitle` + `DOI`.
- Item notes/PDF attachments are separate child items — the metadata
  above lives on the parent.
