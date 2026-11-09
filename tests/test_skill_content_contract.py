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

    def test_registered_skill_markdown_fences_closed(self) -> None:
        """Regression for a real unclosed shell fence in interface-contract-design."""
        def balanced(text: str) -> bool:
            open_fence = False
            for line in text.splitlines():
                if line.lstrip().startswith("```"):
                    open_fence = not open_fence
            return not open_fence

        self.assertFalse(balanced("## Example\\n```bash\\necho one\\n"))
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        for item in items:
            with self.subTest(skill=item["name"]):
                source = (ROOT / item["path"]).read_text(encoding="utf-8")
                self.assertTrue(balanced(source), item["path"])

    def test_skill_method_cases_are_not_fabricated_model_results(self) -> None:
        fixture = json.loads((ROOT / "tests/fixtures/skill_method_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], "adk-skill-method-review-cases/v1")
        self.assertEqual(fixture["behavior_status"], "not-measured")
        cases = fixture["cases"]
        self.assertGreaterEqual(len(cases), 8)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        expected = {"debug-feedback", "tdd-public-seam", "architecture-deep-module",
                    "domain-counterexample", "tracer-slice", "throwaway-prototype",
                    "skill-red-green", "approval-negative"}
        self.assertTrue(expected <= {c["id"] for c in cases})
        for case in cases:
            self.assertIn(case["mode"], {"positive", "negative", "adversarial"})
            for field in ("prompt", "target_skill", "expected_behavior", "reject_behavior"):
                self.assertTrue(isinstance(case[field], str) and case[field].strip(), (case["id"], field))
        refs = [
            "skills/adk-interface-contract-design/references/design-quality-methods.md",
            "skills/adk-code-simplification/references/deep-module-design.md",
            "skills/adk-systematic-debugging/references/tight-feedback-loop.md",
            "skills/adk-test-strategy/references/high-value-tdd.md",
            "skills/adk-task-breakdown/references/vertical-slice-planning.md",
            "skills/adk-structured-requirements-questioning/references/prototype-as-experiment.md",
            "optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md",
            "docs/evals/skill-method-parity.md",
        ]
        for path in refs:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn("not-measured", (ROOT / "docs/evals/skill-method-parity.md").read_text(encoding="utf-8"))

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
                self.assertEqual(body.count("## Goal\n"), 1)
                self.assertNotIn("## Goal\n## Prerequisites", body)
                self.assertNotIn("<what-to-do>", body)
                self.assertNotIn("</what-to-do>", body)
                self.assertNotIn("<supporting-info>", body)
                self.assertNotIn("</supporting-info>", body)
                self.assertIn("## Workflow", body)
        skill = (ROOT / "skills/adk-skill-deep-analysis/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("# Skill 设计深度审查", skill)


    def test_all_skill_shell_references_use_declared_adk_commands(self) -> None:
        import re
        from agent_dev_kit.cli_runtime import PUBLIC_COMMANDS

        allowed = {command for command, _ in PUBLIC_COMMANDS}
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        for item in items:
            text = (ROOT / item["path"]).read_text(encoding="utf-8")
            blocks = re.findall(r"```(?:bash|sh)\n([\s\S]*?)\n```", text)
            with self.subTest(skill=item["name"]):
                for block in blocks:
                    for command in re.findall(r"scripts/devkit\.sh\s+([a-z][a-z-]*)", block):
                        self.assertIn(command, allowed, (item["name"], command))
                    for script in re.findall(
                        r"(?m)^(?:rtk\s+)?(?:bash|python3?)\s+(scripts/[A-Za-z0-9_./-]+\.(?:sh|py))\b",
                        block,
                    ):
                        self.assertTrue((ROOT / script).is_file(), (item["name"], script))
                self.assertNotRegex(text, r"devkit\.sh\s+verify\s+--analysis")

    def test_fault_injection_defaults_never_write_live_device(self) -> None:
        import re

        text = (ROOT / "skills/adk-fault-injection-recovery/SKILL.md").read_text(encoding="utf-8")
        section = text.split("## Commands", 1)[1].split("## Evidence Template", 1)[0]
        for pattern in (
            r"(?m)^\s*echo\s+.*>\s*/sys/kernel/debug",
            r"(?m)^\s*echo\s+.*>\s*/dev/watchdog",
            r"(?m)^\s*stress-ng\s+.*--vm",
        ):
            self.assertIsNone(re.search(pattern, section))
        self.assertIn("独立设备操作者", section)
        self.assertIn("not_evaluated", section)

    def test_details_are_supplemental_not_duplicate_skills(self) -> None:
        for path in ROOT.glob("skills/*/references/details.md"):
            with self.subTest(path=path.name, parent=path.parent.parent.name):
                content = path.read_text(encoding="utf-8")
                self.assertFalse(content.startswith("---\n"))
                self.assertNotIn("## Workflow\n", content)
