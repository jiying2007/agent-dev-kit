from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from agent_dev_kit.run_evidence import (
    RunEvidenceObservation,
    TestAssetObservation,
    emit_run_evidence,
    validate_run_evidence,
)
from agent_dev_kit.trace_summary import (
    CostFact,
    GuardrailFact,
    MetricUnavailable,
    OutcomeFact,
    TokenUsageFact,
    ToolUseFact,
    TraceRunFacts,
    VerificationFact,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests" / "agent_value_contracts.json")
UTC = timezone.utc
OBSERVED_AT = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
WINDOW_FROM = datetime(2026, 8, 29, 11, 0, tzinfo=UTC)
WINDOW_THROUGH = datetime(2026, 8, 29, 13, 0, tzinfo=UTC)
AS_OF = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)


def facts(**overrides: object) -> TraceRunFacts:
    values = {
        "run_id": "run-composition-001",
        "task_id": "task-composition-001",
        "asset_bundle_sha256": "a" * 64,
        "runtime_target": "test-harness",
        "runtime_version": "2026.08.29",
        "model_version": "test-model-v1",
        "goal_ref": "ref:" + "1" * 64,
        "primary_skill": "adk-requirements-triage",
        "prompt_version": "composition-fixture-v1",
        "orchestration_mode": "single-agent",
        "tools_used": (ToolUseFact("repository-read", 1, "succeeded"),),
        "handoffs": (),
        "guardrails": (GuardrailFact("privacy-boundary", "passed"),),
        "verification": (
            VerificationFact("unit-tests", "passed", "ref:" + "2" * 64),
        ),
        "elapsed_ms": 120,
        "first_pass_success": True,
        "human_interventions": 0,
        "wrong_skill": False,
        "abstained": False,
        "privacy_status": "no-sensitive-content",
        "blockers": (),
        "failure_pattern": "none",
        "next_goal_ref": None,
        "token_usage": TokenUsageFact(10, 2, 3),
        "cost": CostFact(0.001, "USD"),
        "outcome": OutcomeFact("succeeded", "completed"),
    }
    values.update(overrides)
    return TraceRunFacts(**values)


def observation(*assets: TestAssetObservation, trace_facts: TraceRunFacts | None = None) -> RunEvidenceObservation:
    return RunEvidenceObservation(
        trace_facts=trace_facts or facts(),
        observed_at=OBSERVED_AT,
        assets=tuple(assets),
        aggregation_from=WINDOW_FROM if assets else None,
        aggregation_through=WINDOW_THROUGH if assets else None,
        as_of=AS_OF if assets else None,
    )


class RunEvidenceCompositionTest(unittest.TestCase):
    def test_trace_only_and_multi_asset_composition_are_bound_and_test_only(self) -> None:
        trace_only = emit_run_evidence(observation(), MANIFEST, CONTRACT)
        self.assertEqual([], trace_only["receipts"])
        self.assertIsNone(trace_only["measurement"])

        value = emit_run_evidence(
            observation(
                TestAssetObservation("agent", "requirements-analyst"),
                TestAssetObservation("skill", "adk-requirements-triage"),
                TestAssetObservation("profile", "core"),
            ),
            MANIFEST,
            CONTRACT,
        )
        self.assertEqual(3, len(value["receipts"]))
        self.assertTrue(all(item["source_trace_ref"] == value["trace_ref"] for item in value["receipts"]))
        self.assertTrue(all(item["evidence_layer"] == "test" for item in value["receipts"]))
        measurement = value["measurement"]
        self.assertEqual("test-only", measurement["evidence_scope"])
        self.assertFalse(measurement["quality_evidence_eligible"])
        self.assertTrue(measurement["owner_review_required"])
        self.assertEqual("none-evidence-only", measurement["lifecycle_authority"])

    def test_unavailable_outcome_allows_trace_only_but_not_asset_receipts(self) -> None:
        unavailable = facts(
            outcome=MetricUnavailable("run-outcome-unavailable"),
            first_pass_success=False,
        )
        value = emit_run_evidence(observation(trace_facts=unavailable), MANIFEST, CONTRACT)
        self.assertEqual("not-available", value["trace_summary"]["outcome"]["status"])
        with self.assertRaisesRegex(ManifestError, "explicitly observed outcome"):
            emit_run_evidence(
                observation(TestAssetObservation("profile", "core"), trace_facts=unavailable),
                MANIFEST,
                CONTRACT,
            )

        abstained = facts(
            outcome=OutcomeFact("abstained", "no-match"),
            first_pass_success=False,
            abstained=True,
        )
        with self.assertRaisesRegex(ManifestError, "cannot infer whether an abstention was correct"):
            emit_run_evidence(
                observation(TestAssetObservation("profile", "core"), trace_facts=abstained),
                MANIFEST,
                CONTRACT,
            )

    def test_duplicate_unknown_window_and_privacy_inputs_fail_closed(self) -> None:
        duplicate = TestAssetObservation("profile", "core")
        with self.assertRaisesRegex(ManifestError, "duplicate asset"):
            emit_run_evidence(observation(duplicate, duplicate), MANIFEST, CONTRACT)

        with self.assertRaises(ManifestError):
            emit_run_evidence(
                observation(TestAssetObservation("skill", "missing-skill")),
                MANIFEST,
                CONTRACT,
            )

        outside = RunEvidenceObservation(
            trace_facts=facts(),
            observed_at=datetime(2026, 8, 29, 10, 0, tzinfo=UTC),
            assets=(TestAssetObservation("profile", "core"),),
            aggregation_from=WINDOW_FROM,
            aggregation_through=WINDOW_THROUGH,
            as_of=AS_OF,
        )
        with self.assertRaisesRegex(ManifestError, "outside the fixed aggregation window"):
            emit_run_evidence(outside, MANIFEST, CONTRACT)

        with self.assertRaisesRegex(ManifestError, "secret-like content"):
            emit_run_evidence(
                observation(trace_facts=facts(runtime_version="sk-abcdefghijklmnop")),
                MANIFEST,
                CONTRACT,
            )

    def test_wrapper_tamper_is_detected_by_recomputation(self) -> None:
        value = emit_run_evidence(
            observation(TestAssetObservation("profile", "core")),
            MANIFEST,
            CONTRACT,
        )
        trace_tamper = copy.deepcopy(value)
        trace_tamper["trace_ref"] = "ref:" + "f" * 64
        with self.assertRaisesRegex(ManifestError, "does not bind"):
            validate_run_evidence(trace_tamper, MANIFEST, CONTRACT)

        receipt_tamper = copy.deepcopy(value)
        receipt_tamper["receipts"][0]["human_interventions"] = 3
        with self.assertRaises(ManifestError):
            validate_run_evidence(receipt_tamper, MANIFEST, CONTRACT)

        projected_tamper = copy.deepcopy(value)
        projected_tamper["receipts"][0]["routing"]["wrong_route"] = True
        body = dict(projected_tamper["receipts"][0])
        body.pop("receipt_id")
        projected_tamper["receipts"][0]["receipt_id"] = "ref:" + sha256_bytes(
            canonical_json_bytes(body)
        )
        with self.assertRaisesRegex(ManifestError, "semantics differ"):
            validate_run_evidence(projected_tamper, MANIFEST, CONTRACT)

        measurement_tamper = copy.deepcopy(value)
        measurement_tamper["measurement"]["source_receipt_count"] = 2
        with self.assertRaisesRegex(ManifestError, "differs from receipt recomputation"):
            validate_run_evidence(measurement_tamper, MANIFEST, CONTRACT)


if __name__ == "__main__":
    unittest.main()
