"""Source-only regressions for method-efficiency Skills; not an LLM A/B."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "task": "skills/adk-task-breakdown/SKILL.md",
    "parallel": "skills/adk-parallel-agent-governance/SKILL.md",
    "test": "skills/adk-test-strategy/SKILL.md",
    "growth": "skills/adk-engineering-growth-review/SKILL.md",
    "review": "skills/adk-code-review-loop/SKILL.md",
}

class SkillMethodEfficiencyTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (ROOT / FILES[name]).read_text(encoding="utf-8")

    def test_design_cases_not_model_success(self) -> None:
        doc = json.loads((ROOT / "tests/fixtures/skill_method_efficiency_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "adk-skill-method-efficiency-cases/v1")
        self.assertEqual(doc["behavior_status"], "not-measured")
        self.assertGreaterEqual(len(doc["cases"]), 16)
        ids = [row["id"] for row in doc["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({row["skill"] for row in doc["cases"]}, set(FILES))
        for row in doc["cases"]:
            for key in ("prompt", "expected", "forbidden"):
                self.assertTrue(row[key].strip(), row["id"])

    def test_small_work_does_not_force_heavy_plan_or_parallel(self) -> None:
        task, parallel = self.read("task"), self.read("parallel")
        self.assertIn("不硬套 0.5–8h", task)
        self.assertIn("not-estimated", task)
        self.assertIn("single-slice", task)
        self.assertIn("Ready Frontier", task)
        self.assertIn("不为满足 2–4 个任务", parallel)
        self.assertIn("Parallel Suitability: no", parallel)
        self.assertIn("无新状态不循环调用模型等待", parallel)

    def test_authority_coverage_survives_compaction(self) -> None:
        task, parallel, test, growth = (self.read(name) for name in ("task", "parallel", "test", "growth"))
        for token in ("adk-task-package-schema-v2", "structured_output_schema",
                      "strict_schema_decision", "refusal_handling", "implementation_permission",
                      "prototype_evidence", "global_constraints", "interfaces", "ready_to_handoff"):
            self.assertIn(token, task)
        for token in ("templates/planning/worker-contract.md", "context_noise_budget",
                      "report_schema", "must_not_touch", "primary_skill", "data-only",
                      "task-package v2", "whole-diff", "raw_output_retention_decision",
                      "parent_merge_policy", "redaction_status", "context-only",
                      "stable work-item ID", "Worker"):
            self.assertIn(token, parallel)
        self.assertIn("Validation Resource Matrix:", test)
        self.assertIn("RED → GREEN → REFACTOR", test)
        self.assertIn("not-tested", test)
        for token in ("index-first", "trace-feedback-eval-handoff", "human approval",
                      "insufficient-evidence"):
            self.assertIn(token, growth)
        for reference in (
            "skills/adk-task-breakdown/references/task-packaging.md",
            "skills/adk-parallel-agent-governance/references/parallel-worktree-task-package.md",
            "skills/adk-engineering-growth-review/references/growth-evidence-boundaries.md",
        ):
            self.assertTrue((ROOT / reference).is_file(), reference)

    def test_feedback_triage_remains_read_only_and_non_final(self) -> None:
        review = self.read("review")
        for term in ("feedback-triage", "false-positive", "Snapshot ID",
                     "cannot-verify-from-diff", "Final Verdict: pass",
                     "Final Readiness: true", "whole-diff-review", "whole-lifecycle-review",
                     "author-self-review", "blocker=0", "schema-backed findings",
                     "untrusted PR", "design-change"):
            self.assertIn(term, review)
        self.assertIn("不强制 whole-diff/全量 CI/额外 reviewer", review)
        self.assertIn("不能**替代最终", review)
        self.assertIn("不自动批准", review)

    def test_no_new_global_skill_or_injected_lifecycle(self) -> None:
        guide = (ROOT / "docs/changes/20261113-skill-method-efficiency/design.md").read_text(encoding="utf-8")
        self.assertIn("not create a new Agent/Skill/Workflow", guide)
        self.assertIn("not-measured", guide)

    def test_task_timeout_is_failure_not_discarded_as_incomplete(self) -> None:
        guide = (ROOT / "optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md").read_text(encoding="utf-8")
        task = next(line for line in guide.splitlines() if "（task-timeout）" in line)
        infrastructure = next(line for line in guide.splitlines() if "（infrastructure-timeout）" in line)
        for term in ("预注册", "有效 task failure", "保留在任务分母中",
                     "不得", "删除失败样本", "用量"):
            self.assertIn(term, task)
        self.assertNotIn("invalid-eval", task)
        for term in ("基础设施/采集链路超时", "invalid-eval / INCOMPLETE",
                     "保留全组", "成对重跑", "不选择性重试",
                     "无法区分超时来源时保持原因未明"):
            self.assertIn(term, infrastructure)

if __name__ == "__main__":
    unittest.main()
