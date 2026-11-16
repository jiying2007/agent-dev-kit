"""Synthetic pre-comparison control tests; no execution or E2-E4 evidence."""

from __future__ import annotations

import copy
import cProfile
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from agent_dev_kit.task_trials import compare_task_trials, task_trial_controls_ref

from test_effect_trials import document
from test_task_evidence import MANIFEST, ROOT, synthetic_package, write_json


def ref(value):
    return "ref:" + sha256_bytes(canonical_json_bytes(value))


def synthetic_task_trials(root):
    """Generate a local synthetic registration plus 36 bounded observations."""
    root.mkdir(parents=True, exist_ok=True)
    existing = document()
    task_bindings = []
    trials = []
    conditions = {"baseline": {}, "candidate": {}}
    for trial_index, trial in enumerate(existing["trials"]):
        result = {"trial_id": trial["trial_id"], "infrastructure_status": trial["infrastructure_status"]}
        for side in ("baseline", "candidate"):
            observations = []
            for task_index, _ in enumerate(trial[side]):
                relative = f"{side}-{task_index}-{trial_index}"
                package = root / relative
                envelope, _, _ = synthetic_package(package, side=side, task=task_index, trial=trial_index)
                path = package / "observation.json"
                observations.append({"path": f"{relative}/observation.json", "sha256": sha256_bytes(path.read_bytes())})
                if side == "baseline" and trial_index == 0:
                    task_bindings.append({"task_id": envelope["run"]["task_id"],
                                          "input_snapshot_sha256": envelope["input_snapshot"]["sha256"],
                                          "workspace_snapshot_sha256": envelope["workspace_snapshot"]["sha256"],
                                          "source_sha": envelope["run"]["source_sha"]})
                conditions[side][envelope["run"]["task_id"]] = {
                    "target_skill": envelope["skill_exposure"]["target_skill"],
                    "expected": envelope["skill_exposure"]["expected"],
                    "content_sha256": envelope["skill_exposure"]["content"]["sha256"],
                }
            result[side] = observations
        trials.append(result)
    plan = existing["plan"]
    value = {"schema_version": "adk-task-trials/v1", "provenance": "synthetic-fixture", "plan": plan,
             "task_bindings": task_bindings, "conditions": conditions, "grader_id": "synthetic-independent-grader",
             "trials": trials}
    plan["controls"]["dataset_ref"] = task_trial_controls_ref(value)
    write_json(root / "task-trials.json", value)
    return value


class TaskTrialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "synthetic-campaign"
        self.data = synthetic_task_trials(self.root)
        self.path = self.root / "task-trials.json"

    def compare(self, **kwargs):
        write_json(self.path, self.data)
        return compare_task_trials(self.path, MANIFEST, **kwargs)

    def mutate_observation(self, change, *, side="candidate", task=0, trial=0):
        reference = self.data["trials"][trial][side][task]
        path = self.root / reference["path"]
        envelope = json.loads(path.read_text())
        events = json.loads((path.parent / envelope["events"]["path"]).read_text())
        acceptance = json.loads((path.parent / envelope["acceptance"]["path"]).read_text())
        change(envelope, events, acceptance, path.parent)
        for index, event in enumerate(events["events"], 1):
            event["seq"] = index
        envelope["events"] = write_json(path.parent / "events.json", events)
        envelope["acceptance"] = write_json(path.parent / "acceptance.json", acceptance)
        write_json(path, envelope)
        reference["sha256"] = sha256_bytes(path.read_bytes())

    def test_complete_imports_are_compared_with_existing_authority(self):
        value = self.compare()
        self.assertEqual(value["status"], "compared")
        self.assertEqual(value["verdict"], "improved")  # Synthetic arithmetic only.
        self.assertEqual(value["provenance"], "synthetic-fixture")
        self.assertEqual(value["population"], "all-assigned-observations")
        self.assertEqual(value["comparison"]["run_count"], 36)
        self.assertEqual(value["comparison"]["metrics"]["latency-per-task-ms"]["benefit_interval"], [30, 30])
        self.assertFalse(value["release_authorized"])
        self.assertFalse(value["quality_evidence_eligible"])
        self.assertEqual(value["evidence_scope"], "test-only")

    def test_task_start_must_follow_registration_and_fit_the_window(self):
        for started_at in ("2026-09-24T09:00:00Z", "2026-09-24T10:30:00Z",
                           "2026-09-24T10:59:59.999999Z"):
            with self.subTest(started_at=started_at):
                self.data = synthetic_task_trials(self.root)
                self.mutate_observation(lambda envelope, *_: envelope["run"].update(started_at=started_at))
                with self.assertRaisesRegex(ManifestError, "task-0.*observation window"):
                    self.compare()

    def test_task_window_boundaries_and_equivalent_timezones_are_valid(self):
        def change(envelope, *_):
            envelope["run"].update(started_at="2026-09-24T19:00:00+08:00",
                                   finished_at="2026-09-24T22:00:00+08:00")

        self.mutate_observation(change)
        self.assertEqual(self.compare()["comparison"]["run_count"], 36)

    def test_same_task_acceptance_composition_cannot_drift(self):
        for category in ("checks", "guardrails"):
            for mutation in ("rename", "add", "remove"):
                for side, trial in (("candidate", 0), ("baseline", 1)):
                    with self.subTest(category=category, mutation=mutation, side=side, trial=trial):
                        self.data = synthetic_task_trials(self.root)

                        def change(envelope, events, acceptance, root):
                            if mutation == "rename":
                                acceptance[category][0]["name"] = "changed-criterion"
                            elif mutation == "add":
                                extra = copy.deepcopy(acceptance[category][0])
                                extra["name"] = "added-criterion"
                                acceptance[category].append(extra)
                            else:
                                acceptance[category] = []
                                if category == "checks":
                                    acceptance["status"] = "not-run"

                        self.mutate_observation(change, side=side, trial=trial)
                        with self.assertRaisesRegex(ManifestError, "task-0.*acceptance composition"):
                            self.compare()

    def test_acceptance_composition_ignores_results_order_and_other_tasks(self):
        for side in ("baseline", "candidate"):
            for trial in range(3):
                def change(envelope, events, acceptance, root):
                    for category in ("checks", "guardrails"):
                        first = copy.deepcopy(acceptance[category][0])
                        first["name"] = "task-one-first"
                        second = copy.deepcopy(first)
                        second["name"] = "task-one-second"
                        acceptance[category] = [first, second] if side == "baseline" else [second, first]
                    if side == "candidate" and trial == 1:
                        acceptance["status"] = acceptance["checks"][0]["status"] = "failed"
                        acceptance["checks"][0]["evidence"] = write_json(root / "failed-check.json", {
                            "synthetic": True, "observation": "failed",
                        })

                self.mutate_observation(change, side=side, task=1, trial=trial)
        value = self.compare()
        self.assertEqual(value["comparison"]["run_count"], 36)
        self.assertEqual(value["comparison"]["outcome_counts"]["candidate"]["failed"], 1)

    def test_contract_is_checked_once_and_reloaded_on_the_next_invocation(self):
        repository = self.root.parent / "contract-source"
        for relative in ("manifests/agent_value_contracts.json", "schemas/agent-value-contracts-v1.schema.json"):
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        manifest = Manifest(repository, MANIFEST.data, repository / "manifest.json")
        profile = cProfile.Profile()
        profile.enable()
        value = compare_task_trials(self.path, manifest)
        profile.disable()
        self.assertEqual(value["comparison"]["run_count"], 36)
        loads = [entry for entry in profile.getstats() if not isinstance(entry.code, str)
                 and entry.code.co_name == "load_contract"
                 and entry.code.co_filename.endswith("/agent_value_contracts.py")]
        self.assertEqual(sum(entry.callcount for entry in loads), 1)

        contract_path = repository / "manifests/agent_value_contracts.json"
        original = contract_path.read_bytes()
        write_json(contract_path, {"schema_version": "invalid-contract"})
        with self.assertRaisesRegex(ManifestError, "agent value contract"):
            compare_task_trials(self.path, manifest)
        contract_path.write_bytes(original)
        schema_path = repository / "schemas/agent-value-contracts-v1.schema.json"
        schema = json.loads(schema_path.read_text())
        schema["required"].append("new-required-field")
        write_json(schema_path, schema)
        with self.assertRaisesRegex(ManifestError, "agent value contract"):
            compare_task_trials(self.path, manifest)

    def test_same_input_different_workspace_cannot_be_controlled_comparison(self):
        def change(envelope, events, acceptance, root):
            envelope["workspace_snapshot"] = write_json(root / "initial.json", {"synthetic": True, "different_state": True})

        self.mutate_observation(change)
        with self.assertRaisesRegex(ManifestError, "initial workspace/source drift"):
            self.compare()

    def test_input_or_source_drift_rejected_despite_matching_controls(self):
        original = copy.deepcopy(self.data)
        for change in ("input", "source"):
            with self.subTest(change=change):
                self.data = copy.deepcopy(original)
                def mutate(envelope, events, acceptance, root):
                    if change == "input":
                        envelope["input_snapshot"] = write_json(root / "input.json", {"synthetic": True, "changed_goal": True})
                    else:
                        envelope["run"]["source_sha"] = "d" * 40
                self.mutate_observation(mutate)
                with self.assertRaises(ManifestError):
                    self.compare()

    def test_cross_trial_assigned_exposure_and_content_drift_rejected(self):
        def content_change(envelope, events, acceptance, root):
            skill = root / "skill.md"
            skill.write_text("Synthetic changed Skill revision\n", encoding="utf-8")
            digest = sha256_bytes(skill.read_bytes())
            envelope["skill_exposure"]["content"]["sha256"] = digest
            events["events"][1]["content_sha256"] = digest

        self.mutate_observation(content_change, trial=1)
        with self.assertRaisesRegex(ManifestError, "assignment or grader"):
            self.compare()

    def test_absent_assignment_drift_is_not_silently_pooled(self):
        def change(envelope, events, acceptance, root):
            envelope["skill_exposure"]["expected"] = "absent"
            events["events"] = [item for item in events["events"] if item["kind"] != "skill-load"]

        self.mutate_observation(change, trial=1)
        with self.assertRaisesRegex(ManifestError, "assignment or grader"):
            self.compare()

    def test_missing_actual_load_remains_in_assigned_population(self):
        def change(envelope, events, acceptance, root):
            events["events"] = [item for item in events["events"] if item["kind"] != "skill-load"]
            acceptance["status"] = "failed"
            acceptance["checks"][0]["status"] = "failed"

        self.mutate_observation(change)
        value = self.compare()
        self.assertEqual(value["comparison"]["run_count"], 36)
        self.assertEqual(value["comparison"]["outcome_counts"]["candidate"]["failed"], 1)
        self.assertGreater(value["comparison"]["metrics"]["wrong-skill-rate"]["candidate"]["mean"], 0)
        self.assertNotEqual(value["verdict"], "improved")

    def test_repeated_skill_load_keeps_retry_in_complete_population(self):
        def change(envelope, events, acceptance, root):
            reload = copy.deepcopy(events["events"][1])
            reload["event_id"] = "load-2"
            retry = copy.deepcopy(events["events"][3])
            retry.update(event_id="model-2", call_id="model-2", attempt_id="attempt-2")
            events["events"].extend([
                {"event_id": "attempt-2", "kind": "attempt", "attempt_id": "attempt-2"}, reload, retry,
            ])

        self.mutate_observation(change)
        value = self.compare()
        comparison = value["comparison"]
        self.assertEqual(value["verdict"], "improved")  # Synthetic latency arithmetic, not runtime evidence.
        self.assertEqual(comparison["run_count"], 36)
        self.assertEqual(comparison["outcome_counts"]["candidate"]["succeeded"], 18)
        metrics = comparison["metrics"]
        for metric in ("cost-per-task", "token-usage-per-task"):
            self.assertGreater(metrics[metric]["candidate"]["mean"], metrics[metric]["baseline"]["mean"])
        self.assertLess(metrics["first-pass-success-rate"]["candidate"]["mean"], 1)

    def test_repeated_process_check_cannot_hide_earlier_failure(self):
        def change(envelope, events, acceptance, root):
            failed = events["events"][-1]
            failed["status"] = "failed"
            later = copy.deepcopy(failed)
            later.update(event_id="guardrail-recheck", status="passed")
            events["events"].append(later)

        self.mutate_observation(change)
        value = self.compare()
        self.assertEqual(value["comparison"]["run_count"], 36)
        self.assertEqual(value["comparison"]["outcome_counts"]["candidate"]["failed"], 1)
        self.assertEqual(value["verdict"], "regressed")
        self.assertEqual(value["comparison"]["reason"], "observed-guardrail-failure")

    def test_timeout_stays_in_failure_denominator(self):
        def change(envelope, events, acceptance, root):
            acceptance["status"] = "not-run"
            acceptance["checks"][0]["status"] = "not-run"
            events["events"].append({"event_id": "timeout", "kind": "termination", "status": "failed",
                                     "category": "timeout", "evidence": events["events"][-1]["evidence"]})

        self.mutate_observation(change)
        value = self.compare()
        self.assertEqual(value["comparison"]["run_count"], 36)
        self.assertEqual(value["comparison"]["outcome_counts"]["candidate"]["failed"], 1)
        self.assertNotEqual(value["verdict"], "improved")

    def test_no_skill_control_contamination_is_invalid(self):
        self.data["conditions"]["baseline"]["task-0"]["expected"] = "absent"
        self.data["plan"]["controls"]["dataset_ref"] = task_trial_controls_ref(self.data)
        def change(envelope, events, acceptance, root):
            envelope["skill_exposure"]["expected"] = "absent"
            # Leave the observed target load to exercise real contamination.
        self.mutate_observation(change, side="baseline")
        with self.assertRaisesRegex(ManifestError, "declared intervention"):
            self.compare()

    def test_different_skills_per_task_are_supported_without_pooling_controls(self):
        for side in ("baseline", "candidate"):
            self.data["conditions"][side]["task-1"]["target_skill"] = "adk-debugging"
            for trial in range(3):
                def change(envelope, events, acceptance, root):
                    envelope["skill_exposure"]["target_skill"] = "adk-debugging"
                    events["events"][1]["skill"] = "adk-debugging"
                self.mutate_observation(change, side=side, task=1, trial=trial)
        self.data["plan"]["controls"]["dataset_ref"] = task_trial_controls_ref(self.data)
        self.assertEqual(self.compare()["comparison"]["run_count"], 36)

    def test_per_task_assignment_coverage_and_frozen_binding_are_enforced(self):
        original = copy.deepcopy(self.data)
        for change in ("missing", "extra", "unbound-edit"):
            with self.subTest(change=change):
                self.data = copy.deepcopy(original)
                assigned = self.data["conditions"]["candidate"]
                if change == "missing":
                    del assigned["task-0"]
                elif change == "extra":
                    assigned["not-planned"] = assigned["task-0"]
                else:
                    assigned["task-0"]["expected"] = "absent"
                with self.assertRaises(ManifestError):
                    self.compare()

    def test_mixed_synthetic_and_recorded_origins_rejected(self):
        self.mutate_observation(lambda envelope, *_: envelope.update(provenance="recorded-task"))
        with self.assertRaisesRegex(ManifestError, "provenance"):
            self.compare()

    def test_duplicate_missing_and_frozen_plan_drift_are_rejected(self):
        original = copy.deepcopy(self.data)
        for change in ("duplicate", "missing", "dataset", "task-binding", "grader"):
            with self.subTest(change=change):
                self.data = copy.deepcopy(original)
                if change == "duplicate":
                    self.data["trials"][1]["candidate"][0] = self.data["trials"][0]["candidate"][0]
                elif change == "missing":
                    self.data["trials"][0]["candidate"].pop()
                elif change == "dataset":
                    self.data["plan"]["controls"]["dataset_ref"] = "ref:" + "0" * 64
                elif change == "grader":
                    self.data["grader_id"] = "another-grader"
                else:
                    self.data["task_bindings"].append(self.data["task_bindings"][0])
                with self.assertRaises(ManifestError):
                    self.compare()

    def test_observation_digest_and_bounded_campaign_are_enforced(self):
        self.data["trials"][0]["baseline"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ManifestError, "digest mismatch"):
            self.compare()
        self.data = synthetic_task_trials(self.root)
        with patch("agent_dev_kit.task_trials.MAX_OBSERVATIONS", 1):
            with self.assertRaisesRegex(ManifestError, "excessive observations"):
                self.compare()
        with patch("agent_dev_kit.task_trials.MAX_CAMPAIGN_BYTES", 1):
            with self.assertRaisesRegex(ManifestError, "byte limit"):
                self.compare()

    def test_output_cannot_overwrite_campaign_or_nested_evidence(self):
        for output in (self.path, self.root / "candidate-0-0/input.json", self.root / "baseline-1-2/check.json"):
            with self.subTest(output=output.name):
                before = output.read_bytes()
                with self.assertRaises(ManifestError):
                    self.compare(output_path=output)
                self.assertEqual(output.read_bytes(), before)

    def test_real_compare_task_cli_compares_and_sanitizes_invalid_input(self):
        output = self.root.parent / "comparison.json"
        command = ["bash", str(ROOT / "scripts/devkit.sh"), "eval", "compare-task-trials", "--input", str(self.path),
                   "--output", str(output), "--summary-json"]
        completed = subprocess.run(command, cwd=ROOT, env={**os.environ, "ADK_PYTHON_BIN": sys.executable},
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout), json.loads(output.read_text()))
        before = output.read_bytes()
        self.path.write_text('{"untrusted":"must-not-echo-this"}', encoding="utf-8")
        completed = subprocess.run(command, cwd=ROOT, env={**os.environ, "ADK_PYTHON_BIN": sys.executable},
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "invalid")
        self.assertNotIn("must-not-echo", completed.stdout + completed.stderr)
        self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
