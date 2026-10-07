"""Frontmatter compatibility and safe constructors on both YAML engines."""

import json
import unittest
from pathlib import Path
from unittest import mock

import yaml

from agent_dev_kit.safe_yaml import safe_load


class SafeYAMLTests(unittest.TestCase):
    def test_actual_asset_frontmatter_matches_original_safe_loader(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        for section in ("agents", "skills", "optional_skills"):
            for record in manifest[section]:
                path = root / record["path"]
                text = path.read_text(encoding="utf-8")
                if text.startswith("---\n"):
                    header = text[4:].split("\n---\n", 1)[0]
                    with self.subTest(path=record["path"]):
                        self.assertEqual(yaml.safe_load(header), safe_load(header))

    def test_unicode_scalars_aliases_and_dates_match(self):
        text = "name: 中文\nvalues: &values [true, null, 0x10, 'yes']\ncopy: *values\ndate: 2026-10-07\n"
        self.assertEqual(yaml.safe_load(text), safe_load(text))

    def test_python_object_constructor_is_rejected(self):
        with self.assertRaises(yaml.YAMLError):
            safe_load("!!python/object/apply:builtins.eval ['40 + 2']")

    def test_malformed_input_is_rejected(self):
        with self.assertRaises(yaml.YAMLError):
            safe_load("values: [unterminated")

    def test_missing_c_extension_preserves_safe_python_parser(self):
        if hasattr(yaml, "CSafeLoader"):
            with mock.patch.object(yaml, "CSafeLoader"):
                del yaml.CSafeLoader
                self.assertEqual({"name": "中文"}, safe_load("name: 中文"))
                with self.assertRaises(yaml.YAMLError):
                    safe_load("!!python/object/apply:builtins.eval ['40 + 2']")
        else:
            self.assertEqual({"name": "中文"}, safe_load("name: 中文"))


if __name__ == "__main__":
    unittest.main()
