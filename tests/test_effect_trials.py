from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.effect_trials import compare_effect_trials, compare_effect_trial_file
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from agent_dev_kit.run_evidence import RunEvidenceObservation, emit_run_evidence
from agent_dev_kit.trace_summary import (
    CostFact, GuardrailFact, MetricUnavailable, OutcomeFact,
    TokenUsageFact, TraceRunFacts, VerificationFact,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests/agent_value_contracts.json")


def ref(value):
    return "ref:" + sha256_bytes(canonical_json_bytes(value))


def fresh_run(side, task, trial, **overrides):
    ident = f"{side}-task-{task}-trial-{trial}"
    facts = TraceRunFacts(
        run_id=ident, task_id=f"task-{task}",
        asset_bundle_sha256=("a" if side == "baseline" else "b") * 64,
        runtime_target="test-harness", runtime_version="runtime-v1", model_version="model-revision-1",
        goal_ref="ref:" + hashlib.sha256(ident.encode()).hexdigest(),
        primary_skill="adk-requirements-triage", prompt_version="fixed-prompt-v1",
        orchestration_mode="single-agent", tools_used=(), handoffs=(),
        guardrails=(GuardrailFact("privacy", "passed"),),
        verification=(VerificationFact("unit-tests", "passed", "ref:" + "9" * 64),),
        elapsed_ms=100 if side == "baseline" else 70, first_pass_success=True,
        human_interventions=0, wrong_skill=False, abstained=False,
        privacy_status="no-sensitive-content", blockers=(), failure_pattern="none", next_goal_ref=None,
        token_usage=TokenUsageFact(20, 0, 5), cost=CostFact(1, "USD"),
        outcome=OutcomeFact("succeeded", "completed"),
    )
    facts = replace(facts, **overrides)
    return dict(emit_run_evidence(
        RunEvidenceObservation(facts, datetime(2026, 9, 24, 12, trial, tzinfo=timezone.utc)),
        MANIFEST, CONTRACT,
    ))


def rebind(document):
    for trial in document["trials"]:
        for side in ("baseline", "candidate"):
            for observation in trial[side]:
                observation["plan_ref"] = ref(document["plan"])
                observation["controls_ref"] = ref(document["plan"]["controls"])


def document(tasks=6, trials=3):
    controls = {
        "runtime_target": "test-harness", "runtime_version": "runtime-v1",
        "model_version": "model-revision-1", "prompt_version": "fixed-prompt-v1",
        "orchestration_mode": "single-agent", "model_identity": "revision-bound",
        **{name: "ref:" + "c" * 64 for name in (
            "environment_ref", "grader_ref", "dataset_ref", "provider_ref", "parameters_ref", "tool_policy_ref"
        )},
    }
    plan = {
        "campaign_id": "repeated-effect-fixture",
        "registered_at": "2026-09-24T10:00:00Z",
        "window": {"from": "2026-09-24T11:00:00Z", "through": "2026-09-24T14:00:00Z",
                   "as_of": "2026-09-24T18:00:00Z"},
        "task_ids": [f"task-{i}" for i in range(tasks)],
        "trial_ids": [f"trial-{i}" for i in range(trials)],
        "bundles": {"baseline": "a" * 64, "candidate": "b" * 64},
        "controls": controls,
        "policy": {"primary_metric": "latency-per-task-ms", "minimum_effect": 5,
                   "noninferiority_margin": 0, "guardrails": {"task-success-rate": 0, "wrong-skill-rate": 0},
                   "minimum_tasks": 5, "minimum_trials": 3,
                   "bootstrap_samples": 200, "bootstrap_seed": 42, "confidence": 0.95},
    }
    value = {"schema_version": "adk-effect-trials/v1", "plan": plan, "trials": [
        {"trial_id": f"trial-{trial}", "infrastructure_status": "ok",
         **{side: [{"run": fresh_run(side, task, trial)} for task in range(tasks)]
            for side in ("baseline", "candidate")}} for trial in range(trials)
    ]}
    rebind(value)
    return value


class EffectTrialsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = document()

    def setUp(self):
        self.data = copy.deepcopy(self.fixture)

    def compare(self):
        return compare_effect_trials(self.data, MANIFEST)

    def test_repeats_are_not_independent_tasks(self):
        value = self.compare()
        metric = value["metrics"]["latency-per-task-ms"]
        self.assertEqual(value["run_count"], 36)
        self.assertEqual(value["task_count"], 6)
        self.assertEqual(metric["task_count"], 6)
        self.assertEqual(metric["sampling_unit"], "task")
        self.assertEqual(metric["benefit_interval"], [30, 30])
        self.assertEqual(value["verdict"], "improved")
        self.assertFalse(value["release_authorized"])
        self.assertFalse(value["quality_evidence_eligible"])
        self.assertEqual(value["evidence_scope"], "test-only")

    def test_deterministic_report(self):
        self.assertEqual(self.compare(), self.compare())

    def test_order_does_not_change_statistical_result(self):
        first = self.compare()
        self.data["trials"].reverse()
        for trial in self.data["trials"]:
            trial["baseline"].reverse()
            trial["candidate"].reverse()
        second = self.compare()
        self.assertEqual(first["metrics"], second["metrics"])
        self.assertEqual(first["trial_comparisons"], second["trial_comparisons"])

    def test_missing_trial_rejected(self):
        self.data["trials"].pop()
        with self.assertRaisesRegex(ManifestError, "missing planned"):
            self.compare()

    def test_duplicate_trial_rejected(self):
        self.data["trials"].append(copy.deepcopy(self.data["trials"][0]))
        with self.assertRaisesRegex(ManifestError, "duplicate"):
            self.compare()

    def test_missing_task_rejected(self):
        self.data["trials"][0]["candidate"].pop()
        with self.assertRaisesRegex(ManifestError, "complete task population"):
            self.compare()

    def test_reused_run_across_trials_rejected(self):
        self.data["trials"][1]["baseline"][0]["run"] = self.data["trials"][0]["baseline"][0]["run"]
        with self.assertRaisesRegex(ManifestError, "reused"):
            self.compare()

    def test_declared_controls_drift_rejected(self):
        self.data["trials"][0]["baseline"][0]["controls_ref"] = "ref:" + "d" * 64
        with self.assertRaisesRegex(ManifestError, "controls"):
            self.compare()

    def test_posthoc_plan_edit_without_rebinding_rejected(self):
        self.data["plan"]["policy"]["minimum_effect"] = 0
        with self.assertRaisesRegex(ManifestError, "frozen plan"):
            self.compare()

    def test_runtime_observation_controls_checked(self):
        self.data["trials"][0]["candidate"][0]["run"] = fresh_run("candidate", 0, 0, prompt_version="different-prompt")
        with self.assertRaisesRegex(ManifestError, "control variables"):
            self.compare()

    def test_bundle_change_between_trials_rejected(self):
        for item in self.data["trials"][1]["candidate"]:
            task = int(item["run"]["trace_summary"]["task_id"].split("-")[-1])
            item["run"] = fresh_run("candidate", task, 1, asset_bundle_sha256="d" * 64)
        with self.assertRaisesRegex(ManifestError, "intervention"):
            self.compare()

    def test_alias_remains_inconclusive(self):
        self.data["plan"]["controls"]["model_identity"] = "alias-unverified"
        rebind(self.data)
        self.assertEqual(self.compare()["verdict"], "inconclusive")

    def test_sample_size_cannot_be_inflated_by_repeats(self):
        self.data["plan"]["policy"]["minimum_tasks"] = 30
        rebind(self.data)
        value = self.compare()
        self.assertEqual(value["verdict"], "inconclusive")
        self.assertEqual(value["task_count"], 6)

    def test_infrastructure_failure_not_dropped(self):
        self.data["trials"][1]["infrastructure_status"] = "failed"
        value = self.compare()
        self.assertEqual(value["verdict"], "invalid")
        self.assertEqual(value["run_count"], 36)

    def test_missing_cost_is_not_zero(self):
        self.data["trials"][0]["candidate"][0]["run"] = fresh_run(
            "candidate", 0, 0, cost=MetricUnavailable("cost-not-observed"))
        self.data["plan"]["policy"]["primary_metric"] = "cost-per-task"
        rebind(self.data)
        value = self.compare()
        self.assertEqual(value["metrics"]["cost-per-task"]["status"], "not-comparable")
        self.assertEqual(value["verdict"], "inconclusive")

    def test_currency_changes_between_trials_rejected(self):
        for side in ("baseline", "candidate"):
            for task, item in enumerate(self.data["trials"][1][side]):
                item["run"] = fresh_run(side, task, 1, cost=CostFact(1, "EUR"))
        with self.assertRaisesRegex(ManifestError, "currencies"):
            self.compare()

    def test_outcome_unavailable_blocks_verdict(self):
        self.data["trials"][0]["candidate"][0]["run"] = fresh_run(
            "candidate", 0, 0, outcome=MetricUnavailable("outcome-not-observed"), first_pass_success=False)
        value = self.compare()
        self.assertEqual(value["verdict"], "inconclusive")
        self.assertEqual(value["reliability"]["candidate"]["status"], "not-measured")

    def test_failure_not_hidden_by_faster_latency(self):
        for trial, item in enumerate(self.data["trials"]):
            for task in range(6):
                item["candidate"][task]["run"] = fresh_run(
                    "candidate", task, trial, first_pass_success=False,
                    outcome=OutcomeFact("failed", "runtime-failure"), failure_pattern="runtime-failure",
                    blockers=("runtime-failure",))
        value = self.compare()
        self.assertEqual(value["verdict"], "regressed")
        self.assertEqual(value["outcome_counts"]["candidate"]["failed"], 18)

    def test_any_success_and_all_success_are_different(self):
        for task in range(6):
            self.data["trials"][0]["candidate"][task]["run"] = fresh_run(
                "candidate", task, 0, first_pass_success=False,
                outcome=OutcomeFact("failed", "runtime-failure"), failure_pattern="runtime-failure",
                blockers=("runtime-failure",))
        values = self.compare()["reliability"]["candidate"]
        self.assertEqual(values["any_trial_succeeded_rate"], 1)
        self.assertEqual(values["all_trials_succeeded_rate"], 0)

    def test_noninferior_when_equal(self):
        for trial, entry in enumerate(self.data["trials"]):
            for task in range(6):
                entry["candidate"][task]["run"] = fresh_run("candidate", task, trial, elapsed_ms=100)
        self.assertEqual(self.compare()["verdict"], "non-inferior")

    def test_guardrails_required(self):
        self.data["plan"]["policy"]["guardrails"] = {"latency-per-task-ms": 1, "cost-per-task": 1}
        rebind(self.data)
        with self.assertRaisesRegex(ManifestError, "guard success"):
            self.compare()

    def test_nan_bool_and_bad_limits_rejected(self):
        for field, bad in (("minimum_effect", float("nan")), ("minimum_tasks", True),
                           ("bootstrap_samples", 0), ("confidence", 1)):
            with self.subTest(field=field):
                self.data = copy.deepcopy(self.fixture)
                self.data["plan"]["policy"][field] = bad
                with self.assertRaises((ManifestError, ValueError)):
                    self.compare()

    def test_uncertainty_crosses_zero_is_inconclusive(self):
        for trial, entry in enumerate(self.data["trials"]):
            for task in range(6):
                entry["candidate"][task]["run"] = fresh_run(
                    "candidate", task, trial, elapsed_ms=50 if task < 3 else 150)
        self.assertEqual(self.compare()["verdict"], "inconclusive")

    def test_time_travel_and_posthoc_registration_rejected(self):
        self.data["plan"]["registered_at"] = "2026-09-24T15:00:00Z"
        rebind(self.data)
        with self.assertRaisesRegex(ManifestError, "precede"):
            self.compare()

    def test_plan_extra_field_rejected(self):
        self.data["plan"]["approve_release"] = True
        with self.assertRaises(ManifestError):
            self.compare()

    def test_raw_evidence_tamper_rejected(self):
        self.data["trials"][0]["candidate"][0]["run"]["trace_summary"]["elapsed_ms"] = 1
        with self.assertRaises(ManifestError):
            self.compare()

    def test_candidate_guard_failure_vetoes_improvement(self):
        self.data["trials"][0]["candidate"][0]["run"] = fresh_run(
            "candidate", 0, 0, guardrails=(GuardrailFact("privacy", "failed"),),
            outcome=OutcomeFact("failed", "validation-failure"), first_pass_success=False,
            blockers=("validation-failure",), failure_pattern="validation-failure")
        self.assertEqual(self.compare()["verdict"], "regressed")

    def test_baseline_guard_failure_does_not_veto_candidate_fix(self):
        self.data["trials"][0]["baseline"][0]["run"] = fresh_run(
            "baseline", 0, 0, guardrails=(GuardrailFact("privacy", "failed"),),
            outcome=OutcomeFact("failed", "validation-failure"), first_pass_success=False,
            blockers=("validation-failure",), failure_pattern="validation-failure")
        self.assertEqual(self.compare()["verdict"], "improved")

    def test_unknown_metric_is_not_silently_ignored(self):
        self.data["plan"]["policy"]["primary_metric"] = "made-up-quality"
        rebind(self.data)
        with self.assertRaisesRegex(ManifestError, "supported directional"):
            self.compare()

    def test_excessive_resampling_rejected_before_run_validation(self):
        self.data["plan"]["task_ids"] = [f"task-{n}" for n in range(300)]
        self.data["plan"]["policy"]["bootstrap_samples"] = 10000
        with self.assertRaisesRegex(ManifestError, "budget"):
            self.compare()

    def test_input_byte_budget_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"input.json"
            path.write_text(json.dumps(self.data))
            self.assertEqual(compare_effect_trial_file(path, MANIFEST)["verdict"], "improved")
            path.write_text("{")
            with self.assertRaisesRegex(ManifestError, "JSON"):
                compare_effect_trial_file(path, MANIFEST)

    def test_cli_invalid_is_json_nonzero(self):
        from agent_dev_kit.evaluation_cli import main
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.json"
            path.write_text("{}")
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                code = main(["compare-trials", "--input", str(path), "--summary-json"])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stream.getvalue())["verdict"], "invalid")


if __name__ == "__main__":
    unittest.main()