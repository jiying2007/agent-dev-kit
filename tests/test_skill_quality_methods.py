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


    def test_external_skill_references_are_source_pinned_and_not_installed(self) -> None:
        content = source("docs/evals/external-skill-method-comparison-20261114.md")
        rows = [line for line in content.splitlines() if line.startswith("| [") and "](https://github.com/" in line]
        self.assertEqual(len(rows), 22)
        self.assertEqual(sum("ENHANCE" in row for row in rows), 8)
        self.assertEqual(sum("RETAIN" in row for row in rows), 11)
        self.assertEqual(sum("OBSERVE" in row for row in rows), 3)
        for row in rows:
            self.assertRegex(row, r"@[0-9a-f]{12}`")
        self.assertIn("not-measured", content)
        self.assertIn("不授权复制外部源码", content)

    def test_spec_to_code_is_bidirectional_and_unchecked_is_not_success(self) -> None:
        design = source("skills/adk-interface-contract-design/SKILL.md")
        review = source("skills/adk-code-review-loop/SKILL.md")
        details = source("skills/adk-interface-contract-design/references/spec-code-bidirectional.md")
        review_detail = source("skills/adk-code-review-loop/references/review-governance-details.md")
        template = source("skills/adk-code-review-loop/references/review-evidence-template.md")
        self.assertIn("Spec-to-Code 双向核对", design)
        self.assertIn("references/spec-code-bidirectional.md", design)
        for token in ("spec → code", "code → spec", "verified / contradicted / absent / not-checked",
                      "documented / undocumented / not-checked", "risk_owner_decision",
                      "缺陷发现率", "not-tested"):
            self.assertIn(token, details)
        self.assertIn("Spec-to-Code", review_detail)
        self.assertIn("Spec-to-Code Ledger", template)
        self.assertIn("spec-compliance pass", review)
        self.assertNotIn("#define IFACE_TIMEOUT_MS     1000", design)
        self.assertNotIn("#define IFACE_MAX_RETRIES    3", design)
        for token in ("partial", "stronger-than-spec", "undecidable", "searched_scope"):
            self.assertIn(token, details)
            self.assertIn(token, review_detail)

    def test_security_scanner_separates_coverage_from_verified_vulnerabilities(self) -> None:
        skill = source("optional-skills/adk-security-supply-chain/SKILL.md")
        ref = source("optional-skills/adk-security-supply-chain/references/skill-scan-coverage.md")
        for token in ("source-only intake", "adoption preflight", "install / runtime readiness",
                      "SECURITY_MODEL.md", "confirmed / false-positive / unverified",
                      "inspected / omitted / unavailable", "source-to-sink"):
            self.assertIn(token, skill)
        for token in ("candidate_source@commit/tag", "reachable_sink", "affected_principal",
                      "inspected/omitted/unavailable", "false-positive", "unverified",
                      "deny_path", "SECURITY_MODEL.md@digest"):
            self.assertIn(token, ref)
        self.assertIn("不自动安装/执行不可信目标", ref)
        self.assertIn("3. 许可证审查：", skill)
        self.assertNotIn("\n2. 许可证审查：", skill)

    def test_preregistered_train_holdout_is_disjoint_and_has_no_claimed_runs(self) -> None:
        fixture = json.loads(source("tests/fixtures/skill_method_ab_prereg.json"))
        examples = json.loads(source("tests/fixtures/skill_method_cases.json"))
        self.assertEqual(fixture["schema"], "adk-skill-method-ab-prereg/v1")
        self.assertEqual(fixture["status"], "not-measured")
        self.assertEqual(fixture["execution"], "no-model-runs")
        self.assertEqual(fixture["baseline"]["source_sha"],
                         "538e224ad91319a17a88f0e8c4d743dd89d7b02d")
        self.assertIsNone(fixture["candidate"]["source_sha"])
        self.assertEqual(fixture["results"], [])
        train = fixture["case_groups"]["train_case_ids"]
        holdout = fixture["case_groups"]["holdout_case_ids"]
        self.assertGreaterEqual(len(train), 5)
        self.assertGreaterEqual(len(holdout), 4)
        self.assertFalse(set(train) & set(holdout))
        self.assertEqual(set(train) | set(holdout), {x["id"] for x in examples["cases"]})
        self.assertEqual(fixture["trial_contract"]["min_repetitions"], 3)
        self.assertTrue(fixture["trial_contract"]["holdout_no_prompt_tuning"])
        self.assertIn("unauthorized_tool_use", fixture["trial_contract"]["hard_fail"])
        self.assertEqual(fixture["trial_contract"]["effect_comparator"],
                         "agent_dev_kit.effect_trials.compare_effect_trial_file")
        guide = source("optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md")
        self.assertIn("train_case_ids", guide)
        self.assertIn("holdout_case_ids", guide)
        self.assertIn("invalid-eval", guide)
        self.assertIn("not-measured", guide)

    def test_cost_priority_requires_real_task_quality_evidence(self) -> None:
        skill = source("skills/adk-token-context-governance/SKILL.md")
        for token in ("Impact-first Selection", "task_success / safety / latency",
                      "cached_tokens", "tool_calls", "串行外部检索瀑布",
                      "not-measured", "audit/L3"):
            self.assertIn(token, skill)
        guide = source("docs/evals/skill-method-parity.md")
        self.assertIn("skill_method_ab_prereg.json", guide)
        self.assertIn("compare_effect_trial_file", guide)
        self.assertIn("not-measured", guide)


    def test_reader_first_acceptance_and_feedback_are_source_only(self) -> None:
        adr = source("skills/adk-adr-writer/SKILL.md")
        handoff = source("skills/adk-cross-team-handoff/SKILL.md")
        composition = source("optional-skills/adk-skill-composition-governance/SKILL.md")
        lifecycle = source(
            "optional-skills/adk-skill-composition-governance/references/adk-skill-lifecycle.md"
        )
        notes = source("docs/evals/external-skill-method-comparison-20261114-round2.md")

        for marker in ("Reader-only acceptance", "reader_view", "self-review", "independent-verified",
                       "not-run", "unknown/pending"):
            self.assertIn(marker, adr)
        for marker in ("Receiver cold-read", "pending", "not-run", "accepted", "不强制"):
            self.assertIn(marker, handoff)
        self.assertIn("失败反馈→回归候选", composition)
        for marker in ("Failure Feedback → Deterministic Regression", "failure_trace_ref",
                       "source_sha", "design-case", "not-measured", "holdout",
                       "Lifecycle Review (report-only)", "required_and_forbidden_footprint",
                       "owner_decision"):
            self.assertIn(marker, lifecycle)

        source_rows = [line for line in notes.splitlines()
                       if line.startswith("| [") and "](https://github.com/" in line]
        self.assertEqual(len(source_rows), 6)
        self.assertEqual(len(set(source_rows)), len(source_rows))
        for row in source_rows:
            self.assertRegex(row, r"@[0-9a-f]{12}`")
        for marker in ("ADR-R1", "ADR-R2", "HANDOFF-R1", "HANDOFF-R2",
                       "LIFE-R1", "LIFE-R2", "not-measured", "不增加新 Skill"):
            self.assertIn(marker, notes)
        self.assertNotIn("真实模型效果已提升", notes)


    def test_skill_fit_and_measured_value_are_not_trigger_success(self) -> None:
        router = source("skills/adk-runtime-router/SKILL.md")
        details = source("skills/adk-runtime-router/references/runtime-routing-details.md")
        eval_guide = source(
            "optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md"
        )
        audit = source("docs/evals/external-skill-method-comparison-20261114-round4.md")
        for marker in ("Skill Fit Gate", "no-skill/abstain", "目标仓当前源码", "过期 Skill 模板"):
            self.assertIn(marker, router)
        for marker in ("target_repo@commit", "target_api_or_toolchain_version",
                       "skill_supported_scope", "conflicting_guidance", "version-unverified",
                       "second classifier"):
            self.assertIn(marker, details)
        for marker in ("no-skill vs selected-skill", "wrong-version",
                       "explicit-instruction-conflict", "irrelevant-trigger",
                       "beneficial / neutral / harmful / inconclusive", "not-measured",
                       "effect_trials"):
            self.assertIn(marker, eval_guide)
        for marker in ("SWE-Skills-Bench", "AgentSkillOS", "Waza v0.41.0",
                       "FIT-01", "FIT-02", "FIT-03", "VALUE-01", "VALUE-02",
                       "VALUE-03", "E0/E1", "E2–E4"):
            self.assertIn(marker, audit)
        self.assertNotIn("ADK 已实测改善", audit)



if __name__ == "__main__":
    unittest.main()
