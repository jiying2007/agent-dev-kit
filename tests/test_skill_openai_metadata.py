"""Validate OpenAI Skill UI metadata against the documented interface contract."""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class SkillOpenAIMetadataTests(unittest.TestCase):
    def test_all_present_openai_metadata_use_interface(self) -> None:
        files = sorted(ROOT.glob("skills/*/agents/openai.yaml"))
        self.assertTrue(files, "metadata inventory must not be empty")
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)
                self.assertNotIn("display_name", data)
                self.assertNotIn("short_description", data)
                interface = data.get("interface")
                self.assertIsInstance(interface, dict)
                for key in ("display_name", "short_description"):
                    self.assertIsInstance(interface.get(key), str)
                    self.assertTrue(interface[key].strip())

    def test_missing_interface_is_rejected(self) -> None:
        invalid = yaml.safe_load("display_name: Old layout\nshort_description: Not nested\n")
        self.assertNotIn("interface", invalid)
