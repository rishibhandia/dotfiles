from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "ai-parity/shared/skills/zotero/scripts/zotero_query.py"


class ZoteroQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="zotero-query-test-")
        self.root = Path(self.temporary.name)
        self.database = self.root / "zotero.sqlite"
        self.query_tmp = self.root / "tmp"
        self.query_tmp.mkdir()
        self._create_database()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_database(self) -> None:
        connection = sqlite3.connect(self.database)
        connection.executescript(
            """
            CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
            CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INTEGER);
            CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
            CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
            CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER);
            CREATE TABLE creators (
                creatorID INTEGER PRIMARY KEY, lastName TEXT, firstName TEXT
            );
            CREATE TABLE itemCreators (
                itemID INTEGER, creatorID INTEGER, orderIndex INTEGER
            );
            CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY);
            """
        )
        connection.executemany(
            "INSERT INTO itemTypes VALUES (?, ?)",
            ((1, "journalArticle"), (2, "preprint"), (3, "attachment")),
        )
        fields = (
            "title", "publicationTitle", "volume", "pages",
            "date", "DOI", "url", "extra",
        )
        connection.executemany(
            "INSERT INTO fields VALUES (?, ?)", enumerate(fields, start=1)
        )
        field_ids = {name: index for index, name in enumerate(fields, start=1)}
        next_value = 1

        def add_item(item_id: int, item_type: int, data: dict[str, str]) -> None:
            nonlocal next_value
            connection.execute("INSERT INTO items VALUES (?, ?)", (item_id, item_type))
            for name, value in data.items():
                connection.execute(
                    "INSERT INTO itemDataValues VALUES (?, ?)", (next_value, value)
                )
                connection.execute(
                    "INSERT INTO itemData VALUES (?, ?, ?)",
                    (item_id, field_ids[name], next_value),
                )
                next_value += 1

        add_item(10, 1, {
            "title": "Coherent Merlin Dynamics",
            "publicationTitle": "Physical Review Letters",
            "volume": "42",
            "pages": "10-20",
            "date": "2020-02-21",
            "DOI": "10.1234/example",
            "url": "https://example.test/merlin",
            "extra": "Project: THz",
        })
        add_item(20, 2, {
            "title": "Ferron modes in layered materials",
            "date": "2024-00-00",
            "extra": "arXiv:2401.00001",
        })
        add_item(30, 1, {
            "title": "Published ferron spectroscopy",
            "publicationTitle": "Nature Physics",
            "date": "2025",
            "DOI": "10.5678/ferron",
        })
        add_item(40, 3, {"title": "Ferron supplementary PDF"})
        add_item(50, 1, {"title": "Deleted ferron article"})
        connection.execute("INSERT INTO deletedItems VALUES (50)")

        creators = (
            (1, "Yamada", "Akira"),
            (2, "Lee", "Beatrice"),
            (3, "Chen", "Carla"),
            (4, "Smith", "Dana"),
        )
        connection.executemany("INSERT INTO creators VALUES (?, ?, ?)", creators)
        connection.executemany(
            "INSERT INTO itemCreators VALUES (?, ?, ?)",
            ((10, 1, 0), (10, 2, 1), (10, 3, 2), (20, 4, 0)),
        )
        connection.commit()
        connection.close()

    def run_query(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        before = hashlib.sha256(self.database.read_bytes()).digest()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments, "--db", str(self.database)],
            text=True,
            capture_output=True,
            env={**os.environ, "TMPDIR": str(self.query_tmp)},
        )
        self.assertEqual(before, hashlib.sha256(self.database.read_bytes()).digest())
        self.assertEqual([], list(self.query_tmp.glob("zotero_ro_*.sqlite")))
        return result

    def test_terms_are_anded_across_metadata_and_authors(self) -> None:
        result = self.run_query("MERLIN", "yamada", "2020")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[10] journalArticle", result.stdout)
        self.assertIn(
            "Yamada, A. et al., Physical Review Letters 42, 10 (2020). "
            "doi:10.1234/example",
            result.stdout,
        )
        self.assertNotIn("[20]", result.stdout)

    def test_max_truncates_only_searchable_parent_items(self) -> None:
        result = self.run_query("ferron", "--max", "1")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[20] preprint", result.stdout)
        self.assertIn("... more results truncated (--max 1)", result.stdout)
        self.assertNotIn("[40]", result.stdout)
        self.assertNotIn("[50]", result.stdout)

    def test_no_match_is_explicit(self) -> None:
        result = self.run_query("missing", "reference")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("no matches for: missing reference\n", result.stdout)

    def test_missing_database_fails_without_temp_copy(self) -> None:
        missing = self.root / "missing.sqlite"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "paper", "--db", str(missing)],
            text=True,
            capture_output=True,
            env={**os.environ, "TMPDIR": str(self.query_tmp)},
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("zotero database not found", result.stderr)
        self.assertEqual([], list(self.query_tmp.iterdir()))


if __name__ == "__main__":
    unittest.main()
