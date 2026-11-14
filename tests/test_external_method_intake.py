"""Source-only regression tests for external Skill/Prompt method intake."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/adk-skill-deep-analysis/SKILL.md"
PROMPT = ROOT / "skills/adk-repo-prompt-analysis/SKILL.md"
DETAILS = ROOT / "skills/adk-skill-deep-analysis/references/details.md"
CASES = ROOT / "tests/fixtures/external_method_intake_cases.json"


class ExternalMethodIntakeTests(unittest.TestCase):
    def test_source_only_cases_have_negative_and_authority_coverage(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "adk-external-method-intake/v1")
        self.assertEqual(data["evaluation_status"], "not-measured")
        self.assertGreaterEqual(len(data["cases"]), 10)
        self.assertEqual({x["skill"] for x in data["cases"]}, {"skill", "prompt"})
        ids = [x["id"] for x in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in data["cases"]:
            for key in ("input", "expected", "forbidden"):
                self.assertTrue(case[key].strip(), (case["id"], key))

    def test_skill_method_is_read_only_and_source_grounded(self) -> None:
        s = SKILL.read_text(encoding="utf-8")
        for item in (
            "repo@commit_or_tag", "license", "method-only", "deep-audit",
            "behavior-eval", "symlink", "hooks", "secret", "prompt injection",
            "holdout", "near-miss", "behavior_status=not-measured",
            "ADOPT / MERGE / ENHANCE / OBSERVE / REJECT",
            "adk-skill-composition-governance",
        ):
            self.assertIn(item, s)
        self.assertIn("不得自动安装、写来源仓、更新 adoption matrix", s)
        self.assertIn("不强制", s)
        self.assertIn("仅在需要多候选排名时做 5 维评分", s)

    def test_bounded_public_discovery_cannot_claim_full_coverage(self) -> None:
        source = SKILL.read_text(encoding="utf-8")
        for marker in ("source-discovery", "research_topic", "candidate_count",
                       "verified_count", "unreviewed_reason", "query_scope",
                       "needs-evidence", "source_discovery_status", "不可信数据",
                       "不得执行", "禁止伪称全网覆盖"):
            self.assertIn(marker, source)
        self.assertIn("用于只读发现并对标公开优质 Skills", source)
        self.assertIn("不用于自动安装外部 Skill", source)

    def test_source_to_implementation_handoff_is_bounded(self) -> None:
        deep = SKILL.read_text(encoding="utf-8")
        adoption = (ROOT / "optional-skills/adk-external-practice-absorption/SKILL.md").read_text(
            encoding="utf-8"
        )
        loop = (ROOT / "skills/adk-planning-execution-loop/SKILL.md").read_text(encoding="utf-8")
        behavioral = (ROOT / "optional-skills/adk-skill-composition-governance"
                      / "references/skill-behavior-evaluation.md").read_text(encoding="utf-8")
        for marker in ("Implementable handoff", "source_identity@sha", "runnable_regression",
                       "本 Skill 不写仓", "affected_existing_skill"):
            self.assertIn(marker, deep)
        for marker in ("scoped-adoption", "portfolio-intake", "source-only",
                       "behavior-qualification", "复用现有 ledger/evidence",
                       "not-measured", "独立 owner 决策"):
            self.assertIn(marker, adoption)
        for marker in ("inline fast path", "planned / observed / ruling / evidence / rollback",
                       "共享写集不冲突", "扩大权限"):
            self.assertIn(marker, loop)
        for marker in ("Case isolation", "initial_workspace_ref", "observed_tool_calls",
                       "forbidden_side_effects", "missing_observability"):
            self.assertIn(marker, behavioral)
        competition = (ROOT / "tests/fixtures/skill_catalog_competition.tsv").read_text(
            encoding="utf-8"
        )
        self.assertIn("继续吸收外部成熟方法，提升已有 Skills 的实际执行效果", competition)
        self.assertIn("R041\tnegated\t-\tadk-external-practice-absorption", competition)

    def test_prompt_trace_not_free_text_guess_or_durable_promotion(self) -> None:
        s = PROMPT.read_text(encoding="utf-8")
        for item in (
            "repo@commit_or_tag", "callsite", "role/system/developer/user",
            "untrusted", "false-positive", "needs-fix", "not-measured",
            "adk-context-engineering", "不得直接写入", "只读",
        ):
            self.assertIn(item, s)
        self.assertIn("不是不存在", s)
        self.assertIn("不默认输出完整长报告", s)
        self.assertNotIn("输出可直接用于 adk 的", s)
        self.assertNotIn("5 维评分每项必须", s)

    def test_deferred_reference_has_no_implicit_writes_or_diagrams(self) -> None:
        s = DETAILS.read_text(encoding="utf-8")
        for item in ("非默认加载", "deep-audit", "Mermaid",
                     "不能由“分析”自动写外部仓", "不要求", "不得因 Star"):
            self.assertIn(item, s)


if __name__ == "__main__":
    unittest.main()
