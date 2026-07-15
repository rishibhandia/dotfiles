#!/usr/bin/env python3
"""Search the local Zotero library and print formatted citations.

Copies zotero.sqlite to a temp file first (the live DB is locked while
Zotero.app runs), queries read-only, and deletes the copy afterward.

Usage:
    zotero_query.py merlin coherent          # AND of all terms
    zotero_query.py yamada 2020 --max 5
    zotero_query.py ferron --db /path/zotero.sqlite

Terms match case-insensitively against title, authors, journal, date,
DOI, url, and extra (where arXiv IDs live).
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

DB_DEFAULT = os.path.expanduser("~/Zotero/zotero.sqlite")
FIELDS = ("title", "publicationTitle", "volume", "pages", "date", "DOI", "url", "extra")
SKIP_TYPES = ("attachment", "note", "annotation")


def load_items(cur):
    cur.execute(
        "SELECT i.itemID, it.typeName FROM items i "
        "JOIN itemTypes it ON it.itemTypeID = i.itemTypeID "
        "WHERE it.typeName NOT IN (?, ?, ?) "
        "AND i.itemID NOT IN (SELECT itemID FROM deletedItems)",
        SKIP_TYPES,
    )
    for item_id, type_name in cur.fetchall():
        cur.execute(
            "SELECT f.fieldName, v.value FROM itemData d "
            "JOIN fields f ON f.fieldID = d.fieldID "
            "JOIN itemDataValues v ON v.valueID = d.valueID "
            "WHERE d.itemID = ?",
            (item_id,),
        )
        data = dict(cur.fetchall())
        cur.execute(
            "SELECT c.lastName, c.firstName FROM itemCreators ic "
            "JOIN creators c ON c.creatorID = ic.creatorID "
            "WHERE ic.itemID = ? ORDER BY ic.orderIndex",
            (item_id,),
        )
        authors = cur.fetchall()
        yield item_id, type_name, data, authors


def matches(terms, data, authors):
    hay = " ".join(
        [data.get(f) or "" for f in FIELDS]
        + ["%s %s" % (ln or "", fn or "") for ln, fn in authors]
    ).lower()
    return all(t.lower() in hay for t in terms)


def format_citation(data, authors):
    if authors:
        last, first = authors[0]
        initial = (first or "")[:1]
        name = "%s, %s." % (last, initial) if initial else (last or "?")
        if len(authors) > 2:
            name += " et al."
        elif len(authors) == 2:
            ln2, fn2 = authors[1]
            i2 = (fn2 or "")[:1]
            name += " + %s, %s." % (ln2, i2) if i2 else " + %s" % ln2
    else:
        name = "(no authors)"
    year = (data.get("date") or "")[:4]
    parts = [name]
    if data.get("publicationTitle"):
        journal = data["publicationTitle"]
        if data.get("volume"):
            journal += " %s" % data["volume"]
        if data.get("pages"):
            journal += ", %s" % data["pages"].split("-")[0]
        parts.append(journal)
    cite = ", ".join(parts)
    if year:
        cite += " (%s)" % year
    if data.get("DOI"):
        cite += ". doi:%s" % data["DOI"]
    return cite


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("terms", nargs="+", help="search terms (ANDed)")
    ap.add_argument("--db", default=DB_DEFAULT, help="path to zotero.sqlite")
    ap.add_argument("--max", type=int, default=20, help="max results (default 20)")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        sys.exit("zotero database not found: %s" % args.db)

    fd, tmp = tempfile.mkstemp(suffix=".sqlite", prefix="zotero_ro_")
    os.close(fd)
    try:
        shutil.copyfile(args.db, tmp)
        con = sqlite3.connect("file:%s?mode=ro" % tmp, uri=True)
        try:
            hits = 0
            for item_id, type_name, data, authors in load_items(con.cursor()):
                if not matches(args.terms, data, authors):
                    continue
                hits += 1
                if hits > args.max:
                    print("... more results truncated (--max %d)" % args.max)
                    break
                print("[%d] %s" % (item_id, type_name))
                print("  %s" % format_citation(data, authors))
                if data.get("title"):
                    print("  title: %s" % data["title"])
                if data.get("extra"):
                    extra = " | ".join(data["extra"].splitlines())
                    print("  extra: %s" % extra)
                print()
            if hits == 0:
                print("no matches for: %s" % " ".join(args.terms))
        finally:
            con.close()
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    main()
