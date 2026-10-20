"""Different-version installation and release rehearsal acceptance tests.

Sources, local Git commits and artifacts below are isolated test fixtures.
No native runtime, release publication or signed certification is claimed.
"""
from __future__ import annotations

from datetime import date, timedelta
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_dev_kit import installation_contract as contract
from agent_dev_kit import target_contracts
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.installation_plan import create_plan, write_plan
from agent_dev_kit.installation_transaction import apply_plan, rollback
from agent_dev_kit.model import Manifest, ManifestError, sha256_file
from agent_dev_kit.release import build_release
from agent_dev_kit.targets import check_target
from agent_dev_kit.versioning import sync_version_identity


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "skills/adk-requirements-triage/scripts/upgrade-fixture.sh"
ADDED = "skills/adk-requirements-triage/references/candidate-only.txt"


class SourceFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = tempfile.TemporaryDirectory(prefix="adk-upgrade-sources-")
        cls.addClassCleanup(cls.sources.cleanup)
        cls.today = date.today()
        previous_version = Manifest.load(ROOT).version
        major, minor, micro = previous_version.split("-", 1)[0].split("+", 1)[0].split(".")
        candidate_version = "{}.{}.{}".format(major, minor, int(micro) + 1)
        cls.previous = cls.make_source("previous", previous_version, b"previous", 0o644, 1)
        cls.candidate = cls.make_source("candidate", candidate_version, b"candidate", 0o755, 30)

    @classmethod
    def make_source(cls, name, version, label, mode, valid_days):
        source = Path(cls.sources.name) / name
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "*.pyc", "*.egg-info", ".mypy_cache", ".ruff_cache", "dist"
        ))
        sync_version_identity(source, version, "isolated-install-test-fixture")
        for path in (source / "manifests/target-contracts").glob("*.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            value["source"]["retrieved_at"] = (cls.today - timedelta(days=1)).isoformat()
            value["source"]["expires_at"] = (cls.today + timedelta(days=valid_days)).isoformat()
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        script = source / SCRIPT
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_bytes(b"#!/bin/sh\n# " + label + b" fixture\nexit 0\n")
        script.chmod(mode)
        if name == "candidate":
            added = source / ADDED
            added.parent.mkdir(parents=True, exist_ok=True)
            added.write_bytes(b"candidate-only fixture\n")
        return Manifest.load(source)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="adk-upgrade-target-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.target = self.work / "target"
        self.receipt = self.target / contract.RECEIPT_NAME

    def install(self, manifest, previous=None):
        plan = create_plan(manifest, "claude-code", str(self.target), ["core"], [], "copy",
                           previous_manifest=previous)
        self.assertEqual("ready", plan["status"])
        path = self.work / "plan.json"
        write_plan(plan, path)
        result = apply_plan(manifest, path, previous_manifest=previous)
        self.assertEqual("pass", result["status"])
        return result

    def snapshot(self):
        """Capture receipt and managed bytes/modes, independent from rendering."""
        value = json.loads(self.receipt.read_text(encoding="utf-8"))
        names = [item["destination"] for item in value["installed"]] + [contract.RECEIPT_NAME]
        return {name: ((self.target / name).read_bytes(), stat.S_IMODE((self.target / name).stat().st_mode))
                for name in names}

    @staticmethod
    def rewrite_receipt(path, value):
        value["receipt_sha256"] = contract._receipt_digest(value)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    @staticmethod
    def cli(source, *args):
        environment = dict(os.environ, ADK_ROOT=str(source), PYTHONPATH=str(ROOT / "src"))
        return subprocess.run([sys.executable, "-m", "agent_dev_kit.cli", *args],
                              env=environment, capture_output=True, text=True, timeout=120)

    @classmethod
    def clock_after(cls, days):
        class ClockDate(date):
            @classmethod
            def today(clock_cls):
                return cls.today + timedelta(days=days)
        return patch.object(target_contracts, "date", ClockDate)


class InstallUpgradeTest(SourceFixture):
    def test_api_round_trip_restores_different_bytes_modes_and_original_receipt(self):
        self.install(self.previous)
        before = self.snapshot()
        self.assertEqual(0o644, before[SCRIPT][1])
        self.assertEqual(0o600, before[contract.RECEIPT_NAME][1])
        self.install(self.candidate, self.previous)
        upgraded = self.snapshot()
        self.assertNotEqual(before[SCRIPT][0], upgraded[SCRIPT][0])
        self.assertEqual(0o755, upgraded[SCRIPT][1])
        self.assertIn(ADDED, upgraded)
        self.assertEqual("pass", rollback(self.receipt, manifest=self.candidate,
                                          previous_manifest=self.previous)["status"])
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.target / ADDED).exists())
        self.assertEqual("pass", rollback(self.receipt, manifest=self.previous)["status"])
        self.assertFalse(self.receipt.exists())
        self.assertFalse((self.target / SCRIPT).exists())

    def test_cli_requires_previous_source_at_plan_apply_and_rollback(self):
        self.install(self.previous)
        original = self.snapshot()
        path = self.work / "cli-plan.json"
        plan_args = ("install", "plan", "--tool", "claude-code", "--target", str(self.target),
                     "--profile", "core", "--output", str(path), "--summary-json")
        rejected = self.cli(self.candidate.root, *plan_args)
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("trusted ADK manifest identity", rejected.stderr)
        self.assertFalse(path.exists())
        planned = self.cli(self.candidate.root, *plan_args, "--previous-source", str(self.previous.root))
        self.assertEqual(0, planned.returncode, planned.stderr)
        rejected = self.cli(self.candidate.root, "install", "apply", "--plan", str(path))
        self.assertNotEqual(0, rejected.returncode)
        self.assertEqual(original, self.snapshot())
        applied = self.cli(self.candidate.root, "install", "apply", "--plan", str(path),
                           "--previous-source", str(self.previous.root))
        self.assertEqual(0, applied.returncode, applied.stderr)
        upgraded = self.snapshot()
        for previous_args in ((), ("--previous-source", str(self.candidate.root))):
            rejected = self.cli(self.candidate.root, "install", "rollback", "--receipt", str(self.receipt),
                                *previous_args)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("trusted ADK manifest identity", rejected.stderr)
            self.assertEqual(upgraded, self.snapshot())
        restored = self.cli(self.candidate.root, "install", "rollback", "--receipt", str(self.receipt),
                            "--previous-source", str(self.previous.root))
        self.assertEqual(0, restored.returncode, restored.stderr)
        self.assertEqual(original, self.snapshot())

    def test_apply_revalidates_explicit_old_source_after_plan(self):
        self.install(self.previous)
        plan = create_plan(self.candidate, "claude-code", str(self.target), ["core"], [], "copy",
                           previous_manifest=self.previous)
        path = self.work / "reviewed-plan.json"
        write_plan(plan, path)
        altered = self.work / "altered-previous"
        shutil.copytree(self.previous.root, altered)
        (altered / SCRIPT).write_bytes(b"substituted source bytes\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ManifestError, "differs from trusted renderer"):
            apply_plan(self.candidate, path, previous_manifest=Manifest.load(altered))
        self.assertEqual(before, self.snapshot())

    def test_rehashed_backup_bytes_and_changed_permissions_cannot_authorize_restore(self):
        self.install(self.previous)
        self.install(self.candidate, self.previous)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        entry = next(item for item in receipt["installed"] if item["destination"] == SCRIPT)
        backup = self.target / entry["backup"]
        original = backup.read_bytes()
        backup.chmod(0o755)
        before = self.snapshot()
        with self.assertRaisesRegex(ManifestError, "permission mode drifted"):
            rollback(self.receipt, manifest=self.candidate, previous_manifest=self.previous)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(original, backup.read_bytes())
        backup.chmod(0o644)
        backup.write_bytes(b"REHASHED-UNTRUSTED-BACKUP\n")
        entry["backup_sha256"] = sha256_file(backup)
        self.rewrite_receipt(self.receipt, receipt)
        before = self.snapshot()
        with self.assertRaisesRegex(ManifestError, "backup differs from trusted previous asset"):
            rollback(self.receipt, manifest=self.candidate, previous_manifest=self.previous)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(b"REHASHED-UNTRUSTED-BACKUP\n", backup.read_bytes())

    def test_rehashed_previous_receipt_still_requires_trusted_inventory_and_target(self):
        self.install(self.previous)
        self.install(self.candidate, self.previous)
        active = json.loads(self.receipt.read_text(encoding="utf-8"))
        previous_path = self.target / active["previous_receipt"]
        original = json.loads(previous_path.read_text(encoding="utf-8"))
        for changed in ("mode", "target", "omitted-asset"):
            with self.subTest(changed=changed):
                previous = json.loads(json.dumps(original))
                if changed == "mode":
                    previous["installed"][0]["file_mode"] = "0777"
                elif changed == "target":
                    previous["target"] = str(self.work / "other-target")
                else:
                    previous["installed"].pop()
                self.rewrite_receipt(previous_path, previous)
                active["previous_receipt_sha256"] = sha256_file(previous_path)
                self.rewrite_receipt(self.receipt, active)
                before = self.snapshot()
                frozen_previous = previous_path.read_bytes()
                with self.assertRaises(ManifestError):
                    rollback(self.receipt, manifest=self.candidate, previous_manifest=self.previous)
                self.assertEqual(before, self.snapshot())
                self.assertEqual(frozen_previous, previous_path.read_bytes())

    def test_expired_old_contract_allows_upgrade_and_recovery_but_not_new_admission(self):
        self.install(self.previous)
        before = self.snapshot()
        with self.clock_after(2):
            with self.assertRaisesRegex(ManifestError, "target_contract_stale"):
                create_plan(self.previous, "claude-code", str(self.work / "new-target"), ["core"], [], "copy")
            with self.assertRaisesRegex(ManifestError, "target_contract_stale"):
                export_assets(self.previous, target="claude-code", output_root=self.work / "export",
                              profiles=["core"], optional_skills=(), clean=True)
            with self.assertRaisesRegex(ManifestError, "target_contract_stale"):
                check_target(self.previous, "claude-code")
            self.install(self.candidate, self.previous)
            rollback(self.receipt, manifest=self.candidate, previous_manifest=self.previous)
            self.assertEqual(before, self.snapshot())
            rollback(self.receipt, manifest=self.previous)
            self.assertFalse(self.receipt.exists())

    def test_apply_rechecks_candidate_freshness_and_recovery_does_not_rewrite_contract(self):
        self.install(self.previous)
        plan = create_plan(self.candidate, "claude-code", str(self.target), ["core"], [], "copy",
                           previous_manifest=self.previous)
        path = self.work / "expiring-plan.json"
        write_plan(plan, path)
        before = self.snapshot()
        with self.clock_after(31):
            with self.assertRaisesRegex(ManifestError, "target_contract_stale"):
                apply_plan(self.candidate, path, previous_manifest=self.previous)
            self.assertEqual(before, self.snapshot())
        self.install(self.candidate, self.previous)
        changed_source = self.work / "renewed-source"
        shutil.copytree(self.candidate.root, changed_source)
        changed_contract = changed_source / "manifests/target-contracts/claude-code.json"
        value = json.loads(changed_contract.read_text(encoding="utf-8"))
        value["source"]["expires_at"] = (self.today + timedelta(days=60)).isoformat()
        changed_contract.write_text(json.dumps(value) + "\n", encoding="utf-8")
        with self.clock_after(31):
            with self.assertRaisesRegex(ManifestError, "target selection differs"):
                rollback(self.receipt, manifest=Manifest.load(changed_source), previous_manifest=self.previous)
            rollback(self.receipt, manifest=self.candidate, previous_manifest=self.previous)
            self.assertEqual(before, self.snapshot())


class ReleaseUpgradeRehearsalTest(SourceFixture):
    def test_real_artifacts_and_cli_complete_different_version_rehearsal(self):
        artifacts = []
        for manifest in (self.previous, self.candidate):
            environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            for args in (("init", "-q"), ("add", "--all"),
                         ("-c", "user.name=ADK Test Fixture", "-c", "user.email=fixture@adk.invalid",
                          "-c", "commit.gpgsign=false", "commit", "-q", "-m", "isolated upgrade fixture")):
                subprocess.run(["git", "-C", str(manifest.root), *args], env=environment,
                               check=True, capture_output=True, text=True, timeout=60)
            built = build_release(manifest, self.work / manifest.version)
            self.assertEqual("pass", built["status"])
            self.assertTrue(built["release_eligible"])
            artifacts.append(built["artifact"])
        result = self.cli(self.candidate.root, "release", "rehearse", "--previous-artifact", artifacts[0],
                          "--candidate-artifact", artifacts[1], "--summary-json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("pass", report["status"])
        self.assertEqual((self.previous.version, self.candidate.version),
                         (report["previous_version"], report["candidate_version"]))
        self.assertEqual("pass", report["rollback"]["status"])
        self.assertGreater(report["restored_assets"], 0)
        self.assertEqual(report["previous_installed"], report["rollback"]["restored"])
        self.assertGreater(report["candidate_installed"], report["previous_installed"])
        self.assertEqual("not-in-scope", report["remote_publish"])
        rejected = self.cli(self.candidate.root, "release", "rehearse", "--previous-artifact", artifacts[1],
                            "--candidate-artifact", artifacts[0], "--summary-json")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("candidate release must be newer", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
