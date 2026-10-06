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
from agent_dev_kit.installation_transaction import apply_plan, rollback
from agent_dev_kit.installation_transaction import _apply_validated_plan
from agent_dev_kit.installation_plan import create_plan as install_create_plan, write_plan
from agent_dev_kit.maintenance_plan import create_plan
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.strict_json import DEFAULT_MAX_BYTES, StrictJSONError, read as read_json

ROOT = Path(__file__).resolve().parents[1]


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
                    injection = patch.object(contract.tempfile, "NamedTemporaryFile", side_effect=failed_write)
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
            self.assertEqual("pass", rollback(receipt_path)["status"])
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
