import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

sys_dont_write_bytecode = __import__("sys")
sys_dont_write_bytecode.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "ai-parity/shared/skills/pdf-chunk/scripts/pdf_common.py"
STATS = ROOT / "ai-parity/shared/skills/pdf-chunk/scripts/literal_pdf_stats.py"
EXTRACT = ROOT / "ai-parity/shared/skills/pdf-chunk/scripts/literal_extract_pages.py"
TRANSFORM = ROOT / "ai-parity/adapters/skills/pdf/scripts/pdf_transform.py"


def run_script(script, *arguments, path=None):
    environment = os.environ.copy()
    # The bundled scripts import pdf_common from the canonical shared tree;
    # without this the subprocess writes __pycache__ into that tree, which
    # hash_tree correctly rejects on the next parity verify.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if path is not None:
        environment["PATH"] = path
    return subprocess.run(
        ["uv", "run", "--script", str(script), *map(str, arguments)], cwd=ROOT,
        env=environment, text=True, capture_output=True, timeout=180,
    )


def make_pdf(path, count, encrypted=False):
    program = (
        "from pypdf import PdfWriter; import sys; w=PdfWriter(); "
        "[w.add_blank_page(width=72,height=72) for _ in range(int(sys.argv[2]))]; "
        "w.encrypt('secret') if sys.argv[3]=='yes' else None; w.write(sys.argv[1])"
    )
    result = subprocess.run(
        ["uv", "run", "--with", "pypdf>=6,<7", "python", "-c", program,
         str(path), str(count), "yes" if encrypted else "no"],
        text=True, capture_output=True, timeout=180,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)


class PdfCommonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("pdf_common", COMMON)
        cls.common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.common)

    def test_page_selection_is_bounded_and_deduplicated(self):
        self.assertEqual(self.common.parse_pages("1-3,3,5", 5), [1, 2, 3, 5])
        with self.assertRaises(self.common.PdfToolError):
            self.common.parse_pages("4-2", 5)
        with self.assertRaises(self.common.PdfToolError):
            self.common.parse_pages("1;touch", 5)

    def test_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = directory / "input.pdf"
            target = directory / "target.txt"
            link = directory / "output.txt"
            source.write_bytes(b"%PDF")
            target.write_text("preserve")
            link.symlink_to(target)
            with self.assertRaises(self.common.PdfToolError):
                self.common.output_path(str(link), [source], True)
            self.assertEqual(target.read_text(), "preserve")


class PdfIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.first = self.directory / "first.pdf"
        self.second = self.directory / "second.pdf"
        make_pdf(self.first, 3)
        make_pdf(self.second, 2)

    def tearDown(self):
        self.temporary.cleanup()

    def test_stats_reports_physical_page_count(self):
        result = run_script(STATS, self.first, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["page_count"], 3)
        self.assertEqual([item["page"] for item in report["samples"]], [1, 2, 3])

    def test_extract_fallback_is_bounded_and_manifested(self):
        output = self.directory / "extract.txt"
        manifest = self.directory / "extract.json"
        uv = Path(shutil.which("uv"))
        result = run_script(
            EXTRACT, self.first, "--pages", "2-3", "--ocr", "never",
            "--output", output, "--manifest", manifest, path=str(uv.parent),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(manifest.read_text())["selected_pages"], [2, 3])
        self.assertIn("Physical page 2", output.read_text())
        self.assertNotIn("Physical page 1", output.read_text())

    def test_merge_select_and_rotate_preserve_sources(self):
        before = self.first.read_bytes()
        merged = self.directory / "merged.pdf"
        selected = self.directory / "selected.pdf"
        rotated = self.directory / "rotated.pdf"
        commands = (
            ("merge", "--output", merged, self.first, self.second),
            ("select", self.first, "--pages", "1,3", "--output", selected),
            ("rotate", self.first, "--pages", "2", "--degrees", "90", "--output", rotated),
        )
        for arguments in commands:
            result = run_script(TRANSFORM, *arguments)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.first.read_bytes(), before)
        counts = []
        for path in (merged, selected, rotated):
            report = run_script(STATS, path, "--json")
            self.assertEqual(report.returncode, 0, report.stderr)
            counts.append(json.loads(report.stdout)["page_count"])
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(counts, [5, 2, 3])

    def test_encrypted_and_malformed_inputs_fail_explicitly(self):
        encrypted = self.directory / "encrypted.pdf"
        malformed = self.directory / "malformed.pdf"
        make_pdf(encrypted, 1, encrypted=True)
        malformed.write_bytes(b"%PDF-1.7\nnot a document")
        encrypted_result = run_script(EXTRACT, encrypted, "--pages", "1", "--ocr", "never")
        malformed_result = run_script(STATS, malformed)
        self.assertNotEqual(encrypted_result.returncode, 0)
        self.assertIn("encrypted", encrypted_result.stderr.lower())
        self.assertNotEqual(malformed_result.returncode, 0)
        self.assertIn("cannot parse", malformed_result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
