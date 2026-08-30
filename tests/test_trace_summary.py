from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_dev_kit.model import ManifestError
from agent_dev_kit.trace_summary import (
    CostFact,
    GuardrailFact,
    HandoffFact,
    MetricUnavailable,
    OutcomeFact,
    TokenUsageFact,
    ToolUseFact,
    TraceRunFacts,
    VerificationFact,
    emit_trace_summary_v2,
    load_trace_summary_schema,
    validate_trace_summary,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "adk-workflow-trace-summary-v2.schema.json"
CONTRACT_PATH = ROOT / "manifests" / "trace_eval_contracts.json"


def summary() -> dict:
    return {
        "schema_version": "adk-workflow-trace-summary/v2",
        "run_id": "run-20260830-001",
        "task_id": "task-trace-contract",
        "asset_bundle_sha256": "a" * 64,
        "runtime_target": "local-agent-runtime",
        "runtime_version": "2026.08.30",
        "model_version": "gpt-5",
        "goal": "not-applicable",
        "goal_ref": "ref:" + "1" * 64,
        "primary_skill": "adk-verification-before-completion",
        "prompt_version": "trace-contract-test-v1",
        "orchestration_mode": "subagents",
        "tool_calls": 2,
        "tools_used": [
            {"name": "exec-command", "call_count": 2, "outcome": "succeeded"}
        ],
        "handoffs": [{"target": "review-agent", "outcome": "succeeded"}],
        "guardrails": [{"name": "privacy-boundary", "status": "passed"}],
        "verification": [
            {"name": "unit-tests", "status": "passed", "evidence_ref": "ref:" + "2" * 64}
        ],
        "token_usage": {"input": 100, "cached_input": 40, "output": 20},
        "cost": {"status": "available", "amount": 0.125, "currency": "USD"},
        "elapsed_ms": 1250,
        "outcome": {"status": "succeeded", "category": "completed"},
        "first_pass_success": True,
        "human_interventions": 0,
        "wrong_skill": False,
        "abstained": False,
        "privacy_status": "sanitized",
        "raw_content_stored": False,
        "blockers": [],
        "failure_pattern": "none",
        "next_goal": None,
        "next_goal_ref": None,
    }


def run_facts(**overrides: object) -> TraceRunFacts:
    values = {
        "run_id": "run-20260830-001",
        "task_id": "task-trace-contract",
        "asset_bundle_sha256": "a" * 64,
        "runtime_target": "local-agent-runtime",
        "runtime_version": "2026.08.30",
        "model_version": "gpt-5",
        "goal_ref": "ref:" + "1" * 64,
        "primary_skill": "adk-verification-before-completion",
        "prompt_version": "trace-contract-test-v1",
        "orchestration_mode": "subagents",
        "tools_used": (ToolUseFact("exec-command", 2, "succeeded"),),
        "handoffs": (HandoffFact("review-agent", "succeeded"),),
        "guardrails": (GuardrailFact("privacy-boundary", "passed"),),
        "verification": (
            VerificationFact("unit-tests", "passed", "ref:" + "2" * 64),
        ),
        "elapsed_ms": 1250,
        "first_pass_success": True,
        "human_interventions": 0,
        "wrong_skill": False,
        "abstained": False,
        "privacy_status": "sanitized",
        "blockers": (),
        "failure_pattern": "none",
        "next_goal_ref": None,
        "token_usage": TokenUsageFact(100, 40, 20),
        "cost": CostFact(0.125, "USD"),
        "outcome": OutcomeFact("succeeded", "completed"),
    }
    values.update(overrides)
    return TraceRunFacts(**values)


class TraceSummaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_trace_summary_schema(SCHEMA_PATH)

    def test_schema_and_manifest_contract_are_versioned_and_emitter_is_explicit_per_run(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        strict = next(item for item in contract["contracts"] if item["id"] == "adk-workflow-trace-summary-v2")
        canonical = contract["canonical_trace_summary_contract"]
        self.assertEqual("adk-workflow-trace-summary-v2", canonical["id"])
        self.assertEqual("schemas/adk-workflow-trace-summary-v2.schema.json", strict["schema_ref"])
        self.assertEqual(strict["schema_ref"], canonical["schema_ref"])
        self.assertEqual("available", strict["emitter_status"])
        self.assertEqual(strict["emitter_status"], canonical["emitter_status"])
        self.assertTrue(strict["per_run_emission_claimed"])
        self.assertEqual("explicit-per-run-library-call", strict["emitter"]["mode"])
        self.assertFalse(strict["emitter"]["automatic_runtime_integration"])
        self.assertEqual(
            "agent_dev_kit.trace_summary.emit_trace_summary_v2",
            canonical["emitter_api"],
        )
        self.assertEqual("ref:<sha256>", strict["privacy_policy"]["evidence_ref_format"])
        self.assertEqual(set(self.schema["required"]), set(strict["required_fields"]))
        legacy = next(item for item in contract["contracts"] if item["id"] == "adk-workflow-trace-summary-v1")
        self.assertNotIn("asset_bundle_sha256", legacy["required_fields"])
        self.assertNotIn("estimated_cost", legacy["required_fields"])

    def test_typed_emitter_preserves_observed_available_facts(self) -> None:
        emitted = emit_trace_summary_v2(run_facts())
        self.assertEqual(summary(), emitted)
        self.assertEqual(2, emitted["tool_calls"])

        second = emit_trace_summary_v2(run_facts(run_id="run-20260830-002"))
        self.assertEqual("run-20260830-002", second["run_id"])
        self.assertEqual("run-20260830-001", emitted["run_id"])

    def test_typed_emitter_defaults_unobserved_metrics_to_not_available(self) -> None:
        emitted = emit_trace_summary_v2(
            run_facts(
                token_usage=None,
                cost=None,
                outcome=None,
                first_pass_success=False,
            )
        )
        self.assertEqual(
            {"status": "not-available", "reason": "runtime-token-usage-unavailable"},
            emitted["token_usage"],
        )
        self.assertEqual(
            {"status": "not-available", "reason": "runtime-pricing-unavailable"},
            emitted["cost"],
        )
        self.assertEqual(
            {"status": "not-available", "reason": "runtime-outcome-unavailable"},
            emitted["outcome"],
        )

        explicit = emit_trace_summary_v2(
            run_facts(
                token_usage=MetricUnavailable("provider-token-metrics-disabled"),
                cost=MetricUnavailable("provider-pricing-evidence-disabled"),
                outcome=MetricUnavailable("run-still-in-progress"),
                first_pass_success=False,
            )
        )
        self.assertEqual("provider-token-metrics-disabled", explicit["token_usage"]["reason"])
        self.assertEqual("provider-pricing-evidence-disabled", explicit["cost"]["reason"])
        self.assertEqual("run-still-in-progress", explicit["outcome"]["reason"])

    def test_typed_emitter_rejects_untyped_or_inconsistent_facts(self) -> None:
        with self.assertRaisesRegex(ManifestError, "facts must be TraceRunFacts"):
            emit_trace_summary_v2({"run_id": "run-1"})  # type: ignore[arg-type]

        with self.assertRaisesRegex(ManifestError, "unavailable outcome excludes"):
            emit_trace_summary_v2(run_facts(outcome=None))

        with self.assertRaises(ManifestError):
            emit_trace_summary_v2(
                run_facts(
                    token_usage={"input": 0},  # type: ignore[arg-type]
                )
            )

    def test_typed_emitter_applies_shared_privacy_validator(self) -> None:
        with self.assertRaisesRegex(ManifestError, "secret-like content"):
            emit_trace_summary_v2(run_facts(runtime_version="sk-abcdefghijklmnop"))

        with self.assertRaisesRegex(ManifestError, "secret-like content"):
            emit_trace_summary_v2(
                run_facts(
                    outcome=MetricUnavailable("raw-prompt-unavailable"),
                    first_pass_success=False,
                )
            )

    def test_valid_available_and_unavailable_cost_summaries(self) -> None:
        self.assertEqual(summary(), validate_trace_summary(summary(), self.schema))

        unavailable = summary()
        unavailable["cost"] = {
            "status": "not-available",
            "reason": "runtime-pricing-unavailable",
        }
        self.assertEqual(unavailable, validate_trace_summary(unavailable, self.schema))

    def test_zero_boundaries_are_valid(self) -> None:
        value = summary()
        value["tool_calls"] = 0
        value["tools_used"] = []
        value["token_usage"] = {"input": 0, "cached_input": 0, "output": 0}
        value["cost"] = {"status": "available", "amount": 0, "currency": "USD"}
        value["elapsed_ms"] = 0
        self.assertEqual(value, validate_trace_summary(value, self.schema))

    def test_token_latency_hash_and_numeric_boundaries_fail_closed(self) -> None:
        cases = []
        negative_input = summary()
        negative_input["token_usage"]["input"] = -1
        cases.append(negative_input)
        cached_exceeds_input = summary()
        cached_exceeds_input["token_usage"]["cached_input"] = 101
        cases.append(cached_exceeds_input)
        negative_elapsed = summary()
        negative_elapsed["elapsed_ms"] = -1
        cases.append(negative_elapsed)
        boolean_interventions = summary()
        boolean_interventions["human_interventions"] = True
        cases.append(boolean_interventions)
        bad_hash = summary()
        bad_hash["asset_bundle_sha256"] = "A" * 64
        cases.append(bad_hash)
        mismatched_tool_count = summary()
        mismatched_tool_count["tool_calls"] = 1
        cases.append(mismatched_tool_count)

        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ManifestError):
                    validate_trace_summary(value, self.schema)

    def test_cost_shape_types_and_unknown_fields_fail_closed(self) -> None:
        cases = []
        missing_currency = summary()
        missing_currency["cost"] = {"status": "available", "amount": 1.0}
        cases.append(missing_currency)
        invented_amount = summary()
        invented_amount["cost"] = {"status": "not-available", "amount": 0, "currency": "USD"}
        cases.append(invented_amount)
        lower_currency = summary()
        lower_currency["cost"]["currency"] = "usd"
        cases.append(lower_currency)
        unknown = summary()
        unknown["provider_trace"] = "not allowed"
        cases.append(unknown)

        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ManifestError):
                    validate_trace_summary(value, self.schema)

    def test_outcome_and_boolean_relationships_fail_closed(self) -> None:
        cases = []
        intervention = summary()
        intervention["human_interventions"] = 1
        cases.append(intervention)
        failed_first_pass = summary()
        failed_first_pass["outcome"] = {"status": "failed", "category": "runtime-failure"}
        cases.append(failed_first_pass)
        mismatched_abstain = summary()
        mismatched_abstain["abstained"] = True
        mismatched_abstain["first_pass_success"] = False
        cases.append(mismatched_abstain)
        wrong_and_abstained = summary()
        wrong_and_abstained["outcome"] = {"status": "abstained", "category": "no-match"}
        wrong_and_abstained["abstained"] = True
        wrong_and_abstained["wrong_skill"] = True
        wrong_and_abstained["first_pass_success"] = False
        cases.append(wrong_and_abstained)
        mismatched_category = summary()
        mismatched_category["outcome"] = {"status": "succeeded", "category": "runtime-failure"}
        cases.append(mismatched_category)
        failed_verification = summary()
        failed_verification["verification"][0]["status"] = "failed"
        cases.append(failed_verification)
        failed_guardrail = summary()
        failed_guardrail["guardrails"][0]["status"] = "failed"
        cases.append(failed_guardrail)
        succeeded_with_blocker = summary()
        succeeded_with_blocker["blockers"] = ["owner-approval-pending"]
        cases.append(succeeded_with_blocker)

        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ManifestError):
                    validate_trace_summary(value, self.schema)

        valid_abstain = summary()
        valid_abstain["outcome"] = {"status": "abstained", "category": "no-match"}
        valid_abstain["abstained"] = True
        valid_abstain["first_pass_success"] = False
        self.assertEqual(valid_abstain, validate_trace_summary(valid_abstain, self.schema))

    def test_raw_prompt_message_and_tool_payload_fields_are_rejected_recursively(self) -> None:
        for forbidden_key in ("raw_prompt", "messages", "tool_payload", "tool.arguments"):
            value = copy.deepcopy(summary())
            value["tools_used"][0][forbidden_key] = "sensitive content"
            with self.subTest(forbidden_key=forbidden_key):
                with self.assertRaisesRegex(ManifestError, "forbidden sensitive field"):
                    validate_trace_summary(value, self.schema)

        raw_flag = summary()
        raw_flag["raw_content_stored"] = True
        with self.assertRaises(ManifestError):
            validate_trace_summary(raw_flag, self.schema)

        invalid_privacy = summary()
        invalid_privacy["privacy_status"] = "unreviewed"
        with self.assertRaises(ManifestError):
            validate_trace_summary(invalid_privacy, self.schema)

    def test_sensitive_values_and_non_finite_cost_are_rejected(self) -> None:
        for secret in (
            "ghp_abcdefghijklmnopqrstuv",
            "github_pat_abcdefghijklmnopqrstuv",
            "sk-abcdefghijklmnop",
            "Bearer abcdefghijklmnop",
            "AKIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
            "raw prompt",
            "tool payload",
        ):
            value = summary()
            value["runtime_version"] = secret
            with self.subTest(secret=secret), self.assertRaises(ManifestError):
                validate_trace_summary(value, self.schema)

        free_evidence_ref = summary()
        free_evidence_ref["verification"][0]["evidence_ref"] = "tests/raw-log.txt"
        with self.assertRaises(ManifestError):
            validate_trace_summary(free_evidence_ref, self.schema)

        secret_in_list = summary()
        secret_in_list["blockers"] = ["ghp_abcdefghijklmnopqrstuv"]
        with self.assertRaises(ManifestError):
            validate_trace_summary(secret_in_list, self.schema)

        for amount in (float("nan"), float("inf"), float("-inf")):
            value = summary()
            value["cost"]["amount"] = amount
            with self.subTest(amount=amount):
                with self.assertRaises(ManifestError):
                    validate_trace_summary(value, self.schema)


if __name__ == "__main__":
    unittest.main()
