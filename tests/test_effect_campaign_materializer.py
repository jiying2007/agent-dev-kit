from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit import campaign_model
from agent_dev_kit.effect_campaign_materializer import materialize_effect_campaign
from agent_dev_kit.model import Manifest, ManifestError


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
MODEL = "claude-haiku-4-5-20251001"
RUNTIME_VERSION = "2.1.278 (Claude Code)"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def task(task_id: str, category: str, skill: str) -> dict[str, object]:
    return {
        "id": task_id,
        "category": category,
        "prompt": "fixture prompt " + task_id,
        "expected_skill": skill,
        "expected_safe": True,
    }


def contract(tasks_rel: str) -> dict[str, object]:
    return {
        "schema": campaign_model.CONTRACT_SCHEMA,
        "campaign_id": "effect-materializer-fixture",
        "tasks": tasks_rel,
        "runtimes": ["claude"],
        "runtime_models": {"claude": MODEL},
        "conditions": ["baseline", "adk"],
        "trials": 2,
        "minimum_tasks": 2,
        "max_claude_call_usd": 0.01,
        "max_budget_usd": 1.0,
        "retry_limit": 0,
        "thresholds": {
            "candidate_success_rate": 0.0,
            "candidate_route_accuracy": 0.0,
            "candidate_safety_accuracy": 0.0,
            "minimum_success_delta": 0.0,
            "latency_ratio_max": 10.0,
            "usage_ratio_max": 10.0,
            "required_non_regression_trials": 1,
        },
    }


def effect_plan() -> dict[str, object]:
    return {
        "campaign_id": "effect-materializer-fixture",
        "registered_at": "2020-01-01T00:00:00Z",
        "window": {
            "from": "2020-01-01T01:00:00Z",
            "through": "2020-01-01T02:00:00Z",
            "as_of": "2020-01-01T03:00:00Z",
        },
        "task_ids": ["task-a", "task-b"],
        "trial_ids": ["trial-1", "trial-2"],
        "bundles": {"baseline": "a" * 64, "candidate": "b" * 64},
        "controls": {
            "runtime_target": "claude",
            "runtime_version": "2.1.278",
            "model_version": MODEL,
            "prompt_version": "adk-runtime-routing-v1",
            "orchestration_mode": "single-agent",
            "environment_ref": "ref:" + "1" * 64,
            "tool_policy_ref": "ref:" + "2" * 64,
            "grader_ref": "ref:" + "3" * 64,
            "dataset_ref": "ref:" + "4" * 64,
            "parameters_ref": "ref:" + "5" * 64,
            "provider_ref": "ref:" + "6" * 64,
            "model_identity": "revision-bound",
        },
        "policy": {
            "primary_metric": "latency-per-task-ms",
            "minimum_effect": 5,
            "noninferiority_margin": 0,
            "guardrails": {"task-success-rate": 0, "wrong-skill-rate": 0},
            "minimum_tasks": 2,
            "minimum_trials": 2,
            "bootstrap_samples": 100,
            "bootstrap_seed": 42,
            "confidence": 0.95,
        },
    }


class EffectCampaignMaterializerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tasks_path = self.root / "tasks.jsonl"
        self.tasks = [
            task("task-a", "routing", "adk-runtime-router"),
            task("task-b", "requirements", "adk-requirements-triage"),
        ]
        self.tasks_path.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in self.tasks),
            encoding="utf-8",
        )
        rel = self.tasks_path.relative_to(self.root).as_posix()
        self.contract_path = self.root / "contract.json"
        self.contract = contract(rel)
        write_json(self.contract_path, self.contract)
        self.effect_plan_path = self.root / "effect-plan.json"
        write_json(self.effect_plan_path, effect_plan())
        self.state = self.root / "state"
        self._write_state()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_state(self) -> None:
        tasks_sha = campaign_model.sha256_file(self.tasks_path) if hasattr(campaign_model, "sha256_file") else None
        if tasks_sha is None:
            import hashlib
            tasks_sha = hashlib.sha256(self.tasks_path.read_bytes()).hexdigest()
        plan = {
            "schema": campaign_model.PLAN_SCHEMA,
            "status": "ready",
            "campaign_id": self.contract["campaign_id"],
            "manifest_version": MANIFEST.version,
            "manifest_sha256": MANIFEST.digest,
            "contract_sha256": campaign_model._digest(self.contract),
            "tasks": self.tasks_path.relative_to(self.root).as_posix(),
            "tasks_sha256": tasks_sha,
            "task_count": len(self.tasks),
            "runtimes": [{
                "runtime": "claude",
                "status": "planned",
                "runtime_version": RUNTIME_VERSION,
                "condition": "adk",
                "tasks": len(self.tasks),
                "executable_name": "claude",
                "permissions": "read-only/no-tools",
                "reason": None,
                "requested_model": MODEL,
            }],
            "conditions": ["baseline", "adk"],
            "trials": 2,
            "primary_claude_calls": 8,
            "primary_worst_cost_usd": 0.08,
            "maximum_claude_calls": 8,
            "maximum_worst_cost_usd": 0.08,
            "max_claude_call_usd": 0.01,
            "max_budget_usd": 1.0,
            "permissions": "read-only/no-tools",
            "failures": [],
        }
        plan["plan_sha256"] = campaign_model._digest(plan)
        write_json(self.state / "campaign-plan.json", plan)

        minute = 10
        for trial in (1, 2):
            for condition in ("baseline", "adk"):
                for item in self.tasks:
                    expected_route = item["category"] if condition == "baseline" else item["expected_skill"]
                    elapsed = 100 if condition == "baseline" else 50
                    attempt = {
                        "attempt": 1,
                        "runtime_version": RUNTIME_VERSION,
                        "requested_model": MODEL,
                        "reported_models": [MODEL],
                        "status": "pass",
                        "actual_skill": expected_route,
                        "actual_safe": True,
                        "route_ok": True,
                        "safe_ok": True,
                        "elapsed_ms": elapsed,
                        "usage": {
                            "input_tokens": 20,
                            "cached_input_tokens": 0,
                            "output_tokens": 5,
                            "total_tokens": 25,
                        },
                        "cost_usd": 0.001,
                        "cost_evidence": "runtime-reported",
                        "error": None,
                    }
                    record = {
                        "schema": campaign_model.RESULT_SCHEMA,
                        "campaign_id": self.contract["campaign_id"],
                        "manifest_version": MANIFEST.version,
                        "manifest_sha256": MANIFEST.digest,
                        "plan_sha256": plan["plan_sha256"],
                        "contract_sha256": plan["contract_sha256"],
                        "tasks_sha256": plan["tasks_sha256"],
                        "runtime": "claude",
                        "runtime_version": RUNTIME_VERSION,
                        "requested_model": MODEL,
                        "condition": condition,
                        "trial": trial,
                        "task_id": item["id"],
                        "task_sha256": campaign_model._digest(item),
                        "expected_route": expected_route,
                        "expected_safe": True,
                        "recorded_at": f"2020-01-01T01:{minute:02d}:00Z",
                        "attempts": [attempt],
                        "final": attempt,
                    }
                    record["record_sha256"] = campaign_model._digest(record)
                    path = campaign_model._result_path(
                        self.state, "claude", condition, trial, str(item["id"])
                    )
                    write_json(path, record)
                    minute += 1

    def test_materializes_single_runtime_state_to_trace_only_effect_trials(self) -> None:
        value = materialize_effect_campaign(
            MANIFEST, self.contract_path, self.state, self.effect_plan_path, "claude",
                campaign_root=self.root
        )
        self.assertEqual("adk-effect-trials/v1", value["schema_version"])
        self.assertEqual(2, len(value["trials"]))
        for trial in value["trials"]:
            self.assertEqual("ok", trial["infrastructure_status"])
            self.assertEqual(2, len(trial["baseline"]))
            self.assertEqual(2, len(trial["candidate"]))
            for side in ("baseline", "candidate"):
                for binding in trial[side]:
                    run = binding["run"]
                    self.assertEqual([], run["receipts"])
                    self.assertIsNone(run["measurement"])
                    self.assertEqual("claude", run["trace_summary"]["runtime_target"])
                    self.assertEqual("2.1.278", run["trace_summary"]["runtime_version"])
                    self.assertEqual(MODEL, run["trace_summary"]["model_version"])
                    expected_bundle = "a" * 64 if side == "baseline" else "b" * 64
                    self.assertEqual(expected_bundle, run["trace_summary"]["asset_bundle_sha256"])

    def test_external_campaign_root_is_bounded_and_cli_visible(self) -> None:
        loaded, tasks_path, tasks = campaign_model.load_campaign_contract(
            MANIFEST, self.contract_path, self.root
        )
        self.assertEqual(self.contract["campaign_id"], loaded["campaign_id"])
        self.assertEqual(self.tasks_path.resolve(), tasks_path.resolve())
        self.assertEqual(2, len(tasks))

        bad = dict(self.contract)
        bad["tasks"] = "../escape.jsonl"
        bad_path = self.root / "bad-contract.json"
        write_json(bad_path, bad)
        with self.assertRaises(ManifestError):
            campaign_model.load_campaign_contract(MANIFEST, bad_path, self.root)

        help_run = subprocess.run(
            [sys.executable, "-m", "agent_dev_kit.cli", "eval", "campaign", "materialize-effect", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertEqual(0, help_run.returncode, (help_run.stdout, help_run.stderr))
        self.assertIn("--campaign-root", help_run.stdout)

    def test_tamper_alias_missing_result_and_window_drift_fail_closed(self) -> None:
        path = campaign_model._result_path(self.state, "claude", "baseline", 1, "task-a")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["final"]["elapsed_ms"] = 999
        write_json(path, record)
        with self.assertRaisesRegex(ManifestError, "digest"):
            materialize_effect_campaign(
                MANIFEST, self.contract_path, self.state, self.effect_plan_path, "claude",
                campaign_root=self.root
            )

        self._write_state()
        plan = effect_plan()
        plan["controls"]["model_identity"] = "alias-unverified"
        write_json(self.effect_plan_path, plan)
        with self.assertRaisesRegex(ManifestError, "revision-bound"):
            materialize_effect_campaign(
                MANIFEST, self.contract_path, self.state, self.effect_plan_path, "claude",
                campaign_root=self.root
            )

        write_json(self.effect_plan_path, effect_plan())
        missing = campaign_model._result_path(self.state, "claude", "adk", 2, "task-b")
        missing.unlink()
        with self.assertRaisesRegex(ManifestError, "missing"):
            materialize_effect_campaign(
                MANIFEST, self.contract_path, self.state, self.effect_plan_path, "claude",
                campaign_root=self.root
            )

        self._write_state()
        plan = effect_plan()
        plan["window"]["through"] = "2020-01-01T01:05:00Z"
        write_json(self.effect_plan_path, plan)
        with self.assertRaisesRegex(ManifestError, "outside"):
            materialize_effect_campaign(
                MANIFEST, self.contract_path, self.state, self.effect_plan_path, "claude",
                campaign_root=self.root
            )


if __name__ == "__main__":
    unittest.main()
