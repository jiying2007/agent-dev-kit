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

    def _resume_state(self):
        return {
            "schema_version": "adk.current-state/v1",
            "goal_ref": "requirements.md#original-acceptance",
            "milestone": "software verified; board awaiting authorization",
            "evidence_refs": ["receipts/not-loaded.json"],
            "blockers": ["UNKNOWN external effect; reconcile before retry"],
            "next_actions": ["touch NEXT_ACTION_MUST_NOT_RUN"],
            "history_refs": ["history/not-loaded.md"],
            "work_in_progress": {
                "ref": "current-batch.md", "status": "BLOCKED",
                "prior_verified_checkpoint": 220, "replan": "keep original batch",
                "qualification": "board evidence unavailable",
            },
        }

    def _public_goal(self, action, plan, state):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path, state_path = root / "goal.json", root / "current.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            environment = dict(os.environ, ADK_PYTHON_BIN=os.sys.executable,
                               PYTHONDONTWRITEBYTECODE="1")
            arguments = ["--state", str(state_path)]
            if action != "state-check":
                arguments += ["--plan", str(plan_path)]
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/devkit.sh"), "goal", action,
                 *arguments],
                cwd=root, env=environment, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(before, {path.name: path.read_bytes() for path in root.iterdir()})
            return result

    def test_public_resume_preserves_state_and_never_executes_recorded_actions(self):
        state = self._resume_state()
        self.plan["deliverables"][0]["verify"] = ["touch VERIFY_MUST_NOT_RUN"]
        result = self._public_goal("resume", self.plan, state)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        for value in (state["goal_ref"], state["milestone"], *state["blockers"],
                      *state["evidence_refs"], *state["next_actions"], *state["history_refs"]):
            self.assertIn(value, result.stdout)
        for value in state["work_in_progress"].values():
            self.assertIn(str(value), result.stdout)
        self.assertIn("D-error [ready]", result.stdout)
        self.assertIn("VERIFY_MUST_NOT_RUN", result.stdout)
        self.assertNotIn("Goal 草案", result.stdout)
        for flag in ("read_only=true", "runtime_authority=false", "completion_allowed=false",
                     "evidence_contents_verified=false"):
            self.assertIn(flag, result.stdout)

    def test_public_resume_can_show_closed_batch_without_reopening_or_approving_it(self):
        self.plan["deliverables"][0].update(status="closed", evidence=["receipts/closed.json"])
        result = self._public_goal("resume", self.plan, self._resume_state())
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn(self.plan["batch"]["id"], result.stdout)
        self.assertIn("D-error [closed]", result.stdout)
        self.assertIn("receipts/closed.json", result.stdout)
        self.assertIn("completion_allowed=false", result.stdout)
        for action in ("plan-check", "render"):
            strict = self._public_goal(action, self.plan, self._resume_state())
            self.assertEqual(1, strict.returncode, strict.stdout)
            verdict = json.loads(strict.stdout)
            self.assertIn("batch-selected-unavailable-deliverable", verdict["reasons"])
            self.assertFalse(verdict["runtime_authority"])
            self.assertFalse(verdict["completion_allowed"])

    def test_public_resume_can_show_blocked_batch_and_unclosed_dependency(self):
        self.plan["batch"]["deliverables"] = ["D-board"]
        result = self._public_goal("resume", self.plan, self._resume_state())
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn("D-board [blocked]", result.stdout)
        self.assertIn("D-error [ready]", result.stdout)
        self.assertIn(self.plan["batch"]["stop"]["external_trigger"], result.stdout)
        strict = self._public_goal("plan-check", self.plan, self._resume_state())
        self.assertEqual(1, strict.returncode, strict.stdout)
        self.assertIn("batch-selected-unavailable-deliverable", json.loads(strict.stdout)["reasons"])

    def test_public_resume_still_rejects_invalid_evidence_dependencies_and_state(self):
        cases = (
            (lambda p, s: p["deliverables"][0].update(status="closed"), "closed-without-evidence"),
            (lambda p, s: p["deliverables"][1].update(status="ready"), "ready-or-closed-with-open-dependency"),
            (lambda p, s: p["deliverables"][1].update(status="closed", evidence=["receipt"]),
             "ready-or-closed-with-open-dependency"),
            (lambda p, s: p["deliverables"][1].update(depends_on=["unknown"]), "unknown-dependency"),
            (lambda p, s: p["deliverables"][0].update(status="blocked", depends_on=["D-board"]),
             "dependency-cycle-or-unresolved"),
            (lambda p, s: p["deliverables"][1].update(status="invalid"), "deliverable-status-invalid"),
            (lambda p, s: p["batch"].update(deliverables=[]), "batch-selection-invalid"),
            (lambda p, s: p["batch"].update(deliverables=["unknown"]), "batch-selection-invalid"),
            (lambda p, s: p["parent_criteria"].append("AC-lost"), "original-criteria-unmapped"),
            (lambda p, s: s.update(work_in_progress={"unknown": "value"}), "current-state-work-in-progress-invalid"),
            (lambda p, s: s.update(next_actions=["a", "b", "c", "d"]), "state-next_actions-invalid"),
        )
        for mutate, reason in cases:
            with self.subTest(reason=reason):
                plan, state = copy.deepcopy(self.plan), self._resume_state()
                plan["batch"]["deliverables"] = ["D-board"]
                mutate(plan, state)
                result = self._public_goal("resume", plan, state)
                self.assertEqual(1, result.returncode, result.stdout)
                verdict = json.loads(result.stdout)
                self.assertIn(reason, verdict["reasons"])
                self.assertFalse(verdict["runtime_authority"])
                self.assertFalse(verdict["completion_allowed"])
        self.plan["deliverables"][1]["status"] = "open"
        self.plan["batch"]["deliverables"] = ["D-board"]
        result = self._public_goal("resume", self.plan, self._resume_state())
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("batch-selected-with-open-dependency", json.loads(result.stdout)["reasons"])

    def test_public_resume_fails_on_output_limit_without_truncating_blockers(self):
        state = self._resume_state()
        self.plan["objective"] = "original objective " + "x" * 5000
        state["blockers"] = ["must preserve entire blocker " + "y" * 4000]
        self.assertLess(len(json.dumps(self.plan, ensure_ascii=False).encode()), 65536)
        self.assertLess(len(json.dumps(state, ensure_ascii=False).encode()), 8192)
        result = self._public_goal("resume", self.plan, state)
        self.assertEqual(1, result.returncode, result.stdout)
        verdict = json.loads(result.stdout)
        self.assertEqual("fail", verdict["status"])
        self.assertTrue(verdict["read_only"])
        self.assertIn("rendered frontier exceeds byte limit", verdict["error"])

    def test_public_resume_keeps_input_byte_limits(self):
        for oversized in ("plan", "state"):
            with self.subTest(oversized=oversized):
                plan, state = copy.deepcopy(self.plan), self._resume_state()
                if oversized == "plan":
                    plan["objective"] = "x" * 65537
                else:
                    state["blockers"] = ["x" * 8193]
                result = self._public_goal("resume", plan, state)
                self.assertEqual(1, result.returncode, result.stdout)
                verdict = json.loads(result.stdout)
                self.assertEqual("fail", verdict["status"])
                self.assertTrue(verdict["read_only"])
                self.assertIn("JSON exceeds byte budget", verdict["error"])

    def test_example_does_not_propose_unmeasured_token_budget(self):
        self.assertIsNone(self.plan["budget_proposal"]["tokens"])

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

    def test_unknown_token_proposal_is_explicit_not_a_false_budget(self):
        plan = copy.deepcopy(self.plan)
        plan["budget_proposal"] = {
            "tokens": None,
            "basis": "缺少受信模型 usage；待真实计量后提交估计",
            "native_goal_applied": False,
        }
        verdict = check(plan)
        self.assertEqual(verdict["status"], "pass", verdict)
        output = render(plan)
        self.assertIn("预算提案：未知（待真实测量）", output)
        self.assertIn("未设置原生预算", output)
        for invalid in (0, -1, True, "100"):
            plan["budget_proposal"]["tokens"] = invalid
            self.assertIn("budget-proposal-invalid-or-claims-authority", check(plan)["reasons"])
        plan["budget_proposal"]["tokens"] = None
        plan["budget_proposal"]["native_goal_applied"] = True
        self.assertIn("budget-proposal-invalid-or-claims-authority", check(plan)["reasons"])

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

    def test_public_state_check_and_resume_agree_on_frontier_field_boundaries(self):
        for field, maximum in (("evidence_refs", 8), ("blockers", 8),
                               ("next_actions", 3), ("history_refs", 3)):
            cases = (
                ("upper-bound", [f"{field}-{i}" for i in range(maximum)], 0),
                ("too-many", [f"{field}-{i}" for i in range(maximum + 1)], 1),
                ("duplicates", ["same reference", "same reference"], 1),
                ("blank", [" \t"], 1),
                ("wrong-type", [None], 1),
                ("empty", [], int(field == "next_actions")),
            )
            for label, values, expected in cases:
                state = self._resume_state()
                state[field] = values
                for action in ("state-check", "resume"):
                    with self.subTest(field=field, case=label, action=action):
                        result = self._public_goal(action, self.plan, state)
                        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
                        if expected:
                            verdict = json.loads(result.stdout)
                            self.assertEqual("fail", verdict["status"])
                            if action == "resume":
                                reason = f"state-{field}-invalid"
                            elif field == "next_actions" and label in ("too-many", "empty"):
                                reason = "current-state-next-actions-limit"
                            else:
                                reason = "current-state-" + field.replace("_", "-") + "-invalid"
                            self.assertIn(reason, verdict["reasons"])
                            self.assertTrue(verdict["read_only"])
                            self.assertFalse(verdict["completion_allowed"])

    def test_public_state_error_vocabularies_and_schema_short_circuit_are_preserved(self):
        state = self._resume_state()
        state.update(schema_version="unknown", goal_ref="", next_actions=[None] * 4)
        preflight = self._public_goal("state-check", self.plan, state)
        resume = self._public_goal("resume", self.plan, state)
        self.assertEqual(1, preflight.returncode)
        self.assertEqual(1, resume.returncode)
        self.assertEqual(["current-state-schema-invalid"], json.loads(preflight.stdout)["reasons"])
        self.assertEqual(["current-state-fields-invalid", "state-goal_ref-invalid",
                          "state-next_actions-invalid"], json.loads(resume.stdout)["reasons"])

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
