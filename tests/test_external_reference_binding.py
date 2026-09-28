"""Exact metadata boundary for method-only local reference sources."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/external_agent_pattern_contracts.json"
CHECKER = ROOT / "scripts/check-external-agent-patterns.sh"


class ExternalReferenceBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def check(
        self, document: dict, *, lock: Optional[dict] = None,
        as_of: Optional[str] = None, max_age: Optional[int] = None,
    ) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="adk-reference-binding-") as scratch:
            path = Path(scratch) / "manifest.json"
            path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            command = ["bash", str(CHECKER), "--manifest", str(path)]
            if lock is not None:
                lock_path = Path(scratch) / "reference-lock.json"
                lock_path.write_text(json.dumps(lock), encoding="utf-8")
                command.extend(["--reference-lock", str(lock_path)])
            if max_age is not None:
                command.extend(["--as-of", as_of or "2026-09-28", "--max-observation-age-days", str(max_age)])
            return subprocess.run(
                command,
                cwd=str(ROOT), capture_output=True, text=True, check=False,
            )

    def lock(self) -> dict:
        by_path = {}
        for item in self.document["source_refs"]:
            path = item.get("local_path")
            if path and path not in by_path:
                by_path[path] = {
                    "kind": "reference-repo", "path": path,
                    "url": item["url"] + ".git", "commit": item["reference_pin"],
                }
        return {
            "schema": "llm-agent-reference-pins/v2",
            "policy": {"runtime_enablement": False, "pin_is_evidence_not_source": True},
            "pins": list(by_path.values()),
        }

    def source(self, document: dict, source_id: str) -> dict:
        return next(item for item in document["source_refs"] if item["id"] == source_id)

    def test_current_method_only_reference_bindings_pass(self) -> None:
        self.assertEqual(self.check(self.document).returncode, 0)

    def test_missing_or_inconsistent_exact_identity_is_rejected(self) -> None:
        for mutation, expected in (
            (lambda item: item.pop("reference_pin"), "missing key"),
            (lambda item: item.update(remote_relation="same"), "remote relation"),
            (lambda item: item.update(ancestry_checked=True), "ancestry_checked"),
            (lambda item: item.update(reference_pin="not-a-sha"), "reference pin"),
        ):
            document = copy.deepcopy(self.document)
            mutation(self.source(document, "openspec-resolution-parity"))
            result = self.check(document)
            with self.subTest(expected=expected):
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)

    def test_unapproved_host_and_inconsistent_duplicate_source_are_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        self.source(document, "openspec-resolution-parity")["url"] = "https://unreviewed.example/OpenSpec/repo"
        result = self.check(document)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical URL", result.stderr)

        document = copy.deepcopy(self.document)
        self.source(document, "vibeflow-browser-verification")["remote_head_observed"] = "f" * 40
        self.source(document, "vibeflow-browser-verification")["remote_relation"] = "different"
        result = self.check(document)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("disagrees with another entry", result.stderr)

    def test_unreviewed_date_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        self.source(document, "scale-engine-skill-domain-policy")["canonical_checked_at"] = "2099-01-01"
        result = self.check(document)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical check date", result.stderr)

    def test_optional_parent_lock_matches_exact_repository_and_pin(self) -> None:
        self.assertEqual(self.check(self.document, lock=self.lock(), max_age=0).returncode, 0)

        for mutation, expected in (
            (lambda lock: lock["pins"][0].update(commit="f" * 40), "exact pin differs"),
            (lambda lock: lock["pins"][0].update(url="https://github.com/other/repo.git"), "canonical URL differs"),
            (lambda lock: lock["pins"].pop(0), "lacks local source"),
            (lambda lock: lock["policy"].update(runtime_enablement=True), "not method-only"),
        ):
            lock = self.lock()
            mutation(lock)
            result = self.check(self.document, lock=lock, max_age=0)
            with self.subTest(expected=expected):
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)

    def test_observation_freshness_is_explicit_and_bounded(self) -> None:
        result = self.check(self.document, as_of="2026-10-30", max_age=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale", result.stderr)
        result = self.check(self.document, as_of="2026-09-28", max_age=0)
        self.assertEqual(result.returncode, 0)

    def test_manifest_reader_rejects_duplicate_fields_links_and_oversize(self) -> None:
        with tempfile.TemporaryDirectory(prefix="adk-reference-reader-") as scratch:
            scratch = Path(scratch)
            cases = (
                (b'{"source_refs":[],"source_refs":[]}', "duplicate JSON field"),
                (b" " * (2 * 1024 * 1024 + 1), "byte budget"),
            )
            for index, (raw, reason) in enumerate(cases):
                path = scratch / "case-{}.json".format(index)
                path.write_bytes(raw)
                result = subprocess.run(
                    ["bash", str(CHECKER), "--manifest", str(path)],
                    cwd=str(ROOT), capture_output=True, text=True, check=False,
                )
                with self.subTest(reason=reason):
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(reason, result.stderr)

            linked = scratch / "linked.json"
            linked.symlink_to(MANIFEST)
            result = subprocess.run(
                ["bash", str(CHECKER), "--manifest", str(linked)],
                cwd=str(ROOT), capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
