"""Runtime comparison identity and per-case regression tests without model calls."""

from __future__ import annotations

import copy
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit import evaluation, evaluation_cli, evaluation_runtime
from agent_dev_kit.model import Manifest, ManifestError

ROOT = Path(__file__).resolve().parents[1]
TASKS = [
    {
        "id": "case-{:02d}".format(index),
        "category": "test",
        "prompt": "route this case {}".format(index),
        "expected_skill": "adk-test-strategy",
        "expected_safe": True,
    }
    for index in range(10)
]


def report(condition: str, failed: set[int]) -> dict:
    results = []
    for index, task in enumerate(TASKS):
        expected_route = task["category"] if condition == "baseline" else task["expected_skill"]
        route_ok = index not in failed
        results.append({
            "id": task["id"],
            "prompt_sha256": evaluation_runtime._prompt_digest(task["prompt"]),
            "category": task["category"],
            "expected_skill": task["expected_skill"],
            "expected_route": expected_route,
            "actual_skill": expected_route if route_ok else "wrong-route",
            "route_ok": route_ok,
            "expected_safe": True,
            "actual_safe": True,
            "safe_ok": True,
            "requested_model": "test-model",
            "reported_models": ["test-model"],
            "error": None,
            "status": "pass" if route_ok else "fail",
            "elapsed_ms": 1.0,
        })
    success = round((10 - len(failed)) / 10, 4)
    gate = {
        "success_rate": success >= evaluation_runtime.RUNTIME_THRESHOLDS["success_rate"],
        "route_accuracy": success >= evaluation_runtime.RUNTIME_THRESHOLDS["route_accuracy"],
        "safety_accuracy": True,
        "runtime_errors": True,
    }
    return {
        "schema_version": 1,
        "suite": "runtime-routing",
        "runtime": "claude",
        "runtime_version": "test-runtime 1",
        "requested_model": "test-model",
        "reported_models": ["test-model"],
        "condition": condition,
        "manifest_sha256": "a" * 64 if condition == "baseline" else "b" * 64,
        "task_set_sha256": evaluation_runtime._task_set_sha256(TASKS),
        "task_set_identity_scope": evaluation_runtime.EVAL_TASK_IDENTITY_SCOPE,
        "task_snapshot_frozen": True,
        "grader_contract": evaluation_runtime.RUNTIME_GRADER_CONTRACT,
        "prompt_version": evaluation.RUNTIME_ROUTING_PROMPT_VERSION,
        "source_snapshot_atomic": False,
        "status": "pass" if all(gate.values()) else "fail",
        "total": 10,
        "passed": 10 - len(failed),
        "success_rate": success,
        "route_accuracy": success,
        "safety_accuracy": 1.0,
        "thresholds": dict(evaluation_runtime.RUNTIME_THRESHOLDS),
        "quality_gate": gate,
        "results": results,
    }


class RuntimeComparisonContractTests(unittest.TestCase):
    def test_direct_runtime_cli_requires_count_and_cost_acknowledgment(self) -> None:
        common = ["run", "--suite", "runtime", "--limit", "1", "--execute", "--model", "test-model"]
        for arguments in (
            common + ["--runtime", "claude"],
            common + ["--runtime", "claude", "--max-new-results", "1", "--approve-budget-usd", "0.10"],
            common + ["--runtime", "codex", "--max-new-results", "1"],
        ):
            with self.subTest(arguments=arguments):
                with patch.object(evaluation_cli, "run_runtime") as execute:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            evaluation_cli.main(arguments)
                execute.assert_not_called()

    def test_provider_prompts_stay_out_of_command_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            def codex_call(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                self.assertNotIn("SENTINEL_SECRET", repr(command))
                self.assertIn("SENTINEL_SECRET", str(kwargs["input"]))
                (workspace / "codex-result.json").write_text(
                    json.dumps({"primary_skill": "test", "safe_to_execute": True, "reason": "ok"}),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            with patch.object(evaluation.shutil, "which", return_value="/fixture/codex"):
                with patch.object(evaluation.subprocess, "run", side_effect=codex_call):
                    evaluation._run_codex(workspace, "system", "SENTINEL_SECRET", workspace / "schema.json")

            def claude_call(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                self.assertNotIn("SENTINEL_SECRET", repr(command))
                self.assertEqual(kwargs["input"], "SENTINEL_SECRET")
                self.assertIn("--system-prompt-file", command)
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps({
                    "structured_output": {"primary_skill": "test", "safe_to_execute": True, "reason": "ok"},
                    "total_cost_usd": 0.01,
                }), stderr="")
            with patch.object(evaluation.shutil, "which", return_value="/fixture/claude"):
                with patch.object(evaluation.subprocess, "run", side_effect=claude_call):
                    evaluation._run_claude(workspace, "system", "SENTINEL_SECRET")

    def test_provider_failure_does_not_echo_cli_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            for runtime, runner in (("codex", evaluation._run_codex), ("claude", evaluation._run_claude)):
                with self.subTest(runtime=runtime):
                    failed = subprocess.CompletedProcess([runtime], 1, stdout="SENTINEL_SECRET", stderr="SENTINEL_SECRET")
                    with patch.object(evaluation.shutil, "which", return_value="/fixture/" + runtime):
                        with patch.object(evaluation.subprocess, "run", return_value=failed):
                            with self.assertRaises(ManifestError) as caught:
                                if runtime == "codex":
                                    runner(workspace, "system", "prompt", workspace / "schema.json")
                                else:
                                    runner(workspace, "system", "prompt")
                    self.assertNotIn("SENTINEL_SECRET", str(caught.exception))

    def test_same_inputs_and_no_case_regression_can_pass(self) -> None:
        result = evaluation_runtime.compare_runtime_reports(
            report("baseline", {0, 1}), report("adk", set())
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["improved_case_ids"], ["case-00", "case-01"])
        self.assertEqual(result["regressed_case_ids"], [])
        self.assertEqual(result["task_set_sha256"], evaluation_runtime._task_set_sha256(TASKS))
        self.assertFalse(result["input_identity_authenticated"])
        self.assertFalse(result["release_authorized"])

    def test_aggregate_gain_cannot_hide_case_regression(self) -> None:
        result = evaluation_runtime.compare_runtime_reports(
            report("baseline", {0, 1}), report("adk", {2})
        )
        self.assertTrue(result["no_regression"])
        self.assertTrue(result["measurable_gain"])
        self.assertTrue(result["candidate_quality_gate"])
        self.assertEqual(result["regressed_case_ids"], ["case-02"])
        self.assertEqual(result["status"], "fail")

    def test_dataset_prompt_and_labels_must_match(self) -> None:
        baseline = report("baseline", {0, 1})
        for field, value in (
            ("task_set_sha256", "c" * 64),
            ("grader_contract", "other-grader/v1"),
            ("requested_model", "other-model"),
            ("runtime_version", "other-runtime"),
            ("reported_models", ["other-model"]),
            ("runtime", "unknown-runtime"),
        ):
            candidate = report("adk", set())
            candidate[field] = value
            with self.subTest(field=field), self.assertRaises(ManifestError):
                evaluation_runtime.compare_runtime_reports(baseline, candidate)

        for field, value in (
            ("prompt_sha256", "d" * 64),
            ("category", "other"),
            ("expected_skill", "other-skill"),
            ("requested_model", "other-model"),
            ("reported_models", ["other-model"]),
        ):
            candidate = report("adk", set())
            candidate["results"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ManifestError):
                evaluation_runtime.compare_runtime_reports(baseline, candidate)

    def test_per_case_model_swap_with_same_union_is_rejected(self) -> None:
        baseline = report("baseline", {0, 1})
        candidate = report("adk", set())
        for value in (baseline, candidate):
            value["results"][1]["reported_models"] = ["other-model"]
            value["reported_models"] = ["other-model", "test-model"]
        candidate["results"][0]["reported_models"] = ["other-model"]
        candidate["results"][1]["reported_models"] = ["test-model"]
        with self.assertRaises(ManifestError):
            evaluation_runtime.compare_runtime_reports(baseline, candidate)

    def test_missing_case_model_cannot_pass_comparison(self) -> None:
        baseline = report("baseline", {0, 1})
        candidate = report("adk", set())
        for value in (baseline, candidate):
            value["results"][0]["reported_models"] = []
        with self.assertRaises(ManifestError):
            evaluation_runtime.compare_runtime_reports(baseline, candidate)

    def test_legacy_and_forged_reports_fail_closed(self) -> None:
        baseline = report("baseline", {0, 1})
        candidate = report("adk", set())
        del candidate["task_set_sha256"]
        with self.assertRaises(ManifestError):
            evaluation_runtime.compare_runtime_reports(baseline, candidate)

        candidate = report("adk", set())
        candidate["results"][0]["actual_skill"] = "wrong-route"
        with self.assertRaises(ManifestError):
            evaluation_runtime.compare_runtime_reports(baseline, candidate)

        for field, value in (("success_rate", True), ("quality_gate", {"success_rate": 1})):
            candidate = report("adk", set())
            candidate[field] = value
            with self.subTest(field=field), self.assertRaises(ManifestError):
                evaluation_runtime.compare_runtime_reports(baseline, candidate)

    def test_runtime_report_emits_bound_identity_without_provider(self) -> None:
        manifest = Manifest.load(ROOT)
        task = TASKS[0]
        mutable_task = copy.deepcopy(task)
        fake_outcome = {
            "value": {"primary_skill": task["expected_skill"], "safe_to_execute": True, "reason": "test"},
            "elapsed_ms": 1.0,
            "usage": {},
            "cost_usd": None,
            "requested_model": "test-model",
            "reported_models": ["test-model"],
        }
        def mutate_source(*args: object, **kwargs: object) -> dict:
            self.assertEqual(args[2], task["prompt"])
            mutable_task["prompt"] = "changed during model call"
            return fake_outcome

        with patch.object(evaluation, "_run_claude", side_effect=mutate_source) as model_call:
            with patch.object(evaluation_runtime, "runtime_version", return_value="test-runtime 1"):
                result = evaluation.run_runtime(
                    manifest, [mutable_task], "claude", "adk", model="test-model"
                )
        model_call.assert_called_once()
        self.assertEqual(result["task_set_sha256"], evaluation_runtime._task_set_sha256([task]))
        self.assertEqual(result["results"][0]["prompt_sha256"], evaluation_runtime._prompt_digest(task["prompt"]))
        self.assertEqual(result["grader_contract"], evaluation_runtime.RUNTIME_GRADER_CONTRACT)
        self.assertFalse(result["source_snapshot_atomic"])
        self.assertTrue(result["task_snapshot_frozen"])
        markdown = evaluation.eval_markdown(result)
        self.assertIn("- grader_contract: adk-runtime-routing-grader/v1", markdown)
        self.assertIn("- requested_model: test-model", markdown)

    def test_deterministic_report_uses_pre_execution_task_snapshot(self) -> None:
        manifest = Manifest.load(ROOT)
        task = TASKS[0]
        mutable_task = copy.deepcopy(task)

        def mutate_source(*args: object, **kwargs: object) -> dict:
            self.assertEqual(args[1], task["prompt"])
            mutable_task["prompt"] = "changed during matcher call"
            return {"match": True, "skill": task["expected_skill"]}

        with patch.object(evaluation_runtime, "match_text", side_effect=mutate_source):
            result = evaluation_runtime.run_deterministic(manifest, [mutable_task])
        self.assertEqual(result["task_set_sha256"], evaluation_runtime._task_set_sha256([task]))
        self.assertTrue(result["task_snapshot_frozen"])

    def test_direct_runtime_rejects_duplicate_ids_before_model_call(self) -> None:
        manifest = Manifest.load(ROOT)
        with patch.object(evaluation, "_run_claude") as model_call:
            with self.assertRaises(ManifestError):
                evaluation.run_runtime(manifest, [TASKS[0], copy.deepcopy(TASKS[0])], "claude", "adk")
        model_call.assert_not_called()

        oversized = copy.deepcopy(TASKS[0])
        oversized["prompt"] = "x" * evaluation_runtime.MAX_EVAL_TASK_BYTES
        with patch.object(evaluation, "_run_claude") as model_call:
            with self.assertRaises(ManifestError):
                evaluation.run_runtime(manifest, [oversized], "claude", "adk")
        model_call.assert_not_called()

    def test_malformed_provider_result_fails_without_leaking_error(self) -> None:
        manifest = Manifest.load(ROOT)
        task = dict(TASKS[0], expected_safe=False)
        for value in (
            {"primary_skill": task["expected_skill"], "reason": "missing safety"},
            {"primary_skill": task["expected_skill"], "safe_to_execute": "false", "reason": "wrong type"},
        ):
            outcome = {"value": value, "elapsed_ms": 1.0, "usage": {}, "cost_usd": None,
                       "requested_model": "test-model", "reported_models": ["test-model"]}
            with patch.object(evaluation, "_run_claude", return_value=outcome):
                with patch.object(evaluation_runtime, "runtime_version", return_value="test-runtime 1"):
                    report_value = evaluation.run_runtime(manifest, [task], "claude", "adk", model="test-model")
            self.assertEqual(report_value["status"], "fail")
            self.assertFalse(report_value["results"][0]["safe_ok"])
            self.assertEqual(report_value["results"][0]["error"], "runtime-evaluation-error")
        with patch.object(evaluation, "_run_claude", side_effect=ManifestError("SENTINEL_SECRET")):
            with patch.object(evaluation_runtime, "runtime_version", return_value="test-runtime 1"):
                report_value = evaluation.run_runtime(manifest, [task], "claude", "adk", model="test-model")
        self.assertNotIn("SENTINEL_SECRET", json.dumps(report_value))

    def test_invalid_runtime_json_error_omits_model_content(self) -> None:
        with self.assertRaises(ManifestError) as caught:
            evaluation_runtime._extract_json_text("SENTINEL_SECRET")
        self.assertNotIn("SENTINEL_SECRET", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
