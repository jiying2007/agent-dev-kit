"""Require complete, localized OpenAI UI metadata for each declared Skill.

Source validation only: it does not certify any installed native host or model behavior.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[\u3400-\u9fff]")


class SkillOpenAIMetadataTests(unittest.TestCase):
    def test_manifest_skills_have_unique_chinese_openai_metadata(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        records = manifest["skills"] + manifest["optional_skills"]
        expected = {ROOT / row["path"].replace("SKILL.md", "agents/openai.yaml") for row in records}
        found = set((ROOT / "skills").glob("*/agents/openai.yaml"))
        found.update((ROOT / "optional-skills").rglob("agents/openai.yaml"))
        self.assertEqual(found, expected, f"missing={expected-found}, unexpected={found-expected}")
        names: set[str] = set()
        for row in records:
            path = ROOT / row["path"].replace("SKILL.md", "agents/openai.yaml")
            with self.subTest(skill=row["name"]):
                raw = path.read_text(encoding="utf-8")
                data = yaml.safe_load(raw)
                self.assertIsInstance(data, dict)
                self.assertNotIn("display_name", data)
                self.assertNotIn("short_description", data)
                interface = data.get("interface")
                self.assertIsInstance(interface, dict)
                title = interface.get("display_name")
                desc = interface.get("short_description")
                self.assertIsInstance(title, str)
                self.assertIsInstance(desc, str)
                self.assertRegex(title, HAN)
                self.assertRegex(desc, HAN)
                self.assertTrue(25 <= len(desc) <= 64, (row["name"], len(desc)))
                self.assertNotIn(title, names)
                names.add(title)
                self.assertRegex(raw, r'(?m)^  display_name: "')
                self.assertRegex(raw, r'(?m)^  short_description: "')
                prompt = interface.get("default_prompt")
                if prompt is not None:
                    self.assertIsInstance(prompt, str)
                    self.assertIn("$" + row["name"], prompt)
                policy = data.get("policy")
                if policy is not None:
                    self.assertIsInstance(policy, dict)
                    self.assertIsInstance(policy.get("allow_implicit_invocation"), bool)

    def test_non_primary_skills_are_explicit_only_in_host_ui(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        non_primary = {
            "adk-context-engineering",
            "adk-artifact-gating",
            "adk-cross-team-handoff",
            "adk-data-fetch",
            "adk-email-imap-fetch",
            "adk-fetch-url-content",
            "adk-incident-rca-report",
        }
        expected = set()
        for row in manifest["skills"] + manifest["optional_skills"]:
            path = ROOT / row["path"].replace("SKILL.md", "agents/openai.yaml")
            meta = yaml.safe_load(path.read_text(encoding="utf-8"))
            policy = meta.get("policy", {})
            if row["name"] in non_primary:
                self.assertIs(policy.get("allow_implicit_invocation"), False, row["name"])
                expected.add(row["name"])
            else:
                self.assertNotIn("allow_implicit_invocation", policy, row["name"])
        self.assertEqual(non_primary, expected)

    def test_explicit_only_metadata_does_not_erase_chinese_prompt(self) -> None:
        path = ROOT / "optional-skills/adk-external-practice-absorption/agents/openai.yaml"
        meta = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertNotIn("policy", meta)
        self.assertIn("$adk-external-practice-absorption", meta["interface"]["default_prompt"])

    def test_missing_interface_is_rejected(self) -> None:
        invalid = yaml.safe_load("display_name: Old layout\nshort_description: Not nested\n")
        self.assertNotIn("interface", invalid)


if __name__ == "__main__":
    unittest.main()
