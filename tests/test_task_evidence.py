"""Synthetic packages prove import mechanics, never real model effectiveness."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.effect_trials import compare_effect_trials
from agent_dev_kit.model import Manifest, ManifestError, sha256_bytes
from agent_dev_kit.run_evidence import validate_run_evidence
from agent_dev_kit.task_evidence import _Package, import_task_evidence, read_task_evidence

from test_effect_trials import document, rebind

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests/agent_value_contracts.json")


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return {"path": path.name, "sha256": sha256_bytes(path.read_bytes())}


def synthetic_package(root, *, side="candidate", task=0, trial=0):
    """Create an explicitly synthetic, caller-observed development package."""
    root.mkdir(parents=True, exist_ok=True)
    run_id = f"{side}-task-{task}-trial-{trial}"
    input_ref = write_json(root / "input.json", {"synthetic": True, "goal": "copy the expected result"})
    workspace_ref = write_json(root / "initial.json", {"synthetic": True, "files": []})
    artifact = write_json(root / "result.json", {"synthetic": True, "answer": 42})
    checked = write_json(root / "check.json", {"synthetic": True, "expected": 42, "actual": 42})
    process = write_json(root / "process.json", {"synthetic": True, "observed_permission_boundary": "passed"})
    skill = root / "skill.md"
    skill.write_text("# Synthetic skill exposure for importer testing only\n", encoding="utf-8")
    skill_ref = {"path": skill.name, "sha256": sha256_bytes(skill.read_bytes())}
    acceptance = {
        "schema_version": "adk-task-acceptance/v1", "run_id": run_id, "task_id": f"task-{task}",
        "executor_id": "synthetic-executor", "grader_id": "synthetic-independent-grader", "status": "passed",
        "artifacts": [artifact], "checks": [{"name": "expected-result", "status": "passed", "evidence": checked}],
        "guardrails": [{"name": "artifact-boundary", "status": "passed", "evidence": checked}],
        "trust": "caller-observed", "evidence_scope": "test-only", "raw_content_stored": False,
    }
    events = {
        "schema_version": "adk-task-events/v1", "run_id": run_id,
        "coverage": {key: True for key in (
            "tools", "human_interventions", "skill_loads", "attempts", "handoffs", "guardrails", "model_calls",
        )},
        "events": [
            {"event_id": "attempt-1", "seq": 1, "kind": "attempt", "attempt_id": "attempt-1"},
            {"event_id": "load-1", "seq": 2, "kind": "skill-load", "skill": "adk-requirements-triage",
             "content_sha256": skill_ref["sha256"], "primary": True},
            {"event_id": "tool-1", "seq": 3, "kind": "tool-call", "attempt_id": "attempt-1",
             "tool": "read-artifact", "outcome": "succeeded"},
            {"event_id": "model-1", "seq": 4, "kind": "model-call", "attempt_id": "attempt-1",
             "call_id": "model-1", "accounting": "exclusive-call", "usage_source": "runtime-reported",
             "usage": {"input": 20, "cached_input": 2, "output": 5}, "cost_source": "provider-reported",
             "cost": {"amount": 1, "currency": "USD"}},
            {"event_id": "guardrail-1", "seq": 5, "kind": "guardrail", "name": "permission-boundary",
             "status": "passed", "evidence": process},
        ],
    }
    elapsed = 100 if side == "baseline" else 70
    start = datetime(2026, 9, 24, 12, trial, tzinfo=timezone.utc)
    envelope = {
        "schema_version": "adk-task-observation/v1", "provenance": "synthetic-fixture",
        "run": {"run_id": run_id, "task_id": f"task-{task}", "executor_id": "synthetic-executor",
                "source_sha": "c" * 40, "asset_bundle_sha256": ("a" if side == "baseline" else "b") * 64,
                "runtime_target": "test-harness", "runtime_version": "runtime-v1", "model_version": "model-revision-1",
                "prompt_version": "fixed-prompt-v1", "orchestration_mode": "single-agent",
                "started_at": start.isoformat(), "finished_at": (start + timedelta(milliseconds=elapsed)).isoformat(),
                "privacy_status": "no-sensitive-content"},
        "input_snapshot": input_ref, "workspace_snapshot": workspace_ref,
        "events": write_json(root / "events.json", events),
        "acceptance": write_json(root / "acceptance.json", acceptance), "artifacts": [artifact],
        "skill_exposure": {"target_skill": "adk-requirements-triage", "expected": "loaded", "content": skill_ref},
    }
    write_json(root / "observation.json", envelope)
    return envelope, events, acceptance


class TaskEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "synthetic-package"
        self.data, self.events, self.acceptance = synthetic_package(self.root)
        self.path = self.root / "observation.json"

    def persist(self):
        for index, item in enumerate(self.events["events"], 1):
            item["seq"] = index
        self.data["events"] = write_json(self.root / "events.json", self.events)
        self.data["acceptance"] = write_json(self.root / "acceptance.json", self.acceptance)
        write_json(self.path, self.data)

    def import_data(self):
        self.persist()
        return import_task_evidence(self.path, MANIFEST)

    def diagnose_data(self):
        self.persist()
        return import_task_evidence(self.path, MANIFEST, diagnostics=True)

    def process_observations(self, statuses):
        template = next(item for item in self.events["events"] if item["kind"] == "guardrail")
        self.events["events"] = [item for item in self.events["events"] if item["kind"] != "guardrail"]
        references = []
        for index, status in enumerate(statuses):
            reference = write_json(self.root / f"process-{index}.json", {
                "synthetic": True, "observation": index, "status": status,
            })
            event = copy.deepcopy(template)
            event.update(event_id=f"guardrail-observation-{index}", status=status, evidence=reference)
            self.events["events"].append(event)
            references.append(reference)
        return references

    def cli(self, *args):
        return subprocess.run(
            ["bash", str(ROOT / "scripts/devkit.sh"), "eval", *map(str, args)],
            cwd=ROOT, env={**os.environ, "ADK_PYTHON_BIN": sys.executable},
            capture_output=True, text=True, timeout=30,
        )

    def test_import_is_existing_run_evidence_with_bounded_authority(self):
        result = self.import_data()
        validate_run_evidence(result["run_evidence"], MANIFEST, CONTRACT)
        self.assertEqual(result["provenance"], "synthetic-fixture")
        self.assertEqual(result["trust"], "caller-observed")
        self.assertEqual(result["evidence_scope"], "test-only")
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["quality_evidence_eligible"])
        self.assertFalse(result["raw_content_stored"])
        trace = result["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"], {"status": "succeeded", "category": "completed"})
        self.assertTrue(trace["first_pass_success"])
        self.assertEqual(trace["tool_calls"], 1)
        self.assertEqual(trace["token_usage"], {"input": 20, "cached_input": 2, "output": 5})
        self.assertEqual({item["name"] for item in trace["guardrails"]},
                         {"process/permission-boundary", "artifact/artifact-boundary"})
        self.assertEqual(result["run_evidence"]["receipts"], [])
        self.assertIsNone(result["run_evidence"]["measurement"])
        self.assertNotIn("copy the expected", json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_diagnostics_are_opt_in_and_reuse_exactly_the_same_verified_reads(self):
        self.persist()
        reads = []
        original_read = _Package.read

        def observed_read(package, path):
            reads.append(path)
            return original_read(package, path)

        with patch.object(_Package, "read", observed_read):
            plain = read_task_evidence(self.path, MANIFEST)
            plain_reads = tuple(reads)
            reads.clear()
            diagnosed = read_task_evidence(self.path, MANIFEST, diagnostics=True)
        self.assertEqual(tuple(reads), plain_reads)
        self.assertEqual(diagnosed.inputs, plain.inputs)
        self.assertEqual(diagnosed.bytes_read, plain.bytes_read)
        self.assertNotIn("diagnostics", plain.report)
        diagnostic = diagnosed.report.pop("diagnostics")
        self.assertEqual(diagnosed.report, plain.report)
        self.assertEqual(diagnostic, self.diagnose_data()["diagnostics"])
        self.assertEqual(diagnostic["facts"]["attempt_count"], 1)
        self.assertEqual(diagnostic["facts"]["recorded_model_call_count"], 1)
        self.assertEqual(diagnostic["evidence_refs"], {
            "trace_ref": plain.report["run_evidence"]["trace_ref"],
            "events_ref": plain.report["bindings"]["events_ref"],
        })
        self.assertEqual(plain.report["run_evidence"]["receipts"], [])
        self.assertIsNone(plain.report["run_evidence"]["measurement"])
        self.assertFalse(plain.report["quality_evidence_eligible"])
        self.assertFalse(plain.report["release_authorized"])
        self.assertNotIn(str(self.root), json.dumps(diagnostic))

    def test_diagnostics_fifty_successful_calls_are_counts_without_waste_judgment(self):
        for index in range(2, 51):
            self.events["events"].append({
                "event_id": f"tool-{index}", "kind": "tool-call", "attempt_id": "attempt-1",
                "tool": "read-artifact", "outcome": "succeeded",
            })
        diagnostic = self.diagnose_data()["diagnostics"]
        self.assertEqual(diagnostic["facts"]["tool_calls"], 50)
        self.assertEqual(diagnostic["facts"]["tool_outcome_counts"], {"read-artifact": {
            "succeeded": 50, "failed": 0, "partial": 0, "blocked": 0, "cancelled": 0, "not-available": 0,
        }})
        self.assertEqual(diagnostic["findings"], [])
        self.assertNotIn("waste", json.dumps(diagnostic))

    def test_diagnostics_mixed_terminal_counts_and_successful_attempts_are_not_inferred(self):
        self.events["events"].append({"event_id": "attempt-2", "kind": "attempt", "attempt_id": "attempt-2"})
        outcomes = ("failed", "failed", "succeeded", "blocked", "cancelled", "partial", "not-available")
        for index, outcome in enumerate(outcomes, 2):
            self.events["events"].append({
                "event_id": f"tool-{index}", "kind": "tool-call", "attempt_id": "attempt-2",
                "tool": "read-artifact", "outcome": outcome,
            })
        self.events["events"].append({"event_id": "attempt-3", "kind": "attempt", "attempt_id": "attempt-3"})
        retry = copy.deepcopy(self.events["events"][3])
        retry.update(event_id="model-2", call_id="model-2", attempt_id="attempt-3")
        self.events["events"].append(retry)
        result = self.diagnose_data()
        diagnostic = result["diagnostics"]
        facts = diagnostic["facts"]
        self.assertEqual(facts["outcome"], {"status": "succeeded", "category": "completed"})
        self.assertFalse(facts["first_pass_success"])
        self.assertEqual(facts["attempt_count"], 3)
        self.assertEqual(facts["recorded_model_call_count"], 2)
        self.assertEqual(facts["tool_calls"], 8)
        self.assertEqual(facts["tools_used"], [{"name": "read-artifact", "call_count": 8, "outcome": "partial"}])
        self.assertEqual(facts["tool_outcome_counts"], {"read-artifact": {
            "succeeded": 2, "failed": 2, "partial": 1, "blocked": 1, "cancelled": 1, "not-available": 1,
        }})
        self.assertEqual(diagnostic["findings"], [{
            "code": "tool-outcome", "location": "/tools_used/0", "fact": facts["tools_used"][0],
        }])
        for unsupported in ("waste", "blind-retry", "savings"):
            self.assertNotIn(unsupported, json.dumps(diagnostic))

    def test_diagnostics_keep_process_failures_even_when_later_checks_and_artifact_pass(self):
        references = self.process_observations(("failed", "passed"))
        self.events["events"].append({
            "event_id": "guardrail-other", "kind": "guardrail", "name": "other-boundary",
            "status": "failed", "evidence": references[0],
        })
        result = self.diagnose_data()
        self.assertEqual(result["acceptance_status"], "passed")
        facts = result["diagnostics"]["facts"]
        self.assertEqual(facts["outcome"]["status"], "failed")
        self.assertEqual(facts["failure_pattern"], "process-guardrail-failed")
        failures = [item for item in result["diagnostics"]["findings"] if item["code"] == "verification-status"]
        self.assertEqual({item["fact"]["name"] for item in failures},
                         {"process/permission-boundary", "process/other-boundary"})
        self.assertTrue(all(item["fact"]["status"] == "failed" for item in failures))
        self.assertTrue(all(item["fact"]["evidence_ref"] == "ref:" + references[0]["sha256"] for item in failures))
        self.assertEqual(facts["verification"], result["run_evidence"]["trace_summary"]["verification"])

    def test_diagnostics_unrun_acceptance_stays_unknown_until_observed_timeout(self):
        self.acceptance["status"] = "not-run"
        self.acceptance["checks"][0]["status"] = "not-run"
        self.acceptance["checks"].append({**self.acceptance["checks"][0], "name": "second-check"})
        result = self.diagnose_data()
        self.assertEqual(result["diagnostics"]["facts"]["outcome"], {
            "status": "not-available", "reason": "artifact-acceptance-not-observed",
        })
        self.events["events"].append({
            "event_id": "timeout", "kind": "termination", "status": "failed", "category": "timeout",
            "evidence": self.events["events"][-1]["evidence"],
        })
        diagnosed = self.diagnose_data()["diagnostics"]
        self.assertEqual(diagnosed["facts"]["outcome"], {"status": "failed", "category": "runtime-failure"})
        self.assertEqual(diagnosed["facts"]["failure_pattern"], "runtime-timeout")
        for report in (result["diagnostics"], diagnosed):
            unrun = [item["fact"]["name"] for item in report["findings"]
                     if item["code"] == "verification-status" and item["fact"]["status"] == "not-run"]
            self.assertEqual(unrun, ["acceptance/expected-result", "acceptance/second-check"])
        self.assertTrue(any(item["fact"].get("name") == "runtime-termination"
                            for item in diagnosed["findings"] if isinstance(item["fact"], dict)))

    def test_diagnostics_preserve_missing_and_estimated_metric_reasons(self):
        original = copy.deepcopy(self.events)
        for change in ("coverage", "usage", "cost", "estimated-usage", "estimated-cost", "no-model-calls"):
            with self.subTest(change=change):
                self.events = copy.deepcopy(original)
                model = self.events["events"][3]
                if change == "coverage":
                    self.events["coverage"]["model_calls"] = False
                elif change == "no-model-calls":
                    self.events["events"] = [item for item in self.events["events"] if item["kind"] != "model-call"]
                elif change.startswith("estimated-"):
                    model["usage_source" if change.endswith("usage") else "cost_source"] = "estimated"
                else:
                    model[change] = None
                result = self.diagnose_data()
                trace = result["run_evidence"]["trace_summary"]
                facts = result["diagnostics"]["facts"]
                self.assertEqual(facts["recorded_model_call_count"], 0 if change == "no-model-calls" else 1)
                for metric in ("token_usage", "cost"):
                    self.assertEqual(facts[metric], trace[metric])
                    if trace[metric].get("status") == "not-available":
                        self.assertTrue(any(item["code"] == "metric-unavailable" and item["fact"] == trace[metric]
                                            for item in result["diagnostics"]["findings"]))

    def test_diagnostics_observed_zero_and_handoff_walltime_have_no_efficiency_inference(self):
        model = self.events["events"][3]
        model["usage"] = {"input": 0, "cached_input": 0, "output": 0}
        model["cost"]["amount"] = 0
        self.events["events"] = [item for item in self.events["events"] if item["kind"] != "tool-call"]
        start = datetime.fromisoformat(self.data["run"]["started_at"])
        self.data["run"]["finished_at"] = (start + timedelta(milliseconds=1000)).isoformat()
        for index in range(3):
            self.events["events"].append({
                "event_id": f"handoff-{index}", "kind": "handoff", "target": "child", "outcome": "succeeded",
            })
        diagnostic = self.diagnose_data()["diagnostics"]
        self.assertEqual(diagnostic["facts"]["tool_calls"], 0)
        self.assertEqual(diagnostic["facts"]["tool_outcome_counts"], {})
        self.assertEqual(diagnostic["facts"]["token_usage"], {"input": 0, "cached_input": 0, "output": 0})
        self.assertEqual(diagnostic["facts"]["cost"], {"status": "available", "amount": 0, "currency": "USD"})
        self.assertEqual(diagnostic["facts"]["elapsed_ms"], 1000)
        self.assertEqual(len(diagnostic["facts"]["handoffs"]), 3)
        self.assertEqual(diagnostic["findings"], [])
        for unsupported in ("parallel_wait", "savings"):
            self.assertNotIn(unsupported, json.dumps(diagnostic))

    def test_diagnostics_cli_preserves_failed_task_import_and_sanitized_invalid_output(self):
        self.acceptance["status"] = self.acceptance["checks"][0]["status"] = "failed"
        self.persist()
        plain = self.cli("import-task", "--input", self.path, "--summary-json")
        self.assertEqual(plain.returncode, 0, plain.stdout + plain.stderr)
        self.assertNotIn("diagnostics", json.loads(plain.stdout))
        output = self.root.parent / "diagnosed.json"
        completed = self.cli("import-task", "--input", self.path, "--diagnostics", "--output", output,
                             "--summary-json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result, json.loads(output.read_text()))
        self.assertEqual(result["diagnostics"]["facts"]["outcome"]["status"], "failed")
        result.pop("diagnostics")
        self.assertEqual(result, json.loads(plain.stdout))
        previous = output.read_bytes()
        self.path.write_text('{"raw_secret":"do-not-echo-this-secret"}', encoding="utf-8")
        completed = self.cli("import-task", "--input", self.path, "--diagnostics", "--output", output,
                             "--summary-json")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "invalid")
        self.assertNotIn("diagnostics", json.loads(completed.stdout))
        self.assertNotIn("do-not-echo", completed.stdout + completed.stderr)
        self.assertEqual(output.read_bytes(), previous)

    def test_diagnostics_cannot_overwrite_inputs_or_any_output_alias(self):
        original_process = self.events["events"][-1]["evidence"]
        self.process_observations(("failed", "passed"))
        self.events["events"].append({
            "event_id": "guardrail-extra", "kind": "guardrail", "name": "another-boundary",
            "status": "passed", "evidence": original_process,
        })
        self.persist()
        originals = {path: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        hardlink = self.root / "hardlink.json"
        os.link(self.path, hardlink)
        symbolic = self.root / "symlink.json"
        symbolic.symlink_to(self.path)
        directory_alias = self.root.parent / "linked-output"
        directory_alias.symlink_to(self.root, target_is_directory=True)
        for output in (*originals, hardlink, symbolic, directory_alias / "new.json"):
            with self.subTest(output=output), self.assertRaises(ManifestError):
                import_task_evidence(self.path, MANIFEST, output_path=output, diagnostics=True)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertFalse((self.root / "new.json").exists())

    def test_diagnostics_keep_digest_and_no_follow_input_checks(self):
        self.persist()
        source = self.root / "input.json"
        original = source.read_bytes()
        source.write_bytes(original + b" ")
        with self.assertRaisesRegex(ManifestError, "digest mismatch"):
            import_task_evidence(self.path, MANIFEST, diagnostics=True)
        source.write_bytes(original)
        source.rename(self.root / "original.json")
        source.symlink_to("original.json")
        with self.assertRaises(OSError):
            import_task_evidence(self.path, MANIFEST, diagnostics=True)

    def test_failed_retry_and_handoff_costs_are_retained(self):
        self.events["events"][2]["outcome"] = "failed"
        retry = copy.deepcopy(self.events["events"][3])
        retry.update(event_id="model-2", call_id="child-model-2", attempt_id="attempt-2")
        self.events["events"].extend([
            {"event_id": "attempt-2", "kind": "attempt", "attempt_id": "attempt-2"},
            {"event_id": "handoff-1", "kind": "handoff", "target": "synthetic-child", "outcome": "succeeded"},
            retry,
            {"event_id": "tool-2", "kind": "tool-call", "attempt_id": "attempt-2",
             "tool": "read-artifact", "outcome": "succeeded"},
            {"event_id": "human-1", "kind": "human-intervention", "category": "correction"},
        ])
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["tool_calls"], 2)
        self.assertEqual(trace["tools_used"][0]["outcome"], "partial")
        self.assertEqual(trace["token_usage"]["input"], 40)
        self.assertEqual(trace["cost"]["amount"], 2)
        self.assertEqual(trace["human_interventions"], 1)
        self.assertEqual(len(trace["handoffs"]), 1)
        self.assertFalse(trace["first_pass_success"])

    def test_repeated_skill_load_preserves_retry_costs_and_ledger(self):
        reload = copy.deepcopy(self.events["events"][1])
        reload["event_id"] = "load-2"
        retry = copy.deepcopy(self.events["events"][3])
        retry.update(event_id="model-2", call_id="child-model-2", attempt_id="attempt-2")
        self.events["events"].extend([
            {"event_id": "attempt-2", "kind": "attempt", "attempt_id": "attempt-2"},
            reload,
            {"event_id": "handoff-1", "kind": "handoff", "target": "synthetic-child", "outcome": "succeeded"},
            retry,
            {"event_id": "tool-2", "kind": "tool-call", "attempt_id": "attempt-2",
             "tool": "read-artifact", "outcome": "succeeded"},
        ])
        result = self.import_data()
        trace = result["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"]["status"], "succeeded")
        self.assertEqual(trace["primary_skill"], "adk-requirements-triage")
        self.assertFalse(trace["wrong_skill"])
        self.assertFalse(trace["first_pass_success"])
        self.assertEqual(trace["tool_calls"], 2)
        self.assertEqual(trace["token_usage"], {"input": 40, "cached_input": 4, "output": 10})
        self.assertEqual(trace["cost"]["amount"], 2)
        self.assertEqual(len(trace["handoffs"]), 1)
        self.assertEqual(result["bindings"]["events_ref"], "ref:" + self.data["events"]["sha256"])
        self.assertEqual(sum(event["kind"] == "skill-load" for event in self.events["events"]), 2)

    def test_repeated_skill_load_conflicts_and_duplicate_identity_still_rejected(self):
        original = copy.deepcopy((self.data, self.events))
        for conflict in ("digest", "role", "role-type", "multiple-primary", "event-id", "absent"):
            with self.subTest(conflict=conflict):
                self.data, self.events = copy.deepcopy(original)
                reload = copy.deepcopy(self.events["events"][1])
                reload["event_id"] = "load-2"
                if conflict == "digest":
                    reload["content_sha256"] = "d" * 64
                elif conflict == "role":
                    reload["primary"] = False
                elif conflict == "role-type":
                    reload["primary"] = 1
                elif conflict == "multiple-primary":
                    reload["skill"] = "adk-debugging"
                elif conflict == "event-id":
                    reload["event_id"] = self.events["events"][1]["event_id"]
                else:
                    self.data["skill_exposure"]["expected"] = "absent"
                self.events["events"].append(reload)
                with self.assertRaises(ManifestError):
                    self.import_data()

    def test_repeated_process_checks_preserve_worst_status_and_actual_evidence(self):
        cases = (
            ("passed", "passed", "passed"), ("failed", "passed", "failed"),
            ("passed", "failed", "failed"), ("failed", "failed", "failed"),
            ("not-applicable", "passed", "passed"), ("passed", "not-applicable", "passed"),
            ("failed", "not-applicable", "failed"), ("not-applicable", "failed", "failed"),
            ("not-applicable", "not-applicable", "not-applicable"),
        )
        for first, second, expected in cases:
            with self.subTest(first=first, second=second):
                references = self.process_observations((first, second))
                result = self.import_data()
                trace = result["run_evidence"]["trace_summary"]
                process = [item for item in trace["guardrails"] if item["name"] == "process/permission-boundary"]
                verification = [item for item in trace["verification"] if item["name"] == "process/permission-boundary"]
                self.assertEqual(process, [{"name": "process/permission-boundary", "status": expected}])
                self.assertEqual(len(verification), 1)
                self.assertEqual(verification[0]["status"], expected)
                self.assertIn(verification[0]["evidence_ref"], [
                    "ref:" + reference["sha256"] for status, reference in zip((first, second), references)
                    if status == expected
                ])
                self.assertEqual(trace["outcome"]["status"], "failed" if expected == "failed" else "succeeded")
                self.assertEqual(result["bindings"]["events_ref"], "ref:" + self.data["events"]["sha256"])

    def test_repeated_process_checks_validate_and_protect_unselected_evidence(self):
        for statuses in (("failed", "passed"), ("passed", "failed")):
            with self.subTest(statuses=statuses):
                references = self.process_observations(statuses)
                self.persist()
                unselected = self.root / references[statuses.index("passed")]["path"]
                original = unselected.read_bytes()
                unselected.write_bytes(original + b" ")
                with self.assertRaisesRegex(ManifestError, "digest mismatch"):
                    import_task_evidence(self.path, MANIFEST)
                unselected.write_bytes(original)
                with self.assertRaises(ManifestError):
                    import_task_evidence(self.path, MANIFEST, output_path=unselected)
                self.assertEqual(unselected.read_bytes(), original)

    def test_repeated_process_checks_do_not_expand_bounded_summary(self):
        reference = self.events["events"][-1]
        for index in range(160):
            event = copy.deepcopy(reference)
            event["event_id"] = f"guardrail-repeat-{index}"
            self.events["events"].append(event)
        result = self.import_data()
        trace = result["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"]["status"], "succeeded")
        self.assertEqual(sum(item["name"] == "process/permission-boundary" for item in trace["verification"]), 1)
        self.assertEqual(result["bindings"]["events_ref"], "ref:" + self.data["events"]["sha256"])

    def test_missing_or_estimated_usage_is_never_zero(self):
        original = copy.deepcopy(self.events)
        for change in ("missing-call", "usage", "cost", "estimated-usage", "estimated-cost"):
            with self.subTest(change=change):
                self.events = copy.deepcopy(original)
                model = self.events["events"][3]
                if change == "missing-call":
                    self.events["coverage"]["model_calls"] = False
                elif change.startswith("estimated-"):
                    model["usage_source" if change.endswith("usage") else "cost_source"] = "estimated"
                else:
                    model[change] = None
                trace = self.import_data()["run_evidence"]["trace_summary"]
                metric = "cost" if change in {"cost", "estimated-cost"} else "token_usage"
                self.assertEqual(trace[metric]["status"], "not-available")
        self.events = copy.deepcopy(original)
        self.events["events"] = [event for event in self.events["events"] if event["kind"] != "model-call"]
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["cost"]["status"], "not-available")
        self.assertEqual(trace["token_usage"]["status"], "not-available")

    def test_missing_counter_coverage_is_rejected(self):
        for name in ("tools", "human_interventions", "skill_loads", "attempts", "handoffs", "guardrails"):
            with self.subTest(name=name):
                self.events["coverage"][name] = False
                with self.assertRaisesRegex(ManifestError, "incomplete event coverage"):
                    self.import_data()
                self.events["coverage"][name] = True

    def test_acceptance_failure_blocked_and_missing_are_not_success(self):
        for status, expected in (("failed", "failed"), ("blocked", "blocked"), ("not-run", "not-available")):
            with self.subTest(status=status):
                self.acceptance["status"] = status
                self.acceptance["checks"][0]["status"] = "failed" if status == "failed" else "not-run"
                trace = self.import_data()["run_evidence"]["trace_summary"]
                self.assertEqual(trace["outcome"]["status"], expected)
                self.assertFalse(trace["first_pass_success"])

    def test_artifact_success_cannot_hide_process_failure(self):
        self.events["events"][-1]["status"] = "failed"
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"]["status"], "failed")
        self.assertEqual(trace["failure_pattern"], "process-guardrail-failed")
        self.assertEqual(self.import_data()["acceptance_status"], "passed")

    def test_observed_runtime_timeout_is_failed_even_without_acceptance(self):
        self.acceptance["status"] = "not-run"
        self.acceptance["checks"][0]["status"] = "not-run"
        self.events["events"].append({
            "event_id": "timeout", "kind": "termination", "status": "failed", "category": "timeout",
            "evidence": self.events["events"][-1]["evidence"],
        })
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"], {"status": "failed", "category": "runtime-failure"})
        self.assertEqual(trace["failure_pattern"], "runtime-timeout")
        self.assertFalse(trace["first_pass_success"])

    def test_artifact_boundary_failure_without_failed_check_is_retained(self):
        self.acceptance["status"] = "failed"
        self.acceptance["guardrails"][0]["status"] = "failed"
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["outcome"]["status"], "failed")
        self.assertEqual(trace["failure_pattern"], "artifact-acceptance-failed")

    def test_route_match_does_not_create_task_success(self):
        self.acceptance["status"] = "failed"
        self.acceptance["checks"][0]["status"] = "failed"
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertFalse(trace["wrong_skill"])
        self.assertEqual(trace["outcome"]["status"], "failed")
        self.events["events"][1]["skill"] = "adk-debugging"
        self.acceptance["status"] = self.acceptance["checks"][0]["status"] = "passed"
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertTrue(trace["wrong_skill"])
        self.assertEqual(trace["outcome"]["status"], "succeeded")
        self.assertFalse(trace["first_pass_success"])

    def test_success_requires_independent_verified_artifacts(self):
        original = copy.deepcopy(self.acceptance)
        for change in ("self-grade", "no-artifacts", "no-checks", "failed-check", "wrong-run", "wrong-artifact"):
            with self.subTest(change=change):
                self.acceptance = copy.deepcopy(original)
                if change == "self-grade":
                    self.acceptance["grader_id"] = self.acceptance["executor_id"]
                elif change == "no-artifacts":
                    self.acceptance["artifacts"] = []
                elif change == "no-checks":
                    self.acceptance["checks"] = []
                elif change == "failed-check":
                    self.acceptance["checks"][0]["status"] = "failed"
                elif change == "wrong-run":
                    self.acceptance["run_id"] = "another-run"
                else:
                    self.acceptance["artifacts"][0]["sha256"] = "d" * 64
                with self.assertRaises(ManifestError):
                    self.import_data()

    def test_digest_tampering_for_every_binding_is_rejected(self):
        self.persist()
        for name in ("input.json", "initial.json", "events.json", "acceptance.json", "result.json",
                     "check.json", "process.json", "skill.md"):
            with self.subTest(file=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ManifestError, "digest mismatch"):
                    import_task_evidence(self.path, MANIFEST)
                path.write_bytes(original)

    def test_path_escape_symlink_and_nonregular_files_are_rejected(self):
        original = copy.deepcopy(self.data["input_snapshot"])
        for path in ("../input.json", "/etc/passwd", "file:///etc/passwd", "a//b", "a/./b", "a\\b"):
            with self.subTest(path=path):
                self.data["input_snapshot"]["path"] = path
                with self.assertRaises(ManifestError):
                    self.import_data()
        self.data["input_snapshot"] = original
        source = self.root / "input.json"
        source.rename(self.root / "original.json")
        source.symlink_to("original.json")
        with self.assertRaises(OSError):
            self.import_data()
        source.unlink()
        source.mkdir()
        with self.assertRaises(ManifestError):
            self.import_data()
        source.rmdir()
        os.mkfifo(source)
        with self.assertRaises(ManifestError):
            self.import_data()
        source.unlink()
        (self.root / "original.json").rename(source)
        (self.root / "linked").symlink_to(self.root, target_is_directory=True)
        self.data["input_snapshot"]["path"] = "linked/input.json"
        with self.assertRaises(OSError):
            self.import_data()
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            import_task_evidence(alias / "observation.json", MANIFEST)

    def test_duplicate_events_calls_artifacts_and_checks_are_rejected(self):
        originals = copy.deepcopy((self.events, self.acceptance, self.data))
        for change in ("event", "model-call", "attempt", "artifact", "check"):
            with self.subTest(change=change):
                self.events, self.acceptance, self.data = copy.deepcopy(originals)
                if change == "artifact":
                    self.data["artifacts"] *= 2
                elif change == "check":
                    self.acceptance["checks"] *= 2
                else:
                    index = {"event": 2, "model-call": 3, "attempt": 0}[change]
                    duplicate = copy.deepcopy(self.events["events"][index])
                    if change != "event":
                        duplicate["event_id"] = "different-event"
                    self.events["events"].append(duplicate)
                with self.assertRaises(ManifestError):
                    self.import_data()

    def test_malformed_json_nonfinite_and_unknown_fields_are_rejected(self):
        for raw in (b'{"schema_version":1,"schema_version":2}', b'{"cost":NaN}', b"\xff", b"[" * 70 + b"]" * 70):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                import_task_evidence(self.path, MANIFEST)
        self.data["run"]["outcome"] = "succeeded"
        with self.assertRaisesRegex(ManifestError, "invalid run fields"):
            self.import_data()

    def test_model_double_accounting_boolean_counts_and_exposure_drift_rejected(self):
        original = copy.deepcopy(self.events)
        for change in ("inclusive", "boolean", "cached", "mixed-currency", "digest", "absent"):
            with self.subTest(change=change):
                self.events = copy.deepcopy(original)
                model = self.events["events"][3]
                if change == "inclusive":
                    model["accounting"] = "includes-children"
                elif change == "boolean":
                    model["usage"]["input"] = True
                elif change == "cached":
                    model["usage"]["cached_input"] = 21
                elif change == "mixed-currency":
                    another = copy.deepcopy(model)
                    another.update(event_id="model-2", call_id="model-2")
                    another["cost"]["currency"] = "EUR"
                    self.events["events"].append(another)
                elif change == "digest":
                    self.events["events"][1]["content_sha256"] = "0" * 64
                else:
                    self.data["skill_exposure"]["expected"] = "absent"
                with self.assertRaises(ManifestError):
                    self.import_data()

    def test_explicit_absence_is_preserved_for_no_skill_condition(self):
        self.data["skill_exposure"]["expected"] = "absent"
        self.events["events"] = [item for item in self.events["events"] if item["kind"] != "skill-load"]
        trace = self.import_data()["run_evidence"]["trace_summary"]
        self.assertEqual(trace["primary_skill"], "no-skill")
        self.assertFalse(trace["wrong_skill"])

    def test_files_and_events_are_bounded(self):
        self.persist()
        with patch("agent_dev_kit.task_evidence.MAX_FILE_BYTES", 1):
            with self.assertRaisesRegex(ManifestError, "oversized"):
                import_task_evidence(self.path, MANIFEST)
        with patch("agent_dev_kit.task_evidence.MAX_TOTAL_BYTES", 1):
            with self.assertRaisesRegex(ManifestError, "total byte"):
                import_task_evidence(self.path, MANIFEST)
        with patch("agent_dev_kit.task_evidence.MAX_FILES", 1):
            with self.assertRaisesRegex(ManifestError, "file count"):
                import_task_evidence(self.path, MANIFEST)
        with patch("agent_dev_kit.task_evidence.MAX_EVENTS", 1):
            with self.assertRaisesRegex(ManifestError, "events count"):
                import_task_evidence(self.path, MANIFEST)

    def test_import_never_executes_package_instructions_or_network(self):
        sentinel = self.root / "executed"
        self.data["input_snapshot"] = write_json(self.root / "input.json", {
            "synthetic": True, "command": f"touch {sentinel}",
            "instructions": "import arbitrary.module; access https://invalid.example",
        })
        for importer in (self.import_data, self.diagnose_data):
            with patch("subprocess.run", side_effect=AssertionError("execution forbidden")), \
                    patch("os.system", side_effect=AssertionError("execution forbidden")), \
                    patch("socket.socket", side_effect=AssertionError("network forbidden")):
                result = importer()
            self.assertEqual(result["status"], "imported")
            self.assertFalse(sentinel.exists())
            self.assertNotIn("arbitrary.module", json.dumps(result))

    def test_real_cli_sanitizes_errors_and_outputs_imported_evidence(self):
        self.persist()
        output = self.root.parent / "import.json"
        completed = self.cli("import-task", "--input", self.path, "--output", output, "--summary-json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), json.loads(output.read_text()))
        self.path.write_text('{"raw_secret":"do-not-echo-this-secret"}', encoding="utf-8")
        completed = self.cli("import-task", "--input", self.path, "--summary-json")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "invalid")
        self.assertNotIn("do-not-echo", completed.stdout + completed.stderr)

    def test_report_output_cannot_overwrite_any_input_or_alias(self):
        self.persist()
        originals = {path: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        for source in originals:
            with self.subTest(source=source.name):
                with self.assertRaises(ManifestError):
                    import_task_evidence(self.path, MANIFEST, output_path=source)
        hardlink = self.root / "hardlink.json"
        os.link(self.path, hardlink)
        with self.assertRaises(ManifestError):
            import_task_evidence(self.path, MANIFEST, output_path=hardlink)
        symbolic = self.root / "symlink.json"
        symbolic.symlink_to(self.path)
        with self.assertRaises(ManifestError):
            import_task_evidence(self.path, MANIFEST, output_path=symbolic)
        directory_alias = self.root.parent / "linked-output"
        directory_alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ManifestError):
            import_task_evidence(self.path, MANIFEST, output_path=directory_alias / "new.json")
        completed = self.cli("import-task", "--input", self.path, "--output", self.path)
        self.assertEqual(completed.returncode, 2)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)
        self.path.write_text('{"invalid":true}', encoding="utf-8")
        invalid_original = self.path.read_bytes()
        completed = self.cli("import-task", "--input", self.path, "--output", self.path)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(self.path.read_bytes(), invalid_original)

    def test_grade_task_cli_to_import_cli_binds_real_artifact_check(self):
        # The actual static grader runs; the task execution/ledger remain synthetic.
        case_root = ROOT / "tests/fixtures/skill_execution_tasks/targeted-document-edit"
        shutil.copytree(case_root / "initial", self.root / "work")
        artifact = self.root / "work/docs/ADR-021.md"
        original = artifact.read_text(encoding="utf-8")
        artifact.write_text(original.replace("Retry timeout: 250 ms.", "Retry timeout: 500 ms.", 1), encoding="utf-8")
        task_id = "targeted-document-edit"
        self.data["run"]["task_id"] = task_id
        acceptance_path = self.root / "graded.json"
        args = ("grade-task", "--case", case_root / "case.json", "--workspace", self.root,
                "--output", acceptance_path, "--run-id", self.data["run"]["run_id"],
                "--executor-id", "synthetic-executor", "--grader-id", "synthetic-independent-grader", "--summary-json")
        completed = self.cli(*args)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        acceptance = json.loads(completed.stdout)
        self.assertEqual(acceptance["status"], "passed")
        self.assertEqual(acceptance, json.loads(acceptance_path.read_text()))
        self.data["artifacts"] = acceptance["artifacts"]
        self.data["acceptance"] = {"path": acceptance_path.name, "sha256": sha256_bytes(acceptance_path.read_bytes())}
        write_json(self.path, self.data)
        completed = self.cli("import-task", "--input", self.path, "--summary-json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        imported = json.loads(completed.stdout)
        self.assertEqual(imported["acceptance_status"], "passed")
        self.assertEqual(imported["run_evidence"]["trace_summary"]["task_id"], task_id)
        self.assertEqual(imported["provenance"], "synthetic-fixture")
        # An unrelated edit must fail the independently running grader.
        artifact.write_text(original.replace("250 mA", "500 mA"), encoding="utf-8")
        completed = self.cli(*args)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "failed")
        self.assertEqual(self.cli("grade-task", "--case", case_root / "case.json", "--workspace", self.root,
                                 "--output", acceptance_path, "--run-id", "invalid", "--executor-id", "same",
                                 "--grader-id", "same").returncode, 2)

    def test_imports_feed_unchanged_comparator_and_real_compare_cli(self):
        synthetic_trials = document()
        for trial_index, trial in enumerate(synthetic_trials["trials"]):
            for side in ("baseline", "candidate"):
                for task_index, binding in enumerate(trial[side]):
                    path = self.root.parent / f"{side}-{task_index}-{trial_index}"
                    synthetic_package(path, side=side, task=task_index, trial=trial_index)
                    imported = import_task_evidence(path / "observation.json", MANIFEST)
                    self.assertEqual(imported["provenance"], "synthetic-fixture")
                    binding["run"] = imported["run_evidence"]
        rebind(synthetic_trials)
        value = compare_effect_trials(synthetic_trials, MANIFEST)
        self.assertEqual(value["verdict"], "improved")  # Synthetic arithmetic, not an E2-E4 claim.
        self.assertEqual(value["metrics"]["latency-per-task-ms"]["benefit_interval"], [30, 30])
        self.assertFalse(value["release_authorized"])
        self.assertFalse(value["quality_evidence_eligible"])
        self.assertEqual(value["evidence_scope"], "test-only")
        trial_path = self.root.parent / "synthetic-trials.json"
        write_json(trial_path, synthetic_trials)
        completed = self.cli("compare-trials", "--input", trial_path, "--summary-json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["run_count"], 36)
        # Missing observed usage must remain inconclusive when it is the primary metric.
        synthetic_trials["trials"][0]["candidate"][0]["run"] = self._unavailable_cost_run()
        synthetic_trials["plan"]["policy"]["primary_metric"] = "cost-per-task"
        rebind(synthetic_trials)
        self.assertEqual(compare_effect_trials(synthetic_trials, MANIFEST)["verdict"], "inconclusive")

    def _unavailable_cost_run(self):
        self.events["events"][3]["cost"] = None
        return self.import_data()["run_evidence"]


if __name__ == "__main__":
    unittest.main()
