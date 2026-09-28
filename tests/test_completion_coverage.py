from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.completion_coverage import CoverageError, audit_coverage

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/completion_coverage_valid.json"


class CompletionCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_complete_structural_coverage_never_grants_completion(self) -> None:
        result = audit_coverage(self.value)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["counts"]["covered_required"], 2)
        self.assertEqual(result["missing_required"], [])
        self.assertRegex(result["normalized_input_sha256"], r"^[0-9a-f]{64}$")
        for field in ("evidence_authenticated", "verifier_authenticated", "command_executed_by_auditor",
                      "completion_allowed", "release_authorized"):
            self.assertFalse(result[field], field)

    def test_missing_required_and_skipped_required_are_visible(self) -> None:
        self.value["observations"] = self.value["observations"][:1]
        missing = audit_coverage(self.value)
        self.assertEqual(missing["status"], "needs-fix")
        self.assertEqual(missing["missing_required"], ["test"])
        self.value["observations"].append({"id": "test", "status": "skipped", "reason": "target unavailable"})
        skipped = audit_coverage(self.value)
        self.assertEqual(skipped["status"], "needs-fix")
        self.assertEqual(skipped["skipped_required"], ["test"])
        self.assertEqual(skipped["missing_required"], [])

    def test_failed_additional_check_still_blocks_coverage(self) -> None:
        failed = copy.deepcopy(self.value["observations"][0])
        failed.update({"id": "security", "status": "failed", "exit_code": 2})
        self.value["observations"].append(failed)
        result = audit_coverage(self.value)
        self.assertEqual(result["status"], "needs-fix")
        self.assertEqual(result["failed_checks"], ["security"])
        self.assertEqual(result["additional_checks"], ["security"])

    def test_stale_required_evidence_does_not_cover_check(self) -> None:
        self.value["observations"][0]["verified_at"] = "2026-09-28T10:00:00Z"
        result = audit_coverage(self.value)
        self.assertEqual(result["status"], "needs-fix")
        self.assertEqual(result["stale_checks"], ["build"])
        self.assertEqual(result["covered_required"], ["test"])

    def test_snapshot_mismatch_and_future_time_are_invalid(self) -> None:
        self.value["observations"][0]["source_snapshot_sha256"] = "d" * 64
        with self.assertRaisesRegex(CoverageError, "source snapshot differs"):
            audit_coverage(self.value)
        self.value["observations"][0]["source_snapshot_sha256"] = "a" * 64
        self.value["observations"][0]["verified_at"] = "2026-09-28T12:00:01Z"
        with self.assertRaisesRegex(CoverageError, "after as_of"):
            audit_coverage(self.value)

    def test_status_exit_code_ref_and_unknown_fields_are_invalid(self) -> None:
        self.value["observations"][0]["exit_code"] = 1
        with self.assertRaisesRegex(CoverageError, "status and exit_code disagree"):
            audit_coverage(self.value)
        self.value["observations"][0]["exit_code"] = 0
        self.value["observations"][0]["evidence_ref"] = "file:unbound"
        with self.assertRaisesRegex(CoverageError, "evidence_ref"):
            audit_coverage(self.value)
        self.value["observations"][0]["evidence_ref"] = "ref:" + "b" * 64
        self.value["extra"] = True
        with self.assertRaisesRegex(CoverageError, "exactly the declared fields"):
            audit_coverage(self.value)

    def test_duplicate_ids_and_invalid_skip_reason_are_rejected(self) -> None:
        self.value["required_checks"] = ["build", "build"]
        with self.assertRaisesRegex(CoverageError, "duplicate IDs"):
            audit_coverage(self.value)
        self.value["required_checks"] = ["build", "test"]
        self.value["observations"].append(copy.deepcopy(self.value["observations"][0]))
        with self.assertRaisesRegex(CoverageError, "duplicate observation ID"):
            audit_coverage(self.value)
        self.value["observations"] = [{"id": "build", "status": "skipped", "reason": " "}]
        with self.assertRaisesRegex(CoverageError, "reason is empty"):
            audit_coverage(self.value)

    def test_duplicate_json_field_is_rejected_by_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="adk-coverage-cli-") as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text('{"schema":"x","schema":"y"}', encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-m", "agent_dev_kit.completion_coverage", "--input", str(path), "--summary-json"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "invalid")
        self.assertFalse(payload["completion_allowed"])


if __name__ == "__main__":
    unittest.main()
