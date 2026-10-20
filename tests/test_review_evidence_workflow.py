"""Lifecycle integration tests with explicit synthetic delegated evidence."""
from __future__ import annotations

import subprocess
from datetime import datetime

from test_review_evidence import ReviewEvidenceFixture, SOURCE_ROOT, sha


class DelegatedWorkflowTests(ReviewEvidenceFixture):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=SyntheticTest",
                        "-c", "user.email=synthetic@example.invalid", "commit", "-q", "--allow-empty",
                        "-m", "Synthetic fixture; not a real review"], check=True)
        self.head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        self.state = self.directory / "state.yaml"
        self.state.write_text("stage: verified\nowner: synthetic-author\n", encoding="utf-8")
        self.report = self.directory / "review-report.md"
        self.report.write_text("Original historical report remains intact until validation.\n", encoding="utf-8")
        self.original_state = self.state.read_bytes()
        self.original_report = self.report.read_bytes()

    def command(self, action, *args):
        options = ["bash", str(SOURCE_ROOT / "scripts/workflow.sh"), action,
                   "--root", str(self.root / "docs/changes"), "--change", "example",
                   "--owner", self.record["reviewer"]["id"]]
        if action == "review":
            options.extend(["--result", "pass", "--blockers", "0", "--majors", "0", "--minors", "0"])
        return subprocess.run(options + list(args), capture_output=True, text=True)

    def assert_unmodified(self):
        self.assertEqual(self.state.read_bytes(), self.original_state)
        self.assertEqual(self.report.read_bytes(), self.original_report)
        self.assertFalse((self.directory / "history.log").exists())

    def test_missing_receipt_rejects_pass_before_report_or_state_mutation(self):
        self.assertNotEqual(self.command("review").returncode, 0)
        self.assert_unmodified()

    def test_deleted_policy_cannot_convert_existing_ai_receipt_to_legacy_pass(self):
        self.write_record()
        self.policy_path.unlink()
        self.assertNotEqual(self.command("review").returncode, 0)
        self.assert_unmodified()

    def test_non_git_workspace_cannot_accept_existing_ai_receipt_as_legacy(self):
        import shutil

        self.write_record()
        shutil.rmtree(self.root / ".git")
        self.assertNotEqual(self.command("review").returncode, 0)
        self.assert_unmodified()

    def test_stale_source_or_false_review_identity_rejects_before_mutation(self):
        self.write_record()
        original = (self.root / "source.py").read_bytes()
        (self.root / "source.py").write_bytes(b"changed source\n")
        self.assertNotEqual(self.command("review").returncode, 0)
        self.assert_unmodified()
        (self.root / "source.py").write_bytes(original)
        self.record["reviewer"]["id"] = self.record["author_id"]
        self.write_record()
        self.assertNotEqual(self.command("review").returncode, 0)
        self.assert_unmodified()

    def test_cli_counts_cannot_contradict_real_findings(self):
        self.record["findings"] = [{"id": "synthetic-minor", "severity": "minor", "disposition": "open",
                                    "reason": "Synthetic unresolved low-impact issue."}]
        self.write_record()
        result = self.command("review")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("counts", result.stderr)
        self.assert_unmodified()

    def test_valid_review_and_archive_preserve_receipt_bytes_and_target_provenance(self):
        self.write_record()
        digest = sha(self.record_path)
        reviewed = self.command("review", "--review-evidence", str(self.record_path),
                                "--owner", "synthetic-lifecycle-operator")
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        self.assertIn("stage: review-passed", self.state.read_text())
        self.assertIn("执行人：synthetic-lifecycle-operator", self.report.read_text())
        self.assertIn("Reviewer Identity: " + self.record["reviewer"]["id"], self.report.read_text())
        archived = self.command("archive", "--owner", "synthetic-archive-operator")
        self.assertEqual(archived.returncode, 0, archived.stderr)
        archive, = (self.root / "docs/changes/archive").glob("*-example")
        self.assertFalse(self.directory.exists())
        self.assertEqual(sha(archive / "review-evidence.json"), digest)
        self.assertIn("stage: archived", (archive / "state.yaml").read_text())
        provenance = (archive / "provenance.md").read_text()
        self.assertIn("repository_head: " + self.head, provenance)
        self.assertIn("force_archive: 0", provenance)
        self.assertIn("archived_by: synthetic-archive-operator", provenance)
        self.assertIn("reviewer_id: " + self.record["reviewer"]["id"], provenance)
        self.assertIn("review_verdict: pass", provenance)
        self.assertIn("review_record_sha256: " + digest, provenance)

    def test_archive_revalidates_changed_evidence_even_with_force(self):
        self.write_record()
        reviewed = self.command("review")
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        state, report = self.state.read_bytes(), self.report.read_bytes()
        (self.directory / "details.md").write_bytes(b"changed after semantic review\n")
        rejected = self.command("archive", "--force")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(self.state.read_bytes(), state)
        self.assertEqual(self.report.read_bytes(), report)
        self.assertFalse((self.directory / "provenance.md").exists())

    def test_existing_archive_destination_cannot_nest_or_mutate_active_package(self):
        self.write_record()
        reviewed = self.command("review")
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        state = self.state.read_bytes()
        archive = self.root / "docs/changes/archive" / (datetime.now().strftime("%Y%m%d") + "-example")
        archive.mkdir(parents=True)
        (archive / "sentinel").write_bytes(b"older archive")
        rejected = self.command("archive")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(self.state.read_bytes(), state)
        self.assertEqual((archive / "sentinel").read_bytes(), b"older archive")
        self.assertFalse((archive / "example").exists())
