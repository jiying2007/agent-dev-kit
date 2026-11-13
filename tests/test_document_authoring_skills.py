"""Source-only document-authoring quality tests, not native model evaluation."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "adk-adr-writer": "skills/adk-adr-writer/SKILL.md",
    "adk-after-action-review": "skills/adk-after-action-review/SKILL.md",
    "adk-incident-rca-report": "optional-skills/adk-incident-rca-report/SKILL.md",
    "adk-cross-team-handoff": "skills/adk-cross-team-handoff/SKILL.md",
    "adk-requirements-triage": "skills/adk-requirements-triage/SKILL.md",
    "adk-lightweight-planning": "skills/adk-lightweight-planning/SKILL.md",
    "adk-knowledge-archive": "skills/adk-knowledge-archive/SKILL.md",
    "adk-prose-revision": "optional-skills/adk-prose-revision/SKILL.md",
}

class DocumentAuthoringSkillTests(unittest.TestCase):
    def content(self, name: str) -> str:
        return (ROOT / FILES[name]).read_text(encoding="utf-8")

    def test_source_case_coverage_not_model_evidence(self) -> None:
        data = json.loads((ROOT / "tests/fixtures/document_authoring_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "adk-document-authoring-source-cases/v1")
        self.assertEqual(data["evaluation_status"], "not-measured")
        self.assertGreaterEqual(len(data["cases"]), 15)
        self.assertEqual({v["skill"] for v in data["cases"]}, set(FILES))
        ids = [row["id"] for row in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for row in data["cases"]:
            for key in ("mode", "input", "expected"):
                self.assertTrue(row[key].strip())

    def test_preserve_evidence_and_optional_prose_boundary(self) -> None:
        doc = (ROOT / "docs/runbooks/document-authoring-quality.md").read_text(encoding="utf-8")
        self.assertIn("不是新的 Skill", doc)
        self.assertIn("显式安装", doc)
        self.assertIn("not-measured", doc)
        for name in FILES.keys() - {"adk-prose-revision"}:
            with self.subTest(name=name):
                self.assertIn("文档保真", self.content(name))

    def test_known_overconstraint_regressions(self) -> None:
        adr = self.content("adk-adr-writer")
        aar = self.content("adk-after-action-review")
        rca = self.content("adk-incident-rca-report")
        handoff = self.content("adk-cross-team-handoff")
        req = self.content("adk-requirements-triage")
        plan = self.content("adk-lightweight-planning")
        self.assertIn("不编造第二方案", adr)
        self.assertIn("memory_candidates: []", aar)
        self.assertIn("trace-feedback-eval-handoff", aar)
        self.assertIn("5-Why 为可选分析工具", rca)
        self.assertIn("unresolved", rca)
        self.assertIn("不得自动修改权限或回滚设备", handoff)
        for field in ("done-when", "required evidence", "artifact paths", "blocker policy"):
            self.assertIn(field, req)
        self.assertIn("不可把高风险任务降为 brief", req)
        self.assertIn("不强制 4–10 项", plan)
        self.assertNotIn("5-Why 分析必须至少穿透到第 3 层", rca)
        self.assertNotIn("签收记录必须包含三方签字", handoff)

if __name__ == "__main__":
    unittest.main()
