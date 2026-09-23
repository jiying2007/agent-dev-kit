from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_dev_kit.effect_comparator import EffectCampaignInput, compare_effects
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.run_evidence import RunEvidenceObservation, emit_run_evidence
from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.trace_summary import (
    CostFact,
    GuardrailFact,
    MetricUnavailable,
    OutcomeFact,
    TokenUsageFact,
    TraceRunFacts,
    VerificationFact,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests" / "agent_value_contracts.json")
UTC = timezone.utc
WINDOW_FROM = datetime(2026, 8, 29, 11, 0, tzinfo=UTC)
WINDOW_THROUGH = datetime(2026, 8, 29, 14, 0, tzinfo=UTC)
AS_OF = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)


def run(
    condition: str,
    task_id: str,
    marker: int,
    *,
    succeeded: bool,
    elapsed_ms: int,
    cost_available: bool = True,
    runtime_version: str = "runtime-v1",
    outcome_available: bool = True,
) -> dict:
    if outcome_available:
        outcome = OutcomeFact("succeeded", "completed") if succeeded else OutcomeFact("failed", "runtime-failure")
    else:
        outcome = MetricUnavailable("outcome-not-observed")
    facts = TraceRunFacts(
        run_id="run-{}-{}".format(condition, marker),
        task_id=task_id,
        asset_bundle_sha256=("a" if condition == "baseline" else "b") * 64,
        runtime_target="test-harness",
        runtime_version=runtime_version,
        model_version="test-model-v1",
        goal_ref="ref:" + str(marker) * 64,
        primary_skill="adk-requirements-triage",
        prompt_version="{}-prompt-v1".format(condition),
        orchestration_mode="single-agent",
        tools_used=(),
        handoffs=(),
        guardrails=(GuardrailFact("privacy-boundary", "passed"),),
        verification=(VerificationFact("unit-tests", "passed", "ref:" + "9" * 64),),
        elapsed_ms=elapsed_ms,
        first_pass_success=succeeded if outcome_available else False,
        human_interventions=0 if succeeded else 1,
        wrong_skill=False,
        abstained=False,
        privacy_status="no-sensitive-content",
        blockers=() if succeeded or not outcome_available else ("runtime-failure",),
        failure_pattern="none" if succeeded or not outcome_available else "runtime-failure",
        next_goal_ref=None,
        token_usage=TokenUsageFact(10 + marker, 0, 2),
        cost=CostFact(1.0, "USD") if cost_available else MetricUnavailable("cost-not-observed"),
        outcome=outcome,
    )
    observed_at = datetime(2026, 8, 29, 12, marker, tzinfo=UTC)
    return dict(emit_run_evidence(
        RunEvidenceObservation(trace_facts=facts, observed_at=observed_at),
        MANIFEST,
        CONTRACT,
    ))


def campaign(baseline: tuple, candidate: tuple, tasks=("task-1", "task-2")) -> EffectCampaignInput:
    return EffectCampaignInput(
        campaign_id="effect-campaign-v1",
        expected_task_ids=tuple(tasks),
        baseline=baseline,
        candidate=candidate,
        window_from=WINDOW_FROM,
        window_through=WINDOW_THROUGH,
        as_of=AS_OF,
    )


class EffectComparatorTest(unittest.TestCase):
    def test_complete_campaign_measures_effect_and_preserves_missing_cost(self) -> None:
        baseline = (
            run("baseline", "task-1", 1, succeeded=True, elapsed_ms=100),
            run("baseline", "task-2", 2, succeeded=False, elapsed_ms=200),
        )
        candidate = (
            run("candidate", "task-1", 3, succeeded=True, elapsed_ms=80),
            run("candidate", "task-2", 4, succeeded=True, elapsed_ms=100, cost_available=False),
        )
        value = compare_effects(campaign(baseline, candidate), MANIFEST, CONTRACT)
        self.assertEqual(2, value["task_population"]["count"])
        self.assertEqual(2, len(value["baseline"]["run_evidence_refs"]))
        self.assertTrue(all(item.startswith("ref:") for item in value["candidate"]["run_evidence_refs"]))
        self.assertEqual(0.5, value["baseline"]["metrics"]["task-success-rate"]["value"])
        self.assertEqual(1.0, value["candidate"]["metrics"]["task-success-rate"]["value"])
        self.assertEqual(0.5, value["deltas"]["task-success-rate"]["candidate_minus_baseline"])
        self.assertEqual(-60.0, value["deltas"]["latency-per-task-ms"]["candidate_minus_baseline"])
        self.assertEqual("not-measured", value["candidate"]["metrics"]["cost-per-task"]["status"])
        self.assertEqual("not-comparable", value["deltas"]["cost-per-task"]["status"])
        self.assertEqual("test-only", value["evidence_scope"])
        self.assertFalse(value["quality_evidence_eligible"])

    def test_missing_duplicate_and_runtime_mismatch_fail_closed(self) -> None:
        baseline = (
            run("baseline", "task-1", 1, succeeded=True, elapsed_ms=100),
            run("baseline", "task-2", 2, succeeded=True, elapsed_ms=100),
        )
        candidate = (run("candidate", "task-1", 3, succeeded=True, elapsed_ms=100),)
        with self.assertRaisesRegex(ManifestError, "complete task population"):
            compare_effects(campaign(baseline, candidate), MANIFEST, CONTRACT)

        duplicate = (baseline[0], copy.deepcopy(baseline[0]))
        with self.assertRaisesRegex(ManifestError, "duplicate task or run"):
            compare_effects(campaign(duplicate, baseline), MANIFEST, CONTRACT)

        mismatch = (
            run("candidate", "task-1", 3, succeeded=True, elapsed_ms=100, runtime_version="runtime-v2"),
            run("candidate", "task-2", 4, succeeded=True, elapsed_ms=100),
        )
        with self.assertRaisesRegex(ManifestError, "runtime/model identity"):
            compare_effects(campaign(baseline, mismatch), MANIFEST, CONTRACT)

        reused = tuple(copy.deepcopy(item) for item in baseline)
        with self.assertRaisesRegex(ManifestError, "independent run identities"):
            compare_effects(campaign(baseline, reused), MANIFEST, CONTRACT)

    def test_unavailable_outcome_prevents_success_delta_and_secret_is_rejected(self) -> None:
        baseline = (
            run("baseline", "task-1", 1, succeeded=True, elapsed_ms=100),
            run("baseline", "task-2", 2, succeeded=True, elapsed_ms=100),
        )
        candidate = (
            run("candidate", "task-1", 3, succeeded=True, elapsed_ms=100),
            run("candidate", "task-2", 4, succeeded=False, elapsed_ms=100, outcome_available=False),
        )
        value = compare_effects(campaign(baseline, candidate), MANIFEST, CONTRACT)
        self.assertEqual("not-measured", value["candidate"]["metrics"]["task-success-rate"]["status"])
        self.assertEqual("not-comparable", value["deltas"]["task-success-rate"]["status"])

        secret_campaign = campaign(baseline, baseline)
        object.__setattr__(secret_campaign, "campaign_id", "sk-abcdefghijklmnop")
        with self.assertRaisesRegex(ManifestError, "secret-like content"):
            compare_effects(secret_campaign, MANIFEST, CONTRACT)


if __name__ == "__main__":
    unittest.main()
