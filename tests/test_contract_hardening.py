import json
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from agent_dev_kit import installation_contract as contract
from agent_dev_kit import installation_transaction as transaction
from agent_dev_kit import atomic_io
from agent_dev_kit.installation_transaction import apply_plan, rollback
from agent_dev_kit.installation_transaction import _apply_validated_plan
from agent_dev_kit.installation_plan import create_plan as install_create_plan, write_plan
from agent_dev_kit.maintenance_plan import create_plan
from agent_dev_kit.model import Manifest, ManifestError, sha256_file
from agent_dev_kit.strict_json import DEFAULT_MAX_BYTES, StrictJSONError, read as read_json
from agent_dev_kit.campaign_model import _write_json_atomic, _load_json_object
from agent_dev_kit.locking import TargetLock, target_lock_status, clear_target_lock, LOCK_METADATA
from agent_dev_kit.release import build_release, build_runtime_bundle

ROOT = Path(__file__).resolve().parents[1]


class PersistentDocumentTest(unittest.TestCase):
    def test_runtime_bundle_checksum_link_rejected_and_public_mode_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = Manifest.load(ROOT)
            outside = root / "outside"
            outside.write_bytes(b"SENTINEL")
            checksum = root / ("adk-runtime-core-" + manifest.version + ".tar.gz.sha256")
            checksum.symlink_to(outside)
            with self.assertRaises(ManifestError):
                build_runtime_bundle(manifest, root, "core")
            self.assertTrue(checksum.is_symlink())
            self.assertEqual(b"SENTINEL", outside.read_bytes())
            checksum.unlink()
            result = build_runtime_bundle(manifest, root, "core")
            self.assertEqual("pass", result["status"])
            self.assertEqual(result["sha256"] + "  " + Path(result["artifact"]).name + "\n",
                             checksum.read_text())
            if os.name == "posix":
                self.assertEqual(0o644, checksum.stat().st_mode & 0o777)

    def test_campaign_preserves_fixed_temporary_and_strict_readback(self):
        for kind in ("regular", "symlink", "fifo"):
            if kind == "fifo" and not hasattr(os, "mkfifo"):
                continue
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "record.json"
                fixed = root / "record.json.tmp"
                outside = root / "outside"
                outside.write_bytes(b"SENTINEL")
                if kind == "symlink":
                    fixed.symlink_to(outside)
                elif kind == "fifo":
                    os.mkfifo(fixed)
                else:
                    fixed.write_bytes(b"KEEP")
                identity = fixed.lstat()
                _write_json_atomic(output, {"value": "published"})
                self.assertEqual({"value": "published"}, _load_json_object(output, "fixture"))
                self.assertFalse(output.is_symlink())
                self.assertEqual(b"SENTINEL", outside.read_bytes())
                self.assertEqual(identity.st_ino, fixed.lstat().st_ino)
                if kind == "regular":
                    self.assertEqual(b"KEEP", fixed.read_bytes())

    def test_campaign_invalid_output_rejected_before_mutation(self):
        nested = {"value": 0}
        for _ in range(65):
            nested = {"value": nested}
        for value in ({"value": float("nan")}, {"value": "x" * DEFAULT_MAX_BYTES}, nested, []):
            with self.subTest(value_type=type(value).__name__), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "not-created/record.json"
                with self.assertRaises(ManifestError):
                    _write_json_atomic(output, value)
                self.assertFalse(output.parent.exists())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside.json"
            outside.write_text('{}')
            linked = root / "linked.json"
            linked.symlink_to(outside)
            with self.assertRaises(ManifestError):
                _load_json_object(linked, "fixture")

    def test_campaign_failed_publication_preserves_old_record(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "record.json"
            output.write_bytes(b"OLD")
            with patch.object(atomic_io.os, "replace", side_effect=OSError("failure")):
                with self.assertRaises(OSError):
                    _write_json_atomic(output, {"value": "new"})
            self.assertEqual(b"OLD", output.read_bytes())
            self.assertEqual([], list(output.parent.glob(".record.json.*.tmp")))

    def test_release_checksum_fixed_link_preserved_with_real_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "release"
            output.mkdir()
            manifest = Manifest.load(ROOT)
            outside = root / "outside"
            outside.write_bytes(b"SENTINEL")
            fixed = output / (".agent-dev-kit-" + manifest.version + ".tar.gz.sha256.tmp")
            fixed.symlink_to(outside)
            result = build_release(manifest, output, allow_unbound_snapshot=True)
            checksum = Path(result["checksum"])
            self.assertEqual("pass", result["status"])
            self.assertFalse(checksum.is_symlink())
            self.assertEqual(result["sha256"] + "  " + Path(result["artifact"]).name + "\n",
                             checksum.read_text())
            self.assertEqual(b"SENTINEL", outside.read_bytes())
            self.assertTrue(fixed.is_symlink())
            if os.name == "posix":
                self.assertEqual(0o644, checksum.stat().st_mode & 0o777)


class TargetLockContractTest(unittest.TestCase):
    def test_local_unknown_owner_never_cleared_but_remote_stale_contract_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = TargetLock(Path(temp) / "target", "fixture")
            lock.acquire()
            path = lock.path / LOCK_METADATA
            original = path.read_bytes()
            data = json.loads(original)
            path.write_text(json.dumps(dict(data, created_at="2000-01-01T00:00:00Z")))
            try:
                with patch("agent_dev_kit.locking.os.kill", side_effect=OSError("unknown probe")):
                    status = target_lock_status(lock.target)
                    self.assertIsNone(status["owner_alive"])
                    self.assertTrue(status["stale"])
                    with self.assertRaises(ManifestError):
                        clear_target_lock(lock.target, lock.lock_id)
                self.assertTrue(lock.path.exists())
                path.write_text(json.dumps(dict(data, host="remote.invalid", created_at="2000-01-01T00:00:00Z")))
                self.assertEqual("cleared", clear_target_lock(lock.target, lock.lock_id)["status"])
                self.assertFalse(lock.path.exists())
                lock.acquired = False
            finally:
                if lock.path.exists():
                    path.write_bytes(original)
                    lock.release()

    def test_invalid_timeout_rejected_before_filesystem_mutation(self):
        for value in (float("nan"), float("inf"), -1, 301, True, "1", None, 10 ** 1000):
            with self.subTest(value_type=type(value).__name__), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / "not-created/target"
                with self.assertRaises(ManifestError):
                    TargetLock(target, "fixture", value)
                self.assertFalse(target.parent.exists())

    def test_strict_metadata_invalid_pid_and_timezone_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = TargetLock(Path(temp) / "target", "fixture")
            lock.acquire()
            path = lock.path / LOCK_METADATA
            original = path.read_bytes()
            data = json.loads(original)
            try:
                for pid in (None, True, "1", 0, -1, 10 ** 100):
                    changed = dict(data, pid=pid)
                    path.write_text(json.dumps(changed))
                    with self.assertRaises(ManifestError):
                        target_lock_status(lock.target)
                for raw in ('{"pid":1,' + original.decode()[1:], '{"extra":NaN,' + original.decode()[1:]):
                    path.write_text(raw)
                    with self.assertRaises(ManifestError):
                        target_lock_status(lock.target)
                path.write_text(json.dumps(dict(data, created_at="2026-10-06T00:00:00")))
                with self.assertRaises(ManifestError):
                    target_lock_status(lock.target)
            finally:
                path.write_bytes(original)
                lock.release()

    def test_permission_error_keeps_owner_active_and_refuses_clear(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = TargetLock(Path(temp) / "target", "fixture")
            lock.acquire()
            try:
                with patch("agent_dev_kit.locking.os.kill", side_effect=PermissionError("fixture")):
                    self.assertTrue(target_lock_status(lock.target)["owner_alive"])
                    with self.assertRaises(ManifestError):
                        clear_target_lock(lock.target, lock.lock_id)
                self.assertTrue(lock.path.exists())
            finally:
                lock.release()

    def test_lock_metadata_publication_failure_leaves_no_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = TargetLock(Path(temp) / "target", "fixture")
            with patch.object(atomic_io.os, "fsync", side_effect=OSError("fixture")):
                with self.assertRaises(OSError):
                    lock.acquire()
            self.assertFalse(lock.path.exists())
            self.assertFalse(lock.acquired)


class InstallationJSONTest(unittest.TestCase):
    def test_plan_preserves_preexisting_predictable_temporary_paths(self):
        for kind in ("regular", "symlink", "fifo"):
            if kind == "fifo" and not hasattr(os, "mkfifo"):
                continue
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "plan.json"
                previous = root / "plan.json.tmp"
                outside = root / "outside"
                outside.write_bytes(b"SENTINEL")
                if kind == "symlink":
                    previous.symlink_to(outside)
                elif kind == "fifo":
                    os.mkfifo(previous)
                else:
                    previous.write_bytes(b"KEEP")
                identity = previous.lstat()
                write_plan({"value": "published"}, output)
                self.assertFalse(output.is_symlink())
                self.assertEqual({"value": "published"}, read_json(output, regular_only=True))
                self.assertEqual(b"SENTINEL", outside.read_bytes())
                self.assertEqual((identity.st_ino, identity.st_mode),
                                 (previous.lstat().st_ino, previous.lstat().st_mode))
                if kind == "regular":
                    self.assertEqual(b"KEEP", previous.read_bytes())
                if os.name == "posix":
                    self.assertEqual(0o600, output.stat().st_mode & 0o777)
                self.assertEqual([], list(root.glob(".plan.json.*.tmp")))

    def test_plan_rejects_output_link_without_overwriting_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside"
            outside.write_bytes(b"SENTINEL")
            output = root / "plan.json"
            output.symlink_to(outside)
            with self.assertRaises(ManifestError):
                write_plan({"value": "blocked"}, output)
            self.assertTrue(output.is_symlink())
            self.assertEqual(b"SENTINEL", outside.read_bytes())

    def test_plan_write_sync_and_publication_failures_preserve_old_document(self):
        original_temporary = tempfile.NamedTemporaryFile

        @contextmanager
        def failed_write(*args, **kwargs):
            with original_temporary(*args, **kwargs) as stream:
                yield SimpleNamespace(name=stream.name, write=Mock(side_effect=OSError("write failure")))

        for fault in ("write", "fsync", "replace"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                output = root / "plan.json"
                output.write_bytes(b"OLD")
                fixed = root / "plan.json.tmp"
                fixed.write_bytes(b"KEEP")
                if fault == "write":
                    injection = patch.object(atomic_io.tempfile, "NamedTemporaryFile", side_effect=failed_write)
                else:
                    injection = patch.object(contract.os, fault, side_effect=OSError("publication failure"))
                with injection, self.assertRaises(OSError):
                    write_plan({"value": "new"}, output)
                self.assertEqual(b"OLD", output.read_bytes())
                self.assertEqual(b"KEEP", fixed.read_bytes())
                self.assertEqual([], list(root.glob(".plan.json.*.tmp")))

    def test_receipt_preserves_predictable_link_and_remains_readable_and_reversible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            outside = root / "outside"
            outside.write_bytes(b"SENTINEL")
            fixed = target / (contract.RECEIPT_NAME + ".tmp")
            fixed.symlink_to(outside)
            manifest = Manifest.load(ROOT)
            plan = install_create_plan(manifest, "claude-code", str(target), ("core",), (), "copy",
                                       asset_kind="agent")
            plan_path = root / "plan.json"
            write_plan(plan, plan_path)
            result = apply_plan(manifest, plan_path)
            self.assertEqual("pass", result["status"])
            self.assertEqual(5, result["installed"])
            receipt_path = target / contract.RECEIPT_NAME
            self.assertFalse(receipt_path.is_symlink())
            contract._read_receipt(receipt_path, "fixture")
            self.assertEqual(b"SENTINEL", outside.read_bytes())
            self.assertTrue(fixed.is_symlink())
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])
            self.assertTrue(fixed.is_symlink())
            self.assertEqual(b"SENTINEL", outside.read_bytes())

    def test_receipt_publication_failure_restores_assets_and_previous_receipt(self):
        for fault in ("fsync", "replace"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                target = root / "target"
                manifest = Manifest.load(ROOT)
                plan_path = root / "plan.json"
                def plan_install():
                    write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                                  "copy", asset_kind="agent"), plan_path)
                plan_install()
                apply_plan(manifest, plan_path)
                receipt_path = target / contract.RECEIPT_NAME
                previous = receipt_path.read_bytes()
                assets = {path: path.read_bytes() for path in (target / "agents").glob("*.md")}
                fixed = target / (contract.RECEIPT_NAME + ".tmp")
                fixed.write_bytes(b"KEEP")
                plan_install()
                original_writer = contract._write_document
                def fail_receipt(text, output):
                    with patch.object(contract.os, fault, side_effect=OSError("receipt publication failure")):
                        return original_writer(text, output)
                with patch.object(contract, "_write_document", side_effect=fail_receipt):
                    with self.assertRaises(OSError):
                        apply_plan(manifest, plan_path)
                self.assertEqual(previous, receipt_path.read_bytes())
                self.assertEqual(assets, {path: path.read_bytes() for path in (target / "agents").glob("*.md")})
                self.assertEqual(b"KEEP", fixed.read_bytes())
                self.assertEqual([], list(target.glob("." + contract.RECEIPT_NAME + ".*.tmp")))
                contract._read_receipt(receipt_path, "previous fixture")

    def test_plan_cannot_forge_replacement_of_unmanaged_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            value = install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                        "copy", asset_kind="agent")
            self.assertEqual("ready", value["status"])
            operation = value["operations"][0]
            destination = target / operation["destination"]
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"UNMANAGED-SENTINEL")
            operation["action"] = "replace-managed"
            operation["destination_sha256"] = sha256_file(destination)
            plan_path = root / "forged-plan.json"
            write_plan(value, plan_path)
            with self.assertRaisesRegex(ManifestError, "unmanaged destination"):
                apply_plan(manifest, plan_path)
            self.assertEqual(b"UNMANAGED-SENTINEL", destination.read_bytes())
            self.assertFalse((target / contract.RECEIPT_NAME).exists())
            self.assertFalse((target / ".adk-staging").exists())

    def test_plan_cannot_rehash_managed_drift_to_overwrite_active_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            value = install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                        "copy", asset_kind="agent")
            write_plan(value, plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt_path = target / contract.RECEIPT_NAME
            receipt_before = receipt_path.read_bytes()
            replan = install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                         "copy", asset_kind="agent")
            self.assertEqual("ready", replan["status"])
            operation = replan["operations"][0]
            destination = target / operation["destination"]
            destination.write_bytes(b"DRIFTED-MANAGED-SENTINEL")
            operation["destination_sha256"] = sha256_file(destination)
            write_plan(replan, plan_path)
            with self.assertRaisesRegex(ManifestError, "active receipt"):
                apply_plan(manifest, plan_path)
            self.assertEqual(b"DRIFTED-MANAGED-SENTINEL", destination.read_bytes())
            self.assertEqual(receipt_before, receipt_path.read_bytes())
            # A successful earlier apply leaves the empty staging parent.
            self.assertEqual([], list((target / ".adk-staging").iterdir()))

    def test_plan_cannot_reclassify_missing_managed_file_as_create(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            value = install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                        "copy", asset_kind="agent")
            write_plan(value, plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt_path = target / contract.RECEIPT_NAME
            receipt_before = receipt_path.read_bytes()
            replan = install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                         "copy", asset_kind="agent")
            operation = replan["operations"][0]
            destination = target / operation["destination"]
            destination.unlink()
            operation["action"] = "create"
            operation["destination_sha256"] = None
            write_plan(replan, plan_path)
            with self.assertRaisesRegex(ManifestError, "active managed asset"):
                apply_plan(manifest, plan_path)
            self.assertFalse(destination.exists())
            self.assertEqual(receipt_before, receipt_path.read_bytes())

    def test_rollback_rejects_rehashed_unmanaged_inventory_even_with_valid_backup_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt_path = target / contract.RECEIPT_NAME
            receipt = json.loads(receipt_path.read_text())
            unrelated = target / "personal" / "private.txt"
            unrelated.parent.mkdir()
            unrelated.write_bytes(b"UNMANAGED-SENTINEL")
            injected = dict(receipt["installed"][0])
            injected["destination"] = unrelated.relative_to(target).as_posix()
            injected["installed_sha256"] = sha256_file(unrelated)
            injected["rendered_sha256"] = injected["installed_sha256"]
            injected["backup"] = None
            injected["backup_sha256"] = None
            receipt["installed"].append(injected)
            receipt["receipt_sha256"] = contract._receipt_digest(receipt)
            receipt_path.write_text(json.dumps(receipt) + "\n")
            before = receipt_path.read_bytes()
            with self.assertRaisesRegex(ManifestError, "inventory does not match trusted rendered assets"):
                rollback(receipt_path, manifest=manifest)
            self.assertEqual(b"UNMANAGED-SENTINEL", unrelated.read_bytes())
            self.assertEqual(before, receipt_path.read_bytes())
            self.assertFalse((target / ".adk-rollback-staging").exists())

    def test_rollback_rejects_asset_path_substitution_and_manifest_version_drift(self):
        for mutation, error in (("destination", "unauthorized"), ("manifest", "manifest identity")):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                target = root / "target"
                manifest = Manifest.load(ROOT)
                plan_path = root / "plan.json"
                write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                               "copy", asset_kind="agent"), plan_path)
                self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
                receipt_path = target / contract.RECEIPT_NAME
                receipt = json.loads(receipt_path.read_text())
                managed = target / receipt["installed"][0]["destination"]
                old_bytes = managed.read_bytes()
                unrelated = target / "private-duplicate.md"
                unrelated.write_bytes(old_bytes)
                if mutation == "destination":
                    receipt["installed"][0]["destination"] = unrelated.relative_to(target).as_posix()
                else:
                    receipt["manifest_version"] = "0.0.0"
                receipt["receipt_sha256"] = contract._receipt_digest(receipt)
                receipt_path.write_text(json.dumps(receipt) + "\n")
                with self.assertRaisesRegex(ManifestError, error):
                    rollback(receipt_path, manifest=manifest)
                self.assertEqual(old_bytes, managed.read_bytes())
                self.assertEqual(old_bytes, unrelated.read_bytes())

    def test_rollback_requires_explicit_trusted_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt_path = target / contract.RECEIPT_NAME
            with self.assertRaises(TypeError):
                rollback(receipt_path)
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])

    def test_rollback_refuses_rehashed_receipt_that_deletes_unmanaged_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            managed = target / "agents" / "requirements-analyst.md"
            managed_before = managed.read_bytes()
            unrelated = target / "private-unmanaged"
            unrelated.mkdir()
            secret = unrelated / "do-not-delete.txt"
            secret.write_bytes(b"UNMANAGED-SENTINEL")
            receipt_path = target / contract.RECEIPT_NAME
            receipt = json.loads(receipt_path.read_text())
            receipt["backup_root"] = unrelated.relative_to(target).as_posix()
            receipt["receipt_sha256"] = contract._receipt_digest(receipt)
            receipt_path.write_text(json.dumps(receipt) + "\n")
            changed_receipt = receipt_path.read_bytes()
            with self.assertRaisesRegex(ManifestError, "backup root does not match receipt identity"):
                rollback(receipt_path, manifest=manifest)
            self.assertEqual(managed_before, managed.read_bytes())
            self.assertEqual(b"UNMANAGED-SENTINEL", secret.read_bytes())
            self.assertEqual(changed_receipt, receipt_path.read_bytes())
            self.assertEqual([], list((target / ".adk-rollback-staging").iterdir()) if (target / ".adk-rollback-staging").exists() else [])

    def test_rollback_refuses_rehashed_unmanaged_backup_or_previous_receipt(self):
        for attack in ("backup", "previous-receipt"):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                target = root / "target"
                manifest = Manifest.load(ROOT)
                plan_path = root / "plan.json"
                def apply():
                    write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                                   "copy", asset_kind="agent"), plan_path)
                    self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
                apply()
                apply()
                receipt_path = target / contract.RECEIPT_NAME
                receipt = json.loads(receipt_path.read_text())
                managed = target / "agents" / "requirements-analyst.md"
                managed_before = managed.read_bytes()
                if attack == "backup":
                    item = next(a for a in receipt["installed"] if a["backup"])
                    original = target / item["backup"]
                    unmanaged = target / "other-unmanaged-backup.md"
                    unmanaged.write_bytes(original.read_bytes())
                    item["backup"] = unmanaged.relative_to(target).as_posix()
                    expected_error = "rollback backup path does not match managed asset identity"
                else:
                    original = target / receipt["previous_receipt"]
                    unmanaged = target / "other-unmanaged-receipt.json"
                    unmanaged.write_bytes(original.read_bytes())
                    receipt["previous_receipt"] = unmanaged.relative_to(target).as_posix()
                    expected_error = "rollback previous receipt path does not match run identity"
                receipt["receipt_sha256"] = contract._receipt_digest(receipt)
                receipt_path.write_text(json.dumps(receipt) + "\n")
                changed_receipt = receipt_path.read_bytes()
                with self.assertRaisesRegex(ManifestError, expected_error):
                    rollback(receipt_path, manifest=manifest)
                self.assertEqual(managed_before, managed.read_bytes())
                self.assertEqual(original.read_bytes(), unmanaged.read_bytes())
                self.assertEqual(changed_receipt, receipt_path.read_bytes())

    def test_rollback_refuses_rehashed_noncanonical_run_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt_path = target / contract.RECEIPT_NAME
            receipt = json.loads(receipt_path.read_text())
            receipt["receipt_id"] = "."
            receipt["backup_root"] = ".adk-backups/."
            receipt["receipt_sha256"] = contract._receipt_digest(receipt)
            receipt_path.write_text(json.dumps(receipt) + "\n")
            with self.assertRaisesRegex(ManifestError, "canonical install run identifier"):
                rollback(receipt_path, manifest=manifest)
            self.assertTrue((target / "agents" / "requirements-analyst.md").is_file())

    def test_managed_update_rejects_internal_file_symlink_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            def plan():
                value = install_create_plan(
                    manifest, "claude-code", str(target), ("core",), (),
                    "copy", asset_kind="agent"
                )
                write_plan(value, plan_path)
                return value
            plan()
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            original_receipt = (target / contract.RECEIPT_NAME).read_bytes()
            next_plan = plan()
            self.assertEqual("ready", next_plan["status"])
            managed = target / "agents" / "requirements-analyst.md"
            unmanaged = target / "unmanaged-duplicate.md"
            unmanaged.write_bytes(managed.read_bytes())
            unmanaged.chmod(0o600)
            original_bytes = unmanaged.read_bytes()
            managed.unlink()
            managed.symlink_to(unmanaged)
            # Before this fix, apply returned PASS and chmod'd unmanaged
            # 0600 -> 0644 while the active receipt named a different file.
            with self.assertRaisesRegex(ManifestError, "symlink aliases"):
                apply_plan(manifest, plan_path)
            with self.assertRaisesRegex(ManifestError, "symlink aliases"):
                install_create_plan(
                    manifest, "claude-code", str(target), ("core",), (),
                    "copy", asset_kind="agent"
                )
            with self.assertRaisesRegex(ManifestError, "symlink aliases"):
                rollback(target / contract.RECEIPT_NAME, manifest=manifest)
            self.assertEqual(original_bytes, unmanaged.read_bytes())
            self.assertEqual(0o600, unmanaged.stat().st_mode & 0o777)
            self.assertTrue(managed.is_symlink())
            self.assertEqual(original_receipt, (target / contract.RECEIPT_NAME).read_bytes())

    def test_managed_update_rejects_internal_directory_symlink_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            def plan():
                value = install_create_plan(
                    manifest, "claude-code", str(target), ("core",), (),
                    "copy", asset_kind="agent"
                )
                write_plan(value, plan_path)
                return value
            plan()
            self.assertEqual("pass", apply_plan(manifest, plan_path)["status"])
            receipt = target / contract.RECEIPT_NAME
            receipt_before = receipt.read_bytes()
            plan()
            managed_dir = target / "agents"
            elsewhere = target / "aliased-agents"
            managed_dir.rename(elsewhere)
            managed_dir.symlink_to(elsewhere, target_is_directory=True)
            before = {p.name: p.read_bytes() for p in elsewhere.iterdir()}
            with self.assertRaisesRegex(ManifestError, "symlink aliases"):
                apply_plan(manifest, plan_path)
            with self.assertRaisesRegex(ManifestError, "symlink aliases"):
                rollback(receipt, manifest=manifest)
            self.assertEqual(before, {p.name: p.read_bytes() for p in elsewhere.iterdir()})
            self.assertEqual(receipt_before, receipt.read_bytes())

    def test_backup_digest_failure_restores_asset_and_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            def install():
                write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                               "copy", asset_kind="agent"), plan_path)
                return apply_plan(manifest, plan_path)
            install()
            receipt_path = target / contract.RECEIPT_NAME
            old_receipt = receipt_path.read_bytes()
            assets = {path: path.read_bytes() for path in (target / "agents").glob("*.md")}
            real_sha256_tree = transaction.sha256_tree
            def fail_backup_digest(path):
                if ".adk-backups" in Path(path).parts:
                    raise OSError("simulated backup digest failure")
                return real_sha256_tree(path)
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            with patch.object(transaction, "sha256_tree", side_effect=fail_backup_digest):
                with self.assertRaisesRegex(OSError, "backup digest failure"):
                    apply_plan(manifest, plan_path)
            self.assertEqual(old_receipt, receipt_path.read_bytes())
            self.assertEqual(assets, {path: path.read_bytes() for path in (target / "agents").glob("*.md")})
            self.assertEqual([], list((target / ".adk-backups").rglob("*.md")))
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])

    def test_rollback_second_compensation_failure_retains_staged_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            def install():
                write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                               "copy", asset_kind="agent"), plan_path)
                return apply_plan(manifest, plan_path)
            install()
            install()
            receipt_path = target / contract.RECEIPT_NAME
            receipt = contract._read_receipt(receipt_path, "fixture")
            real_replace = os.replace
            def fault(src, dst):
                if Path(dst) == receipt_path:
                    raise OSError("simulated receipt publication failure")
                if ".adk-rollback-staging" in Path(src).parts:
                    raise OSError("simulated second compensation failure")
                return real_replace(src, dst)
            with patch.object(transaction.os, "replace", side_effect=fault):
                with self.assertRaisesRegex(OSError, "second compensation failure"):
                    rollback(receipt_path, manifest=manifest)
            staged = target / ".adk-rollback-staging" / str(receipt["receipt_id"])
            self.assertTrue(staged.is_dir())
            self.assertEqual(len(receipt["installed"]), len(list(staged.rglob("*.md"))))
            self.assertEqual(receipt["receipt_sha256"], contract._read_receipt(receipt_path, "fixture")["receipt_sha256"])
            for item in receipt["installed"]:
                self.assertTrue((staged / item["destination"]).is_file())
            # Unresolved transactions must retain their recovery material, not
            # silently clear staging and thereby pretend that rollback succeeded.
            with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
                install()
            with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
                rollback(receipt_path, manifest=manifest)
            self.assertEqual(len(receipt["installed"]), len(list(staged.rglob("*.md"))))

    def test_failed_install_compensation_preserves_staging_and_blocks_new_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            plan_path = root / "plan.json"
            def install():
                write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                               "copy", asset_kind="agent"), plan_path)
                return apply_plan(manifest, plan_path)
            install()
            receipt_path = target / contract.RECEIPT_NAME
            original_receipt = receipt_path.read_bytes()
            real_replace = os.replace
            real_hash = transaction.sha256_tree
            def failing_digest(path):
                if ".adk-backups" in Path(path).parts:
                    raise OSError("simulated digest read failure")
                return real_hash(path)
            def failing_restore(src, dst):
                if ".adk-backups" in Path(src).parts:
                    raise OSError("simulated restoration failure")
                return real_replace(src, dst)
            write_plan(install_create_plan(manifest, "claude-code", str(target), ("core",), (),
                                           "copy", asset_kind="agent"), plan_path)
            with patch.object(transaction, "sha256_tree", side_effect=failing_digest), \
                 patch.object(transaction.os, "replace", side_effect=failing_restore):
                with self.assertRaisesRegex(OSError, "restoration failure"):
                    apply_plan(manifest, plan_path)
            staging_runs = list((target / ".adk-staging").iterdir())
            self.assertEqual(1, len(staging_runs))
            self.assertTrue(staging_runs[0].is_dir())
            backup_runs = [
                run for run in (target / ".adk-backups").iterdir()
                if list(run.rglob("*.md"))
            ]
            self.assertEqual(1, len(backup_runs))
            self.assertEqual(original_receipt, receipt_path.read_bytes())
            with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
                apply_plan(manifest, plan_path)
            with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
                rollback(receipt_path, manifest=manifest)
            self.assertEqual(original_receipt, receipt_path.read_bytes())
            self.assertTrue(list(backup_runs[0].rglob("*.md")))

    def test_document_producer_readback_and_write_rejection(self):
        data = {"schema": contract.RECEIPT_SCHEMA, "receipt_id": "fixture", "installed": [],
                "padding": "", "receipt_sha256": "0" * 64}
        overhead = len((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())
        data["padding"] = "x" * (DEFAULT_MAX_BYTES - overhead)
        data["receipt_sha256"] = contract._receipt_digest(data)
        text = contract._encode_document(data, "fixture")
        self.assertEqual(DEFAULT_MAX_BYTES, len(text.encode()))
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "receipt.json"
            receipt.write_text(text)
            self.assertEqual("fixture", contract._read_receipt(receipt, "fixture")["receipt_id"])
            output = Path(temp) / "new-dir/plan.json"
            data["padding"] += "x"
            with self.assertRaises(ManifestError):
                write_plan(data, output)
            self.assertFalse(output.parent.exists())
            with self.assertRaises(ManifestError):
                write_plan({"value": float("nan")}, output)

    def test_receipt_preview_budget_rejected_before_asset_mutation(self):
        files = []
        operations = []
        for index in range(8000):
            destination = "skills/fixture/references/record-%05d.md" % index
            files.append(SimpleNamespace(destination=destination, source=destination, kind="skill",
                                         name="fixture", sha256="a" * 64, mode=0o644))
            operations.append({"destination": destination, "source_sha256": "b" * 64})
        plan = {"plan_id": "fixture-id", "tool": "claude-code", "operations": operations}
        self.assertLess(len(contract._encode_document(plan, "plan").encode()), DEFAULT_MAX_BYTES)
        bundle = SimpleNamespace(files=files, contract=SimpleNamespace(digest="c" * 64),
                                 resolution=SimpleNamespace(profiles=("core",)),
                                 optional_skills=(), asset_kind="skill")
        manifest = SimpleNamespace(version="8.0.0", digest="d" * 64)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "not-created"
            with self.assertRaisesRegex(ManifestError, "receipt preview"):
                _apply_validated_plan(manifest, plan, target, bundle)
            self.assertFalse(target.exists())

    def test_open_time_leaf_replacement_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "input.json"
            outside = root / "outside.json"
            outside.write_text('{}')
            original_open = os.open
            replacements = ("symlink", "fifo") if hasattr(os, "mkfifo") else ("symlink",)
            for replacement in replacements:
                path.write_text('{}')

                def replace_then_open(name, flags):
                    path.unlink()
                    if replacement == "fifo":
                        os.mkfifo(path)
                    else:
                        path.symlink_to(outside)
                    return original_open(name, flags)

                with patch("agent_dev_kit.strict_json.os.open", side_effect=replace_then_open):
                    with self.assertRaises(StrictJSONError):
                        read_json(path, regular_only=True)
                path.unlink()

    def test_receipt_duplicate_nonfinite_and_budgets(self):
        data = {"schema": contract.RECEIPT_SCHEMA, "receipt_id": "fixture", "installed": []}
        data["receipt_sha256"] = contract._receipt_digest(data)
        valid = json.dumps(data)
        with tempfile.TemporaryDirectory() as temp:
            receipt = Path(temp) / "receipt.json"
            receipt.write_text(valid)
            self.assertEqual("fixture", contract._read_receipt(receipt, "fixture")["receipt_id"])
            for raw in ('{"schema":"wrong",' + valid[1:], '{"extra":NaN,' + valid[1:],
                        '{"extra":1e9999,' + valid[1:], '[' * 65 + '0' + ']' * 65,
                        ' ' * (4 * 1024 * 1024 + 1)):
                receipt.write_text(raw)
                with self.assertRaises(ManifestError):
                    contract._read_receipt(receipt, "fixture")

    def test_plan_rejected_before_lock_or_target_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target"
            plan = Path(temp) / "plan.json"
            valid = json.dumps({"target": str(target)})
            for raw in ('{"target":"wrong",' + valid[1:], '{"extra":NaN,' + valid[1:],
                        '[' * 65 + '0' + ']' * 65, ' ' * (4 * 1024 * 1024 + 1)):
                plan.write_text(raw)
                with patch("agent_dev_kit.installation_transaction.TargetLock") as lock:
                    with self.assertRaises(ManifestError):
                        apply_plan(Manifest.load(ROOT), plan)
                    lock.assert_not_called()
                self.assertFalse(target.exists())

    def test_special_and_link_inputs_rejected_without_opening(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            regular = root / "regular.json"
            regular.write_text("{}")
            linked = root / "link.json"
            linked.symlink_to(regular)
            with self.assertRaises(ManifestError):
                apply_plan(Manifest.load(ROOT), linked)
            with self.assertRaises(ManifestError):
                contract._read_receipt(linked, "fixture")
            if hasattr(os, "mkfifo"):
                fifo = root / "fifo"
                os.mkfifo(fifo)
                with self.assertRaises(ManifestError):
                    apply_plan(Manifest.load(ROOT), fifo)
                with self.assertRaises(ManifestError):
                    contract._read_receipt(fifo, "fixture")


class MaintenancePlanTest(unittest.TestCase):
    def test_directory_replacement_cannot_traverse_outside(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifest.json").write_text("{}")
            cache = root / ".cache"
            cache.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret").write_text("preserve")
            original_open = os.open

            def replace_then_open(name, flags, **kwargs):
                if name == ".cache":
                    cache.rename(root / "old-cache")
                    cache.symlink_to(outside, target_is_directory=True)
                return original_open(name, flags, **kwargs)

            with patch("agent_dev_kit.maintenance_plan.os.open", side_effect=replace_then_open) as opened:
                with patch("agent_dev_kit.maintenance_plan.os.supports_dir_fd", os.supports_dir_fd | {opened}):
                    with self.assertRaises(OSError):
                        create_plan(root)

    def test_cli_apply_rejected_consistently_without_mutation(self):
        for script, command in (("performance.sh", "optimize"), ("auto-ops.sh", "cleanup"),
                                ("auto-ops.sh", "optimize"), ("auto-ops.sh", "monthly")):
            result = subprocess.run(["bash", str(ROOT / "scripts" / script), command,
                                     "--apply", "--summary-json"], text=True, capture_output=True)
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual("blocked", data["status"])
            self.assertFalse(data["applied"])
            self.assertFalse(data["execution_supported"])

    def test_report_summary_written_matches_actual_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.md"
            result = subprocess.run(["bash", str(ROOT / "scripts/performance.sh"), "report",
                                     "--summary-json", "--out", str(output)], text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(1, json.loads(result.stdout)["written"])
            self.assertTrue(output.read_text().startswith("# 性能报告"))

    def test_inventory_is_readonly_and_preserves_protected_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifest.json").write_text("{}")
            cached = root / ".cache/regular.tmp"
            cached.parent.mkdir()
            cached.write_text("keep")
            cached.chmod(0o600)
            protected = root / ".cache/local-ci/evidence.json"
            protected.parent.mkdir()
            protected.write_text("preserve")
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret").write_text("untouched")
            (root / ".cache/link").symlink_to(outside, target_is_directory=True)
            result = create_plan(root, "advanced")
            paths = [item["path"] for item in result["candidates"]]
            self.assertIn(".cache/regular.tmp", paths)
            self.assertNotIn(".cache/local-ci/evidence.json", paths)
            self.assertNotIn(".cache/link/secret", paths)
            self.assertFalse(result["applied"])
            self.assertFalse(result["execution_supported"])
            self.assertEqual("keep", cached.read_text())
            self.assertEqual(0o600, cached.stat().st_mode & 0o777)

    def test_inventory_budget_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifest.json").write_text("{}")
            (root / ".cache").mkdir()
            for index in range(4):
                (root / ".cache" / str(index)).write_text("keep")
            with patch("agent_dev_kit.maintenance_plan.MAX_ENTRIES", 3):
                with self.assertRaises(ManifestError):
                    create_plan(root)


class RuntimeScanTest(unittest.TestCase):
    def test_scan_error_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temp:
            bin_dir = Path(temp)
            scanner = bin_dir / "rg"
            scanner.write_text("#!/bin/sh\nexit 2\n")
            scanner.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
            result = subprocess.run(["bash", str(ROOT / "scripts/check-runtime-boundary.sh"), "--summary-json"],
                                    env=env, text=True, capture_output=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual("fail", json.loads(result.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
