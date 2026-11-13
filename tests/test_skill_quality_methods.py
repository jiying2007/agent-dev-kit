"""Source-only tests for conditional review coverage, patch variants and target scope."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/fixtures/skill_quality_methods_cases.json"


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def suite(script: str, name: str) -> list[str]:
    matched = re.search(r"(?ms)^" + name + r"=\(\n(.*?)^\)", script)
    if matched is None:
        raise AssertionError("Missing runner array " + name)
    return [row.strip() for row in matched.group(1).splitlines() if row.strip().endswith(".sh")]


class SkillQualityMethodsTests(unittest.TestCase):
    def test_cases_are_source_only_not_runtime_success(self) -> None:
        payload = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "adk-skill-quality-method-cases/v1")
        self.assertEqual(payload["behavior_status"], "not-measured")
        self.assertGreaterEqual(len(payload["cases"]), 12)
        self.assertEqual({x["skill"] for x in payload["cases"]}, {"review", "test", "embedded", "ci"})
        ids = [x["id"] for x in payload["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for row in payload["cases"]:
            for field in ("input", "expected", "forbidden"):
                self.assertTrue(row[field].strip(), (row["id"], field))

    def test_review_coverage_is_conditional_and_fail_closed(self) -> None:
        review = source("skills/adk-code-review-loop/SKILL.md")
        details = source("skills/adk-code-review-loop/references/review-governance-details.md")
        template = source("skills/adk-code-review-loop/references/review-evidence-template.md")
        self.assertIn("Review Coverage Ledger", review)
        self.assertIn("uninspected", review)
        self.assertIn("不得 pass", review)
        for marker in ("scope_id", "source_snapshot", "inspected|uninspected|unavailable",
                       "evidence_ref", "risk_owner_decision", "feedback-triage",
                       "not-applicable", "不得声称全覆盖"):
            self.assertIn(marker, details)
        self.assertIn("Review Coverage Ledger", template)
        self.assertIn("Uninspected", template)
        self.assertNotIn("- Review Mode: task-level | whole-diff | whole-branch", template)

    def test_patch_validation_requires_variants_and_non_regression(self) -> None:
        details = source("skills/adk-code-review-loop/references/review-governance-details.md")
        test = source("skills/adk-test-strategy/SKILL.md")
        template = source("skills/adk-code-review-loop/references/review-evidence-template.md")
        for token in ("vulnerable_ref", "patched_ref", "original_repro", "related_variants",
                      "legitimate_behavior", "new_risks", "not-tested", "授权"):
            self.assertIn(token, details)
        self.assertIn("同根因变体", test)
        self.assertIn("合法行为保留", test)
        self.assertIn("授权隔离环境", test)
        self.assertIn("Patch Validation", template)

    def test_embedded_tools_bind_target_and_missing_evidence(self) -> None:
        static = source("skills/adk-static-analysis-c-cpp/SKILL.md")
        bsp = source("skills/adk-bsp-analysis/SKILL.md")
        for target in ("linux-embedded", "mcu-rtos", "mcu-baremetal"):
            self.assertIn(target, static)
            self.assertIn(target, bsp)
        for key in ("compile_commands", "not-scanned", "libc", "Zephyr", "独立权限"):
            self.assertIn(key, static)
        self.assertIn("SoC/board/toolchain", bsp)
        self.assertIn("不得以 Zephyr 或 Linux", bsp)

    def test_fast_checks_move_before_expensive_matrix_without_duplication(self) -> None:
        script = source("tests/run_all.sh")
        full = suite(script, "TESTS")
        quick = suite(script, "QUICK_TESTS")
        self.assertEqual(len(full), 102)
        self.assertEqual(len(quick), 61)
        for rows in (full, quick):
            self.assertEqual(len(rows), len(set(rows)))
            self.assertEqual(rows[:5], [
                "test_validate.sh", "test_manifest_contract.sh",
                "test_catalog.sh", "test_skill_content.sh", "test_skill_trigger_matrix.sh",
            ])
            self.assertLess(rows.index("test_catalog.sh"), rows.index("test_strict_json.sh"))
        self.assertLess(full.index("test_skill_sop_quality.sh"), full.index("test_contract_hardening.sh"))
        self.assertNotIn("test_skill_sop_quality.sh", quick)

    def test_real_eval_is_pre_registered_but_unmeasured(self) -> None:
        guide = source("docs/evals/skill-method-parity.md")
        self.assertIn("65 个登记 Skill", guide)
        for marker in ("compare_effect_trial_file", "baseline/candidate", "holdout",
                       "not-measured", "first-pass success", "不少于 3 次",
                       "不能", "无需每小时巡检"):
            self.assertIn(marker, guide)


if __name__ == "__main__":
    unittest.main()
