from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import hashlib
import io

from agent_dev_kit.goal_plan import check, load, main, render


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "skills/adk-goal-authoring/references/goal-plan.json"


class GoalPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(EXAMPLE.read_text())

    def test_public_adk_cli_runs_from_another_project(self):
        with tempfile.TemporaryDirectory() as temp:
            environment = dict(os.environ, ADK_PYTHON_BIN=os.sys.executable)
            result = subprocess.run(["bash", str(ROOT / "scripts/devkit.sh"), "goal", "plan-check",
                                     "--plan", str(EXAMPLE)], cwd=temp, env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            self.assertEqual("adk.goal-plan-check/v1", json.loads(result.stdout)["schema_version"])
            self.assertFalse(json.loads(result.stdout)["runtime_authority"])

    def test_core_profile_contains_authoring_skill(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertIn("adk-goal-authoring", manifest["profiles"]["core"]["include_skills"])

    def test_valid_contract_does_not_grant_runtime_or_completion(self):
        result = check(self.plan)
        self.assertEqual("pass", result["status"])
        for key in ("runtime_authority", "completion_allowed", "evidence_contents_verified"):
            self.assertFalse(result[key])
        text = render(self.plan)
        self.assertIn("未设置原生预算", text)
        self.assertIn("原目标全部验收保留", text)
        self.assertIn("非关闭批次4次", text)
        self.assertIn("范围：", text)

    def test_original_denominator_unknown_parent_and_duplicate_ids_are_rejected(self):
        for mutation, expected in (
            (lambda p: p["parent_criteria"].append("AC-lost"), "original-criteria-unmapped"),
            (lambda p: p["deliverables"][0]["parents"].append("AC-unknown"), "parent-reference-invalid"),
            (lambda p: p["deliverables"].append(copy.deepcopy(p["deliverables"][0])), "deliverable-id-invalid"),
        ):
            plan = copy.deepcopy(self.plan)
            mutation(plan)
            self.assertIn(expected, check(plan)["reasons"])

    def test_dependencies_and_fake_closure_fail(self):
        self.plan["deliverables"][0]["depends_on"] = ["D-board"]
        self.assertIn("dependency-cycle-or-unresolved", check(self.plan)["reasons"])
        self.plan["deliverables"][0]["depends_on"] = ["missing"]
        self.assertIn("unknown-dependency", check(self.plan)["reasons"])
        self.plan["deliverables"][0]["status"] = "closed"
        self.assertIn("closed-without-evidence", check(self.plan)["reasons"])

    def test_budget_authority_and_empty_exit_cannot_pass(self):
        for value in (True, 0, -1, "100"):
            self.plan["budget_proposal"]["tokens"] = value
            self.assertIn("budget-proposal-invalid-or-claims-authority", check(self.plan)["reasons"])
        self.plan["budget_proposal"]["tokens"] = 100
        self.plan["budget_proposal"]["native_goal_applied"] = True
        self.plan["batch"]["done_when"] = ""
        self.plan["batch"]["replan_effect"] = ""
        self.plan["batch"]["stop"]["same_failure_limit"] = True
        result = check(self.plan)
        for key in ("budget-proposal-invalid-or-claims-authority", "batch-exit-or-scope-missing", "replan-effect-missing", "stop-condition-invalid"):
            self.assertIn(key, result["reasons"])

    def test_ready_cannot_bypass_open_dependency_or_select_blocked_item(self):
        self.plan["deliverables"][0]["depends_on"] = ["D-board"]
        self.assertIn("ready-or-closed-with-open-dependency", check(self.plan)["reasons"])
        self.plan["batch"]["deliverables"] = ["D-board"]
        self.assertIn("batch-selected-unavailable-deliverable", check(self.plan)["reasons"])

    def test_selected_open_deliverable_cannot_bypass_dependency(self):
        self.plan["deliverables"][0]["status"] = "open"
        self.plan["deliverables"][0]["depends_on"] = ["D-board"]
        self.plan["deliverables"][1]["depends_on"] = []
        self.assertIn("batch-selected-with-open-dependency", check(self.plan)["reasons"])

    def test_current_state_work_in_progress_uses_shared_validation(self):
        from agent_dev_kit.planning_state import check_current_state
        state = {"schema_version": "adk.current-state/v1", "goal_ref": "goal.json",
                 "milestone": "error path", "evidence_refs": [], "blockers": [],
                 "next_actions": ["verify"], "history_refs": [],
                 "work_in_progress": {"status": "OPEN", "prior_verified_checkpoint": 220}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "current.json"
            for work in (state["work_in_progress"], {}, {"status": []},
                         {"prior_verified_checkpoint": True}, {"unknown": "x"}):
                state["work_in_progress"] = work
                path.write_text(json.dumps(state))
                expected = "pass" if work.get("status") == "OPEN" else "fail"
                self.assertEqual(expected, check_current_state(path)["status"])
                self.assertEqual(expected, check(self.plan, state)["status"])

    def test_strict_input_boundaries_and_digest_bind_same_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            for raw in ('{"x":' + '[' * 1100 + '0' + ']' * 1100 + '}',
                        '{"x":NaN}', '{"x":1e10000}', '{"x":"\\ud800"}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    load(path, 65536)
            raw = json.dumps(self.plan).encode()
            path.write_bytes(raw)
            output = io.StringIO()
            with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded second read")):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(0, main(["check", "--plan", str(path)]))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), json.loads(output.getvalue())["plan_sha256"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX input boundary")
    def test_fifo_and_symlink_inputs_fail_without_hanging(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "plan.json"
            source.write_text(json.dumps(self.plan))
            alias = root / "alias"
            alias.symlink_to(source)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            parent = root / "parent"
            parent.symlink_to(root, target_is_directory=True)
            for unsafe in (alias, fifo, parent / source.name, root):
                with self.assertRaises(ValueError):
                    load(unsafe, 65536)

    def test_current_frontier_is_bounded_and_does_not_load_history(self):
        state = {"schema_version": "adk.current-state/v1", "goal_ref": "goal.json",
                 "milestone": "error path", "evidence_refs": ["evidence.json"],
                 "blockers": [], "next_actions": ["run exact failing consumer"],
                 "history_refs": ["history-index.md"]}
        self.assertEqual("pass", check(self.plan, state)["status"])
        self.assertIn("run exact failing consumer", render(self.plan, state))
        state["evidence_refs"] = [str(i) for i in range(9)]
        self.assertIn("state-evidence_refs-invalid", check(self.plan, state)["reasons"])

    def test_untrusted_json_types_are_diagnostics(self):
        for field in ("constraints", "parent_criteria", "deliverables", "batch", "budget_proposal"):
            plan = copy.deepcopy(self.plan)
            plan[field] = None
            self.assertEqual("fail", check(plan)["status"])

    def test_load_limits_duplicate_keys_and_cli_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            for raw in ('{"x":1,"x":2}', '[]', 'invalid'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    load(path, 100)
            path.write_text(json.dumps(self.plan))
            with self.assertRaises(ValueError):
                load(path, 10)
            before = path.read_bytes()
            self.assertEqual(0, main(["check", "--plan", str(path)]))
            self.assertEqual(1, main(["resume", "--plan", str(path)]))
            self.assertEqual(before, path.read_bytes())



if __name__ == "__main__":
    unittest.main()
