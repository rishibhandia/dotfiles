import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

sys_dont_write_bytecode = __import__("sys")
sys_dont_write_bytecode.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "ai-parity/shared/skills/keynote/scripts/literal_keynote_layout.py"
AUDIT = ROOT / "ai-parity/shared/skills/keynote/scripts/literal_keynote_audit.py"
BRIDGE = ROOT / "ai-parity/shared/skills/keynote/scripts/literal_keynote_bridge.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KeynoteLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = load_module("keynote_layout", LAYOUT)
        cls.bridge = load_module("keynote_bridge", BRIDGE)

    def test_applescript_string_escapes_special_characters(self):
        self.assertEqual(
            self.bridge.applescript_string('quoted "text" and \\alpha\nnext'),
            '"quoted \\"text\\" and \\\\alpha\\nnext"',
        )

    def test_hex_color_converts_to_keynote_channels(self):
        self.assertEqual(self.layout.hex_color("#FF8000"), (65535, 32896, 0))
        with self.assertRaises(self.layout.LayoutError):
            self.layout.hex_color("orange")

    def test_table_json_must_be_rectangular_and_scalar(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "table.json"
            path.write_text(json.dumps([["Metric", "Value"], ["Accuracy", 0.98]]))
            self.assertEqual(self.layout.load_table(path), [["Metric", "Value"], ["Accuracy", 0.98]])
            path.write_text(json.dumps([[1, 2], [3]]))
            with self.assertRaises(self.layout.LayoutError):
                self.layout.load_table(path)


class KeynoteAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module("keynote_audit", AUDIT)

    def test_audit_flags_accessibility_overlap_and_small_text(self):
        inventory = {
            "canvas": {"width": 1000, "height": 700},
            "slides": {
                "slide-0": {
                    "items": [
                        {
                            "type": "text", "index": 1,
                            "position": [100, 100], "size": [300, 100],
                            "font_size": 14,
                        },
                        {
                            "type": "image", "index": 1,
                            "position": [150, 120], "size": [200, 120],
                            "description": "",
                        },
                    ]
                }
            },
        }
        findings = self.audit.audit_inventory(inventory)
        codes = {finding["code"] for finding in findings}
        self.assertEqual(codes, {"small-text", "missing-alt-text", "overlap"})

    def test_audit_flags_off_canvas_items(self):
        inventory = {
            "canvas": {"width": 1000, "height": 700},
            "slides": {
                "slide-0": {
                    "items": [{
                        "type": "table", "index": 1,
                        "position": [900, 600], "size": [200, 200],
                    }]
                }
            },
        }
        findings = self.audit.audit_inventory(inventory)
        self.assertEqual([finding["code"] for finding in findings], ["off-canvas"])


if __name__ == "__main__":
    unittest.main()
