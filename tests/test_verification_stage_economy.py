"""Source-only regression for stage-aware completion verification, not host behavior."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/adk-verification-before-completion/SKILL.md"
DETAILS = ROOT / "skills/adk-verification-before-completion/references/verification-governance-details.md"
CASES = ROOT / "tests/fixtures/verification_stage_cases.json"


class VerificationStageEconomyTests(unittest.TestCase):
    def test_stage_and_risk_are_orthogonal_with_fail_closed_gates(self) -> None:
        entry = SKILL.read_text(encoding="utf-8")
        for token in (
            "checkpoint（阶段验收）", "goal-final（整个目标完成）",
            "风险与阶段正交", "low", "medium/high", "原验收分母",
            "claimant", "verifier", "source snapshot",
            "needs-fix", "阶段通过不赋予 commit/merge/release 权限",
            "not_applicable_reason", "whole-lifecycle review",
        ):
            self.assertIn(token, entry)
        self.assertLessEqual(len(entry.encode("utf-8")), 7500)

    def test_full_risk_template_is_deferred_not_removed(self) -> None:
        entry = SKILL.read_text(encoding="utf-8")
        details = DETAILS.read_text(encoding="utf-8")
        self.assertIn("references/verification-governance-details.md", entry)
        self.assertIn("Full Evidence Template", details)
        self.assertIn("Detailed 25-Step Verification Flow", details)
        for token in (
            "Appshots / UI Evidence Boundary", "Runner Smoke Contract",
            "Runtime Control Plane Audit", "Tool / Skill Evidence Plan",
            "Trace Eval Regression Evidence", "Replayable Evidence Bundle",
            "Completion Guard Payload", "Subjective Feature Proof",
            "Lifecycle Operation Evidence", "Review Convergence Evidence",
            "Codify Decision", "promotion_candidate: true",
            "independent_verifier", "runtime_config_diff",
        ):
            self.assertIn(token, entry)
            self.assertIn(token, details)

    def test_checkpoint_does_not_require_full_codify_or_fake_success(self) -> None:
        entry = SKILL.read_text(encoding="utf-8")
        for marker in (
            "checkpoint-deferred", "do_not_promote_reason", "skipped skills",
            "budget", "not_applicable_reason",
        ):
            if marker != "budget":
                self.assertIn(marker, entry)
        self.assertIn("实际命令", entry)
        self.assertIn("未验证", entry)
        self.assertIn("completion_coverage", entry)

    def test_scenario_ledger_declares_hypotheses_not_host_measurements(self) -> None:
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], "adk-verification-stage-cases/v1")
        self.assertEqual(fixture["behavior_status"], "not-measured")
        self.assertEqual({x["kind"] for x in fixture["cases"]},
                         {"checkpoint", "goal-final", "authority-negative"})
        self.assertGreaterEqual(len(fixture["cases"]), 8)
        ids = [x["id"] for x in fixture["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for row in fixture["cases"]:
            for field in ("input", "expected", "forbidden"):
                self.assertTrue(row[field].strip(), (row["id"], field))


if __name__ == "__main__":
    unittest.main()
