"""Development artifact acceptance, not Skill/model execution or E2-E4 evidence."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import ManifestError
from agent_dev_kit.task_acceptance import MAX_FILE_BYTES, grade_task_artifacts

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/skill_execution_tasks"
TASKS = (
    "deadline-repair", "review-false-positive", "goal-resume", "kws-asset-reuse",
    "crosscompile-applicability", "targeted-document-edit", "intent-distinction",
    "optional-availability-negation",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class SkillExecutionTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def prepare(self, task):
        package = self.root / task
        shutil.copytree(FIXTURES / task / "initial", package / "work")
        return package

    def grade(self, task, package, **overrides):
        options = dict(run_id="development-1", executor_id="fixture-author", grader_id="artifact-grader")
        options.update(overrides)
        return grade_task_artifacts(FIXTURES / task / "case.json", package, Path("acceptance.json"), **options)

    def solve(self, task, package):
        """Independent, known fixture answers; never read the grader's expected values."""
        work = package / "work"
        if task == "deadline-repair":
            source = work / "retry_policy.py"
            source.write_text(source.read_text().replace("<= timeout_ms", "< timeout_ms"))
            write_json(work / "expected-results.json", {
                "signal": "deadline-boundary", "scope": "expected-results-only",
                "cases": [{"elapsed_ms": n, "timeout_ms": 100, "retry_allowed": n < 100}
                          for n in (0, 99, 100, 101)],
            })
        elif task == "review-false-positive":
            write_json(work / "review.json", {
                "finding_id": "R1", "disposition": "false-positive", "review_mode": "feedback-triage",
                "source": "limit_items.py", "condition": "limit is None",
                "observed_outputs": [{"limit": n, "items": [1, 2] if n is None else [1, 2][:n]}
                                     for n in (None, 0, 1)], "required_changes": [],
            })
        elif task == "goal-resume":
            checkpoint = read_json(work / "checkpoint.json")
            receipt = read_json(work / "receipts/release.json")
            checkpoint.update(revision=checkpoint["revision"] + 1, last_completed="release-index",
                              publish_state=receipt["status"], next_actions=["verify-device"])
            write_json(work / "checkpoint.json", checkpoint)
            write_json(work / "release-index.json", {
                "release_id": receipt["release_id"], "package": receipt["package"],
                "receipt": "receipts/release.json", "publish_state": receipt["status"],
                "device_acceptance": "blocked",
            })
        elif task == "kws-asset-reuse":
            inventory = read_json(work / "inventory.json")
            selected = []
            for asset in inventory["assets"]:
                digest = hashlib.sha256((work / asset["path"]).read_bytes()).hexdigest()
                if asset["verified"] and asset["profile"] == inventory["requested_profile"] and digest == asset["sha256"]:
                    selected.append({"path": asset["path"], "sha256": digest})
            write_json(work / "selection.json", {
                "profile": inventory["requested_profile"], "reused_assets": selected,
                "new_assets": [], "runtime_evidence": "not-measured",
            })
        elif task == "crosscompile-applicability":
            write_json(work / "diagnosis.json", {
                "build_system": "autotools", "first_failure": (work / "build-output.txt").read_text().splitlines()[1],
                "failure_layer": "host", "next_probe": {
                    "kind": "host-tool-availability", "tools": ["aclocal", "automake", "autoconf"],
                }, "build_status": "not-run",
            })
            write_json(work / "target-probes.json", [
                {"target": target["id"], "probe": target["available_tools"][0], "measured": False}
                for target in read_json(work / "targets.json")
            ])
        elif task == "targeted-document-edit":
            adr = work / "docs/ADR-021.md"
            adr.write_text(adr.read_text().replace("Retry timeout: 250 ms.", "Retry timeout: 500 ms."))
        elif task == "intent-distinction":
            decisions = []
            for request in read_json(work / "requests.json"):
                clear = "approved_task" in request
                decisions.append({
                    "request_id": request["request_id"], "mode": "execute-approved" if clear else "explore",
                    "primary": "adk-planning-execution-loop" if clear else "adk-structured-requirements-questioning",
                    "questions": [] if clear else [{"id": "target-platform", "options": request["candidate_platforms"]}],
                })
            write_json(work / "decisions.json", decisions)
        elif task == "optional-availability-negation":
            installed = read_json(work / "inventory.json")["trusted_installed"]
            routes = []
            for request in read_json(work / "requests.json"):
                state = ("user-excluded" if request["negated"] else
                         "installed-eligible" if request["skill"] in installed else "not-installed")
                selected = request["skill"] if state == "installed-eligible" else None
                routes.append({"request_id": request["request_id"], "state": state, "selected": selected,
                               "load": [selected] if selected else [], "install": False})
            write_json(work / "routes.json", routes)
        else:
            self.fail("unknown development fixture")

    def corrupt_result(self, task, package):
        work = package / "work"
        if task == "deadline-repair":
            path = work / "retry_policy.py"
            path.write_text(path.read_text().replace("return elapsed_ms < timeout_ms", "return elapsed_ms <= timeout_ms"))
        elif task == "review-false-positive":
            path = work / "review.json"
            data = read_json(path)
            data.update(disposition="confirmed", required_changes=["limit_items.py"])
            write_json(path, data)
        elif task == "goal-resume":
            path = work / "checkpoint.json"
            data = read_json(path)
            data["logical_task_open"] = False
            write_json(path, data)
        elif task == "kws-asset-reuse":
            path = work / "selection.json"
            data = read_json(path)
            data["reused_assets"][0]["path"] = "assets/stale.txt"
            write_json(path, data)
        elif task == "crosscompile-applicability":
            path = work / "target-probes.json"
            data = read_json(path)
            data[1]["probe"] = "perf"
            write_json(path, data)
        elif task == "targeted-document-edit":
            path = work / "docs/ADR-021.md"
            path.write_text(path.read_text().replace("250 mA", "500 mA"))
        elif task == "intent-distinction":
            path = work / "decisions.json"
            data = read_json(path)
            data[0]["mode"] = "explore"
            data[0]["questions"] = [{"id": "confirm-plan", "options": ["yes", "no"]}]
            write_json(path, data)
        else:
            path = work / "routes.json"
            data = read_json(path)
            data[1].update(selected="adk-prose-revision", load=["adk-prose-revision"])
            write_json(path, data)

    def test_suite_is_eight_development_tasks_with_real_inputs(self):
        suite = read_json(FIXTURES / "suite.json")
        self.assertEqual(suite["split"], "development")
        self.assertEqual(suite["evaluation_status"], "not-measured")
        self.assertEqual({case["task_id"] for case in suite["cases"]}, set(TASKS))
        self.assertEqual(len({case["family"] for case in suite["cases"]}), 8)
        for row in suite["cases"]:
            self.assertTrue((FIXTURES / row["prompt"]).is_file())
            self.assertTrue(any((FIXTURES / row["task_id"] / "initial").rglob("*")))

    def test_all_eight_correct_outputs_produce_digest_bound_acceptance(self):
        for task in TASKS:
            with self.subTest(task=task):
                package = self.prepare(task)
                self.solve(task, package)
                result = self.grade(task, package)
                self.assertEqual(result["status"], "passed")
                self.assertEqual(result["evidence_scope"], "test-only")
                self.assertEqual(result["trust"], "caller-observed")
                self.assertFalse(result["raw_content_stored"])
                self.assertNotEqual(result["executor_id"], result["grader_id"])
                self.assertTrue(result["checks"])
                self.assertTrue(result["artifacts"])
                for ref in result["artifacts"] + [row["evidence"] for row in result["checks"] + result["guardrails"]]:
                    self.assertEqual(hashlib.sha256((package / ref["path"]).read_bytes()).hexdigest(), ref["sha256"])
                report = read_json(package / result["checks"][0]["evidence"]["path"])
                self.assertEqual(report["scope"], "final-artifact-conformance-only")
                self.assertIn("intermediate-side-effects", report["unverified"])
                self.assertIn("skill-loading", report["unverified"])

    def test_each_wrong_semantic_output_fails_without_losing_other_checks(self):
        for task in TASKS:
            with self.subTest(task=task):
                package = self.prepare(task)
                self.solve(task, package)
                self.corrupt_result(task, package)
                result = self.grade(task, package)
                self.assertEqual(result["status"], "failed")
                self.assertTrue(any(row["status"] == "failed" for row in result["checks"]))
                self.assertEqual(result["guardrails"][0]["status"], "passed")
                self.assertEqual(len(result["checks"]), len(read_json(FIXTURES / task / "case.json")["checks"]))

    def test_unmodified_input_is_not_task_success(self):
        for task in TASKS:
            with self.subTest(task=task):
                result = self.grade(task, self.prepare(task))
                self.assertEqual(result["status"], "failed")

    def test_original_bug_signal_really_fails_before_and_passes_after_fixed_patch(self):
        task = "deadline-repair"
        package = self.prepare(task)
        command = [sys.executable, "-B", "-m", "unittest", "deadline_cases", "-v"]
        # This runs only the committed, known source fixture and our fixed patch;
        # grade_task_artifacts never runs a command or arbitrary candidate code.
        before = subprocess.run(command, cwd=package / "work", capture_output=True, text=True, timeout=10)
        self.assertNotEqual(before.returncode, 0)
        self.assertIn("test_original_symptom_at_deadline", before.stderr)
        self.assertIn("failures=1", before.stderr)
        self.solve(task, package)
        after = subprocess.run(command, cwd=package / "work", capture_output=True, text=True, timeout=10)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertIn("Ran 3 tests", after.stderr)
        self.assertEqual(self.grade(task, package)["status"], "passed")

    def test_unrequested_file_fails_boundary_even_when_all_outputs_match(self):
        task = "goal-resume"
        package = self.prepare(task)
        self.solve(task, package)
        (package / "work/receipts/replayed-publish.json").write_text("{}\n")
        result = self.grade(task, package)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(all(row["status"] == "passed" for row in result["checks"]))
        self.assertEqual(result["guardrails"][0]["status"], "failed")

    def test_claimed_success_cannot_replace_missing_artifact(self):
        task = "kws-asset-reuse"
        package = self.prepare(task)
        self.solve(task, package)
        (package / "work/assets/features.csv").unlink()
        result = self.grade(task, package)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(next(row for row in result["checks"] if row["name"] == "verified-features-preserved")["status"], "failed")

    def test_json_does_not_coerce_boolean_number_or_accept_duplicate_keys(self):
        task = "intent-distinction"
        package = self.prepare(task)
        self.solve(task, package)
        path = package / "work/decisions.json"
        for malformed in ('{"status":"failed","status":"passed"}', '[' * 65 + ']' * 65,
                          '{"not_a_number":NaN}', '"' + "x" * MAX_FILE_BYTES + '"'):
            with self.subTest(payload_kind=malformed[:30]):
                path.write_text(malformed)
                self.assertEqual(self.grade(task, package)["status"], "failed")
        task = "optional-availability-negation"
        package = self.prepare(task)
        self.solve(task, package)
        path = package / "work/routes.json"
        data = read_json(path)
        data[2]["install"] = 0
        write_json(path, data)
        self.assertEqual(self.grade(task, package)["status"], "failed")

    def test_reference_and_output_cannot_be_symlinked_or_escape(self):
        task = "targeted-document-edit"
        package = self.prepare(task)
        self.solve(task, package)
        target = package / "work/docs/ADR-021.md"
        outside = self.root / "outside.md"
        outside.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(outside)
        self.assertEqual(self.grade(task, package)["status"], "failed")
        self.assertEqual(outside.read_bytes(), target.read_bytes())
        with self.assertRaises(ManifestError):
            grade_task_artifacts(FIXTURES / task / "case.json", package, self.root / "escaped.json",
                                 run_id="dev", executor_id="author", grader_id="grader")
        self.assertFalse((self.root / "escaped.json").exists())
        with self.assertRaises(ManifestError):
            grade_task_artifacts(FIXTURES / task / "case.json", package, Path("work/acceptance.json"),
                                 run_id="dev", executor_id="author", grader_id="grader")

    def test_special_file_does_not_block_or_pass(self):
        task = "targeted-document-edit"
        package = self.prepare(task)
        self.solve(task, package)
        os.mkfifo(package / "work/unexpected-fifo")
        self.assertEqual(self.grade(task, package)["status"], "failed")

    def test_executor_grader_identity_and_frozen_case_boundary(self):
        task = "targeted-document-edit"
        package = self.prepare(task)
        self.solve(task, package)
        with self.assertRaises(ManifestError):
            self.grade(task, package, executor_id="same", grader_id="same")
        with self.assertRaises(ManifestError):
            self.grade(task, package, grader_id="Invalid-Uppercase")
        shutil.copy2(FIXTURES / task / "case.json", package / "case.json")
        with self.assertRaises(ManifestError):
            grade_task_artifacts(package / "case.json", package, Path("acceptance.json"),
                                 run_id="dev", executor_id="author", grader_id="grader")

    def test_case_cannot_add_commands_or_traversal_or_omit_input_coverage(self):
        task = "targeted-document-edit"
        package = self.prepare(task)
        self.solve(task, package)
        owner = self.root / "owner"
        shutil.copytree(FIXTURES / task, owner)
        original = read_json(owner / "case.json")
        for kind in ("command", "traversal", "unsupported-path", "omitted-input", "duplicate-check"):
            with self.subTest(kind=kind):
                data = json.loads(json.dumps(original))
                if kind == "command":
                    data["checks"][0] = {"name": "inject", "kind": "command", "path": "work/escape",
                                         "command": "touch should-never-exist"}
                elif kind == "traversal":
                    data["checks"][0]["path"] = "work/../escape"
                elif kind == "unsupported-path":
                    data["checks"][0]["path"] = "work/name:with-space .json"
                elif kind == "omitted-input":
                    data["checks"][0] = {"name": "trivial", "kind": "json-equals", "path": "work/trivial.json", "expected": {}}
                else:
                    data["checks"].append(data["checks"][0].copy())
                write_json(owner / "case.json", data)
                with self.assertRaises(ManifestError):
                    grade_task_artifacts(owner / "case.json", package, Path("acceptance.json"),
                                         run_id="dev", executor_id="author", grader_id="grader")
                self.assertFalse((package / "acceptance.json").exists())
                self.assertFalse((package / "should-never-exist").exists())


if __name__ == "__main__":
    unittest.main()
