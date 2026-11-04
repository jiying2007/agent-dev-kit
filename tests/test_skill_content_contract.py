"""Skill content v2 checks without obsolete line-count or fixed-heading constraints."""
from __future__ import annotations
import json
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


class SkillContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_all_registered_skill_frontmatter_and_body(self) -> None:
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        self.assertEqual(len({item["name"] for item in items}), len(items))
        for item in items:
            path = ROOT / item["path"]
            with self.subTest(path=item["path"]):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"))
                _, header, body = content.split("---", 2)
                meta = yaml.safe_load(header)
                self.assertIsInstance(meta, dict)
                self.assertEqual(meta.get("name"), item["name"])
                self.assertTrue(isinstance(meta.get("description"), str) and meta["description"].strip())
                self.assertLessEqual(len(meta["description"]), 1024)
                self.assertTrue(body.strip())
                self.assertTrue(isinstance(meta.get("triggers"), list) and meta["triggers"])
                self.assertIsInstance(meta.get("non_triggers"), list)

    def test_no_language_duplicate_skill_and_counts_match(self) -> None:
        names = {v["name"] for t in ("skills", "optional_skills") for v in self.manifest[t]}
        self.assertFalse(any(n.startswith(("adk-chinese-", "adk-english-")) for n in names))
        for n in ("adk-chinese-code-review", "adk-chinese-commit-conventions"):
            self.assertFalse((ROOT / "skills" / n).exists())
        policy = json.loads((ROOT / "manifests/content_architecture_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.manifest["skills"]), policy["identity_baseline"]["core_skill_count"])
        self.assertEqual(len(self.manifest["optional_skills"]), policy["identity_baseline"]["optional_skill_count"])


    def test_review_skill_entries_have_real_goal_and_no_placeholder(self) -> None:
        # Targeted regression for reviewed defects, not a new global heading/length gate.
        for name in ("adk-repo-prompt-analysis", "adk-skill-deep-analysis"):
            with self.subTest(skill=name):
                content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                body = content.split("---", 2)[2]
                self.assertEqual(body.count("## Goal\\n"), 1)
                self.assertNotIn("## Goal\\n## Prerequisites", body)
                self.assertNotIn("<what-to-do>", body)
                self.assertIn("## Workflow", body)
        skill = (ROOT / "skills/adk-skill-deep-analysis/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("# Skill 设计与可迁移实践深度评估", skill)

    def test_details_are_supplemental_not_duplicate_skills(self) -> None:
        for path in ROOT.glob("skills/*/references/details.md"):
            with self.subTest(path=path.name, parent=path.parent.parent.name):
                content = path.read_text(encoding="utf-8")
                self.assertFalse(content.startswith("---\n"))
                self.assertNotIn("## Workflow\n", content)
