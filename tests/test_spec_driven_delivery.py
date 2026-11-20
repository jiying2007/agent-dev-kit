"""Deterministic SDD routing and source-contract regression; not model/field proof."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class SpecDrivenDeliveryTests(unittest.TestCase):
    def test_route_reuses_existing_skill_not_runtime(self) -> None:
        manifest = Manifest.load(ROOT)
        for prompt in ("SDD驱动", "规格驱动开发"):
            with self.subTest(prompt=prompt):
                result = match_text(manifest, prompt, scope="auto")
                self.assertTrue(result.get("match"), result)
                self.assertEqual(result.get("skill"), "adk-requirements-triage", result)
                self.assertEqual(result.get("mutation_permission"), "deny", result)
        data = json.loads(read("manifest.json"))
        self.assertEqual((len(data["workflows"]), len(data["skills"]), len(data["optional_skills"])), (7, 56, 9))
        route = [x for x in data["routing"]["intents"] if x["intent"] == "spec_driven_delivery"]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]["task_mode"], "readonly")

    def test_canonical_contract_with_three_real_paths(self) -> None:
        workspace = read("docs/changes/README.md")
        workflow = read("workflows/feature-delivery/WORKFLOW.md")
        guide = read("docs/runbooks/spec-driven-delivery.md")
        self.assertIn("Canonical Change Contract", workspace)
        for marker in ("REQ-NNN", "ACC-NNN", "TASK-NNN", "VERIFY-NNN", "ADDED/MODIFIED/REMOVED", "spec → code → test"):
            self.assertTrue(marker in guide or marker in workflow, marker)
        for marker in ("小修", "SoC ↔ MCU UART", "not-tested", "飞书项目", "TAPD"):
            self.assertIn(marker, guide)
        self.assertIn("propose/apply/verify/review/archive", workflow)
        self.assertIn("不新增 Spec 引擎", guide)
        self.assertIn("not-measured", guide)
        self.assertNotIn("仍可运行", read("changes/README.md"))

    def test_skill_handoffs_and_unsafe_completion_visible(self) -> None:
        markers = {
            "skills/adk-structured-requirements-questioning/SKILL.md": ("反证优先", "可证伪", "退出", "不授予"),
            "skills/adk-requirements-triage/SKILL.md": ("Canonical Change Contract", "TAPD", "行为变化"),
            "skills/adk-interface-contract-design/SKILL.md": ("protocol/spec@digest", "重复/乱序", "not-tested"),
            "skills/adk-task-breakdown/SKILL.md": ("Spec-to-slice", "REQ-NNN/ACC-NNN", "VERIFY-NNN"),
        }
        for path, required in markers.items():
            with self.subTest(path=path):
                content = read(path)
                for marker in required:
                    self.assertIn(marker, content)
        self.assertIn("not-measured", read("docs/evals/interactive-discovery-evaluation.md"))


if __name__ == "__main__":
    unittest.main()
