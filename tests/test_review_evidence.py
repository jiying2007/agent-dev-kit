"""Synthetic review-contract tests; fixtures are never real review evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit import review_evidence as review
from agent_dev_kit.readiness import run_harness_readiness
from agent_dev_kit.readiness_evidence import EXPECTED_DIMENSIONS

SOURCE_ROOT = Path(__file__).resolve().parents[1]


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(value):
    return value.isoformat().replace("+00:00", "Z")


class ReviewEvidenceFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-review-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        (self.root / ".adk").mkdir()
        (self.root / "source.py").write_bytes(b"value = 1\n")
        self.directory = self.root / "docs/changes/example"
        self.directory.mkdir(parents=True)
        self.original_patch = self.directory / review.TARGET_PATCH_PATH
        self.original_patch.parent.mkdir()
        self.original_patch.write_bytes(b"diff --git a/source.py b/source.py\n--- a/source.py\n+++ b/source.py\n"
                                        b"@@ -1 +1 @@\n-value = 0\n+value = 1\n")
        (self.directory / "details.md").write_bytes(b"Synthetic independent review and test evidence.\n")
        self.record_path = self.directory / "review-evidence.json"
        self.authorization = self.root / ".adk/authorization.md"
        self.authorization.write_bytes(b"Synthetic test-only owner delegation; not a user instruction.\n")
        self.policy = {"schema": review.POLICY_SCHEMA, "mode": "owner-delegated-ai", "owner": "leiwenjun",
                       "allowed_scopes": sorted(review.SCOPES),
                       "authorization": {"path": ".adk/authorization.md", "sha256": sha(self.authorization),
                                         "granted_at": stamp(self.now - timedelta(minutes=2))}}
        self.policy_path = self.root / review.POLICY_PATH
        self.policy_path.write_bytes(encoded(self.policy))
        self.record = {"schema": review.SCHEMA, "subject_id": "example", "scope": "source-change",
                       "owner": "leiwenjun", "author_id": "implementation-agent",
                       "reviewer": {"id": "independent-review-agent", "kind": "ai", "independence": "independent"},
                       "reviewed_at": stamp(self.now - timedelta(seconds=1)),
                       "evidence_completed_at": stamp(self.now - timedelta(seconds=2)),
                       "verdicts": {"spec": "pass", "quality": "pass"}, "findings": [],
                       "limitations": ["Synthetic fixture; no human, model, field, or product qualification."],
                       "target": {"base_commit": "a" * 40, "head_commit": "b" * 40,
                                  "original_patch_sha256": sha(self.original_patch)},
                       "policy_sha256": sha(self.policy_path), "validator_sha256": review.validator_fingerprints(),
                       "sources": [self.reference("source.py"), self.reference(review.TARGET_PATCH_PATH, base="record")],
                       "evidence": [self.reference("details.md", base="record")]}

    def reference(self, path, base="repository"):
        root = self.root if base == "repository" else self.directory
        return {"base": base, "path": path, "sha256": sha(root / path)}

    def write_record(self):
        self.record_path.write_bytes(encoded(self.record))

    def validate(self, **kwargs):
        self.write_record()
        return review.validate_review(self.root, self.record_path, expected_subject=self.record["subject_id"],
                                      expected_scope=self.record["scope"], now=self.now, **kwargs)


class ReviewEvidenceTests(ReviewEvidenceFixture):
    def test_valid_record_preserves_declared_ai_identity_and_scope(self):
        result = self.validate()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["reviewer"], self.record["reviewer"])
        self.assertEqual(result["record_sha256"], sha(self.record_path))
        self.assertEqual(result["target"], self.record["target"])
        for flag in ("human_review_performed", "field_evidence_verified", "provider_execution_performed",
                     "product_release_authorized"):
            self.assertFalse(result[flag])

    def test_validator_fingerprints_use_the_actual_loaded_modules(self):
        shadow = self.root / "src/agent_dev_kit/review_evidence.py"
        shadow.parent.mkdir(parents=True)
        shadow.write_bytes(b"# unrelated, caller-controlled validator lookalike\n")
        self.record["validator_sha256"]["src/agent_dev_kit/review_evidence.py"] = sha(shadow)
        with self.assertRaisesRegex(review.ReviewEvidenceError, "validator source identity"):
            self.validate()

    def test_no_policy_cannot_enable_delegated_review(self):
        self.policy_path.unlink()
        with self.assertRaises(review.ReviewEvidenceError):
            self.validate()

    def test_policy_and_authorization_changes_invalidate_old_review(self):
        for path in (self.policy_path, self.authorization):
            original = path.read_bytes()
            with self.subTest(path=path.name):
                path.write_bytes(original + b"\n")
                with self.assertRaises(review.ReviewEvidenceError):
                    self.validate()
            path.write_bytes(original)

    def test_unscoped_and_unknown_scope_delegations_are_rejected(self):
        self.policy["allowed_scopes"] = ["harness-source"]
        self.policy_path.write_bytes(encoded(self.policy))
        self.record["policy_sha256"] = sha(self.policy_path)
        with self.assertRaisesRegex(review.ReviewEvidenceError, "scope is not delegated"):
            self.validate()

    def test_subject_and_scope_must_match_the_consumer(self):
        self.write_record()
        for subject, scope in (("other", "source-change"), ("example", "longitudinal-review")):
            with self.subTest(subject=subject, scope=scope), self.assertRaises(review.ReviewEvidenceError):
                review.validate_review(self.root, self.record_path, expected_subject=subject,
                                       expected_scope=scope, now=self.now)

    def test_malformed_record_field_types_raise_only_review_errors(self):
        original = copy.deepcopy(self.record)
        for field in original:
            for value in (None, True, 0, {}, [{}]):
                with self.subTest(field=field, value=value), self.assertRaises(review.ReviewEvidenceError):
                    self.record = dict(original, **{field: value})
                    self.validate()

    def test_malformed_nested_field_types_raise_only_review_errors(self):
        original = copy.deepcopy(self.record)
        finding = {"id": "finding-1", "severity": "minor", "disposition": "fixed", "reason": "Synthetic fix."}
        for group, fields in (("reviewer", ("id", "kind", "independence")),
                              ("target", ("base_commit", "head_commit", "original_patch_sha256")),
                              ("findings", ("id", "severity", "disposition", "reason")),
                              ("sources", ("base", "path", "sha256"))):
            for field in fields:
                for value in ({}, [{}]):
                    self.record = copy.deepcopy(original)
                    if group == "findings":
                        self.record[group] = [dict(finding)]
                    item = self.record[group][0] if group in ("findings", "sources") else self.record[group]
                    item[field] = value
                    with self.subTest(group=group, field=field, value=value):
                        with self.assertRaises(review.ReviewEvidenceError):
                            self.validate()

    def test_malformed_policy_and_authorization_raise_only_review_errors(self):
        original = copy.deepcopy(self.policy)
        for group, fields in (("policy", tuple(original)), ("authorization", ("path", "sha256", "granted_at"))):
            for field in fields:
                for value in ({}, [{}]):
                    candidate = copy.deepcopy(original)
                    item = candidate if group == "policy" else candidate[group]
                    item[field] = value
                    self.policy_path.write_bytes(encoded(candidate))
                    self.record["policy_sha256"] = sha(self.policy_path)
                    with self.subTest(group=group, field=field, value=value):
                        with self.assertRaises(review.ReviewEvidenceError):
                            self.validate()

    def test_real_independence_is_not_replaced_by_author_self_review(self):
        original = copy.deepcopy(self.record["reviewer"])
        for change in ({"id": self.record["author_id"]}, {"kind": "human"},
                       {"independence": "author-self-review"}, {"id": ""}):
            with self.subTest(change=change):
                self.record["reviewer"] = dict(original, **change)
                with self.assertRaises(review.ReviewEvidenceError):
                    self.validate()

    def test_time_must_follow_authorization_and_evidence_and_not_be_future(self):
        original = copy.deepcopy(self.record)
        cases = (("reviewed_at", stamp(self.now - timedelta(minutes=3))),
                 ("reviewed_at", stamp(self.now + timedelta(days=1))),
                 ("evidence_completed_at", stamp(self.now)),
                 ("reviewed_at", "2026-10-20T00:00:00"),
                 ("reviewed_at", "2026-02-30T00:00:00Z"))
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.record = dict(original, **{field: value})
                with self.assertRaises(review.ReviewEvidenceError):
                    self.validate()

    def test_separate_spec_and_quality_pass_are_required(self):
        for verdicts in ({"spec": "pass"}, {"spec": "needs-fix", "quality": "pass"},
                         {"spec": "pass", "quality": "needs-fix"}):
            with self.subTest(verdicts=verdicts), self.assertRaises(review.ReviewEvidenceError):
                self.record["verdicts"] = verdicts
                self.validate()

    def test_unresolved_severe_findings_reject_pass(self):
        for severity in ("blocker", "major"):
            self.record["findings"] = [{"id": "finding-1", "severity": severity,
                                        "disposition": "open", "reason": "Unresolved synthetic finding."}]
            with self.subTest(severity=severity), self.assertRaises(review.ReviewEvidenceError):
                self.validate()
        self.record["findings"][0]["disposition"] = "accepted-risk"
        self.assertEqual(self.validate()["status"], "pass")
        self.record["findings"][0]["reason"] = ""
        with self.assertRaises(review.ReviewEvidenceError):
            self.validate()

    def test_exact_original_base_and_head_are_required(self):
        for target in ({"base_commit": "a" * 40}, {"base_commit": "main", "head_commit": "b" * 40}):
            self.record["target"] = target
            with self.subTest(target=target), self.assertRaises(review.ReviewEvidenceError):
                self.validate()

    def test_retained_original_patch_is_required_not_an_unrelated_source(self):
        self.record["sources"] = [self.reference("source.py")]
        with self.assertRaisesRegex(review.ReviewEvidenceError, "complete original patch"):
            self.validate()

    def test_original_patch_digest_must_match_the_declared_target(self):
        self.record["target"]["original_patch_sha256"] = "0" * 64
        with self.assertRaisesRegex(review.ReviewEvidenceError, "original patch identity"):
            self.validate()

    def test_original_patch_must_retain_diff_bytes_and_record_relative_path(self):
        original = self.original_patch.read_bytes()
        for payload in (b"", b"reviewed a synthetic patch", b"\n" + original):
            self.original_patch.write_bytes(payload)
            self.record["sources"][1] = self.reference(review.TARGET_PATCH_PATH, base="record")
            self.record["target"]["original_patch_sha256"] = sha(self.original_patch)
            with self.subTest(payload=payload), self.assertRaises(review.ReviewEvidenceError):
                self.validate()
        self.original_patch.write_bytes(original)
        self.record["sources"][1] = self.reference(self.original_patch.relative_to(self.root).as_posix())
        self.record["target"]["original_patch_sha256"] = sha(self.original_patch)
        with self.assertRaisesRegex(review.ReviewEvidenceError, "complete original patch"):
            self.validate()

    def test_source_and_evidence_changes_cannot_reuse_review(self):
        for path in (self.root / "source.py", self.directory / "details.md", self.original_patch):
            original = path.read_bytes()
            path.write_bytes(original + b"modified\n")
            with self.subTest(path=path.name), self.assertRaises(review.ReviewEvidenceError):
                self.validate()
            path.write_bytes(original)

    def test_record_relative_evidence_survives_canonical_archive_move(self):
        result = self.validate()
        archive = self.root / "docs/changes/archive/20261020-example"
        archive.parent.mkdir()
        self.directory.rename(archive)
        self.directory = archive
        self.record_path = archive / "review-evidence.json"
        self.assertEqual(self.validate()["record_sha256"], result["record_sha256"])

    def test_relative_paths_cannot_escape_alias_or_follow_links(self):
        original = self.record["sources"][0]
        link = self.root / "linked.py"
        link.symlink_to(self.root / "source.py")
        directory = self.root / "linked-directory"
        directory.symlink_to(self.root, target_is_directory=True)
        for path in ("../source.py", "./source.py", "a/../source.py", "//source.py", "a\\b",
                     "/source.py", "linked.py", "linked-directory/source.py", "source\x00.py",
                     "source\n.py", "source\ud800.py"):
            with self.subTest(path=path), self.assertRaises(review.ReviewEvidenceError):
                self.record["sources"] = [dict(original, path=path)]
                self.validate()

    def test_symlink_root_and_nonregular_reference_are_rejected(self):
        alias = self.root / "root-link"
        alias.symlink_to(self.root, target_is_directory=True)
        self.write_record()
        with self.assertRaises(review.ReviewEvidenceError):
            review.validate_review(alias, Path("docs/changes/example/review-evidence.json"),
                                   expected_subject="example", expected_scope="source-change", now=self.now)
        fifo = self.root / "source-fifo"
        os.mkfifo(str(fifo))
        self.record["sources"][0]["path"] = "source-fifo"
        with self.assertRaises(review.ReviewEvidenceError):
            self.validate()

    def test_duplicate_and_self_references_are_rejected(self):
        self.record["sources"] *= 2
        with self.assertRaises(review.ReviewEvidenceError):
            self.validate()
        self.record["sources"] = [{"base": "record", "path": "review-evidence.json", "sha256": "0" * 64}]
        with self.assertRaisesRegex(review.ReviewEvidenceError, "own source"):
            self.validate()

    def test_reference_count_and_byte_budgets_are_enforced(self):
        with patch.object(review, "MAX_REFERENCES", 1), self.assertRaises(review.ReviewEvidenceError):
            self.validate()
        with patch.object(review, "MAX_TOTAL_BYTES", 1), self.assertRaises(review.ReviewEvidenceError):
            self.validate()
        source = self.root / "source.py"
        source.write_bytes(b"x" * (128 * 1024 + 1))
        self.record["sources"] = [self.reference("source.py")]
        with patch.object(review, "MAX_REFERENCE_BYTES", 128 * 1024), self.assertRaises(review.ReviewEvidenceError):
            self.validate()

    def test_duplicate_json_nonfinite_and_oversized_records_are_rejected(self):
        for raw in (b'{"schema":"first","schema":"second"}', b'{"value":NaN}',
                    b"x" * (review.MAX_RECORD_BYTES + 1)):
            self.record_path.write_bytes(raw)
            with self.subTest(raw_size=len(raw)), self.assertRaises(review.ReviewEvidenceError):
                review.validate_review(self.root, self.record_path, expected_subject="example",
                                       expected_scope="source-change", now=self.now)

    def test_downstream_repository_reuses_the_single_explicit_adk_policy(self):
        downstream = self.root / "consumer"
        downstream.mkdir()
        (downstream / "source.py").write_bytes((self.root / "source.py").read_bytes())
        (downstream / "details.md").write_bytes((self.directory / "details.md").read_bytes())
        self.record["subject_id"] = "real-campaign-review"
        self.record["scope"] = "effect-value-review"
        self.record.pop("target")
        self.record["sources"] = [self.reference("source.py")]
        path = downstream / "review-evidence.json"
        path.write_bytes(encoded(self.record))
        kwargs = {"expected_subject": self.record["subject_id"], "expected_scope": self.record["scope"], "now": self.now}
        with self.assertRaises(review.ReviewEvidenceError):
            review.validate_review(downstream, path, **kwargs)
        checked = review.validate_review(downstream, path, policy_root=self.root, **kwargs)
        self.assertEqual(checked["reviewer"]["kind"], "ai")
        self.assertFalse(checked["field_evidence_verified"])


class ReadinessUtcDateTests(unittest.TestCase):
    def test_default_evaluation_day_is_utc_across_local_midnight(self):
        root = SOURCE_ROOT / "fixtures/harness-readiness/pass/team-repo"
        for utc_now, local_day in (
            (datetime(2026, 10, 21, 0, 30, tzinfo=timezone.utc), date(2026, 10, 20)),
            (datetime(2026, 10, 20, 23, 30, tzinfo=timezone.utc), date(2026, 10, 21)),
        ):
            with self.subTest(utc=utc_now, local=local_day), \
                 patch("agent_dev_kit.readiness.datetime", create=True, wraps=datetime) as clock, \
                 patch("agent_dev_kit.readiness.date", wraps=date) as host_date:
                clock.now.return_value = utc_now
                host_date.today.return_value = local_day
                report = run_harness_readiness(
                    root, contract_path=SOURCE_ROOT / "manifests/harness_readiness_contracts.json",
                    mode="gate",
                )
                self.assertEqual(utc_now.date().isoformat(), report["as_of"])


class HarnessDelegatedReviewTests(ReviewEvidenceFixture):
    def setUp(self):
        super().setUp()
        fixture = SOURCE_ROOT / "fixtures/harness-readiness/pass/team-repo"
        shutil.copytree(fixture, self.root, dirs_exist_ok=True)
        for name in review.HARNESS_SOURCE_PATHS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_ROOT / name, target)
        # Recreate the explicit test-only policy overwritten by no fixture.
        self.policy_path.write_bytes(encoded(self.policy))
        metadata_path = self.root / ".adk/harness-readiness.json"
        self.metadata = json.loads(metadata_path.read_text())
        for value in self.metadata["dimensions"].values():
            value["owner"] = "leiwenjun"
            value["last_verified_at"] = self.record["reviewed_at"].split("T")[0]
        metadata_path.write_bytes(encoded(self.metadata))
        # Remove policy only while collecting synthetic input references. This
        # fixture scan is never evidence of actual owner or repository review.
        policy_raw = self.policy_path.read_bytes()
        self.policy_path.unlink()
        raw = self.run_harness()
        self.policy_path.write_bytes(policy_raw)
        paths = {path for dim in raw["dimensions"] for path in dim["evidence_refs"]
                 if path != ".adk/harness-readiness.json"}
        self.record.update(subject_id="harness-readiness", scope="harness-source",
                           dimension_ids=list(EXPECTED_DIMENSIONS),
                           sources=[self.reference(path) for path in sorted(paths | review.HARNESS_SOURCE_PATHS)])
        self.record.pop("target")
        self.refresh_metadata()

    def refresh_metadata(self):
        self.write_record()
        for item in self.metadata["dimensions"].values():
            item["review_evidence"] = {"path": self.record_path.relative_to(self.root).as_posix(),
                                       "sha256": sha(self.record_path)}
        (self.root / ".adk/harness-readiness.json").write_bytes(encoded(self.metadata))

    def run_harness(self):
        return run_harness_readiness(self.root,
                                     contract_path=self.root / "manifests/harness_readiness_contracts.json",
                                     mode="gate")

    def test_current_delegated_review_can_pass_without_claiming_human_or_field(self):
        report = self.run_harness()
        self.assertEqual(report["overall_status"], "pass", report)
        self.assertEqual(report["field_evidence_status"], "not-verified")
        self.assertTrue(all(dim["review"]["reviewer"]["kind"] == "ai" for dim in report["dimensions"]))
        self.assertTrue(all(dim["owner"] == "leiwenjun" for dim in report["dimensions"]))

    def test_utc_review_is_not_future_when_host_calendar_is_previous_day(self):
        with patch("agent_dev_kit.readiness.datetime", create=True, wraps=datetime) as clock, \
             patch("agent_dev_kit.readiness.date", wraps=date) as host_date:
            clock.now.return_value = self.now
            host_date.today.return_value = self.now.date() - timedelta(days=1)
            report = self.run_harness()
        self.assertEqual(self.now.date().isoformat(), report["as_of"])
        self.assertEqual("pass", report["overall_status"], report)
        self.assertEqual("not-verified", report["field_evidence_status"])

    def test_ai_receipt_cannot_be_treated_as_legacy_review_without_policy(self):
        self.policy_path.unlink()
        report = self.run_harness()
        self.assertEqual(report["overall_status"], "needs-review", report)
        self.assertTrue(all(dim["review"]["status"] == "invalid" for dim in report["dimensions"]))

    def test_metadata_receipt_pointer_requires_canonical_relative_shape(self):
        item = self.metadata["dimensions"][EXPECTED_DIMENSIONS[0]]
        original = copy.deepcopy(item["review_evidence"])
        for reference in ({}, [], {"path": [], "sha256": original["sha256"]},
                          dict(original, path=str(self.record_path)),
                          dict(original, path="./" + original["path"]),
                          dict(original, path="docs/../" + original["path"]),
                          dict(original, sha256={})):
            item["review_evidence"] = reference
            (self.root / ".adk/harness-readiness.json").write_bytes(encoded(self.metadata))
            with self.subTest(reference=reference):
                self.assertEqual(self.run_harness()["overall_status"], "needs-review")

    def test_date_only_renewal_or_removing_one_dimension_receipt_cannot_pass(self):
        item = self.metadata["dimensions"][EXPECTED_DIMENSIONS[0]]
        item.pop("review_evidence")
        (self.root / ".adk/harness-readiness.json").write_bytes(encoded(self.metadata))
        self.assertEqual(self.run_harness()["overall_status"], "needs-review")
        self.refresh_metadata()
        item["last_verified_at"] = (self.now + timedelta(days=1)).date().isoformat()
        (self.root / ".adk/harness-readiness.json").write_bytes(encoded(self.metadata))
        self.assertEqual(self.run_harness()["overall_status"], "needs-review")

    def test_receipt_requires_exact_all_seven_dimensions_and_owner(self):
        original = copy.deepcopy(self.record)
        for change in ({"dimension_ids": list(EXPECTED_DIMENSIONS[:-1])},
                       {"dimension_ids": [EXPECTED_DIMENSIONS[0]] * 7},
                       {"dimension_ids": [{}] * 7}, {"dimension_ids": {}}, {"owner": "another-owner"}):
            self.record = dict(original, **change)
            self.refresh_metadata()
            with self.subTest(change=change):
                self.assertEqual(self.run_harness()["overall_status"], "needs-review")

    def test_scan_sources_and_evaluator_changes_require_new_review(self):
        for relative in ("README.md", "src/agent_dev_kit/readiness_tools.py"):
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b"\nchanged\n")
            with self.subTest(relative=relative):
                self.assertEqual(self.run_harness()["overall_status"], "needs-review")
            path.write_bytes(original)

    def test_harness_record_cannot_omit_actual_scanned_source(self):
        self.record["sources"] = [ref for ref in self.record["sources"] if ref["path"] != "README.md"]
        self.refresh_metadata()
        self.assertEqual(self.run_harness()["overall_status"], "needs-review")

    def test_stale_review_remains_stale_after_delegation(self):
        past = self.now - timedelta(days=92)
        self.policy["authorization"]["granted_at"] = stamp(past - timedelta(days=1))
        self.policy_path.write_bytes(encoded(self.policy))
        self.record.update(policy_sha256=sha(self.policy_path), reviewed_at=stamp(past),
                           evidence_completed_at=stamp(past - timedelta(seconds=1)))
        for item in self.metadata["dimensions"].values():
            item["last_verified_at"] = past.date().isoformat()
        self.refresh_metadata()
        report = self.run_harness()
        self.assertEqual(report["overall_status"], "partial", report)
        self.assertTrue(all(any(b["code"] == "stale_last_verified_at" for b in dim["blockers"])
                            for dim in report["dimensions"]))

    def test_not_applicable_dimension_still_requires_delegated_review(self):
        (self.root / "mcp.json").unlink()
        # The changed applicable-source inventory must be truthfully reviewed.
        self.record["sources"] = [ref for ref in self.record["sources"] if ref["path"] != "mcp.json"]
        self.refresh_metadata()
        tool = self.metadata["dimensions"]["tool_and_permission_boundary"]
        tool.pop("review_evidence")
        (self.root / ".adk/harness-readiness.json").write_bytes(encoded(self.metadata))
        report = self.run_harness()
        dim = next(item for item in report["dimensions"] if item["dimension_id"] == "tool_and_permission_boundary")
        self.assertEqual(dim["status"], "needs-review", dim)

    def test_duplicate_metadata_cannot_hide_removed_review_reference(self):
        path = self.root / ".adk/harness-readiness.json"
        path.write_text('{"schema_version":1,"dimensions":{},"dimensions":{}}')
        report = self.run_harness()
        self.assertEqual(report["overall_status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
