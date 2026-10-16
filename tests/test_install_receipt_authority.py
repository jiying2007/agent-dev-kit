"""Receipt authority and backup cleanup regressions."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_dev_kit import installation_contract as contract
from agent_dev_kit import installation_transaction as transaction
from agent_dev_kit.installation_plan import create_plan, write_plan
from agent_dev_kit.installation_transaction import apply_plan, rollback
from agent_dev_kit.model import Manifest, ManifestError, sha256_file
from agent_dev_kit.targets import render_selection

ROOT = Path(__file__).resolve().parents[1]


class ReceiptAuthorityTest(unittest.TestCase):
    @staticmethod
    def install(manifest: Manifest, root: Path, target: Path) -> Path:
        path = root / "plan.json"
        write_plan(create_plan(manifest, "claude-code", str(target), ("core",), (),
                               "copy", asset_kind="agent"), path)
        assert apply_plan(manifest, path)["status"] == "pass"
        return target / contract.RECEIPT_NAME

    def test_forged_active_receipt_cannot_authorize_unmanaged_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            receipt_path = self.install(manifest, root, target)
            selection = render_selection(manifest, "claude-code", ("core",), (), "skill")
            self.assertTrue(selection.files)
            unmanaged = target / selection.files[0].destination
            unmanaged.parent.mkdir(parents=True, exist_ok=True)
            unmanaged.write_bytes(b"UNMANAGED-SENTINEL")
            receipt = json.loads(receipt_path.read_text())
            receipt["asset_kind"] = "skill"
            receipt["installed"] = [{"destination": selection.files[0].destination,
                                      "installed_sha256": sha256_file(unmanaged)}]
            receipt["receipt_sha256"] = contract._receipt_digest(receipt)
            receipt_path.write_text(json.dumps(receipt) + "\n")
            with self.assertRaisesRegex(ManifestError, "trusted rendered assets"):
                create_plan(manifest, "claude-code", str(target), ("core",), (),
                            "copy", asset_kind="skill")
            self.assertEqual(b"UNMANAGED-SENTINEL", unmanaged.read_bytes())

    def test_apply_revalidates_rehashed_current_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            receipt_path = self.install(manifest, root, target)
            plan = create_plan(manifest, "claude-code", str(target), ("core",), (),
                               "copy", asset_kind="agent")
            receipt = json.loads(receipt_path.read_text())
            receipt["manifest_sha256"] = "0" * 64
            receipt["receipt_sha256"] = contract._receipt_digest(receipt)
            receipt_path.write_text(json.dumps(receipt) + "\n")
            plan["active_receipt_sha256"] = sha256_file(receipt_path)
            write_plan(plan, root / "rebound-plan.json")
            tracked = target / plan["operations"][0]["destination"]
            before = tracked.read_bytes()
            with self.assertRaisesRegex(ManifestError, "trusted ADK manifest identity"):
                apply_plan(manifest, root / "rebound-plan.json")
            self.assertEqual(before, tracked.read_bytes())

    def test_rollback_omission_and_unlisted_backup_fail_closed(self):
        for mode in ("omit-asset", "omit-receipt", "extra-file", "extra-directory"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                target = root / "target"
                manifest = Manifest.load(ROOT)
                self.install(manifest, root, target)
                receipt_path = self.install(manifest, root, target)
                receipt = json.loads(receipt_path.read_text())
                backup_root = target / receipt["backup_root"]
                managed = {a["destination"]: (target / a["destination"]).read_bytes()
                           for a in receipt["installed"]}
                if mode == "omit-asset":
                    entry = next(a for a in receipt["installed"] if a["backup"])
                    preserved = target / entry["backup"]
                    entry["backup"] = entry["backup_sha256"] = None
                elif mode == "omit-receipt":
                    preserved = target / receipt["previous_receipt"]
                    receipt["previous_receipt"] = receipt["previous_receipt_sha256"] = None
                elif mode == "extra-file":
                    preserved = backup_root / "unlisted.txt"
                    preserved.write_bytes(b"UNMANAGED-SENTINEL")
                else:
                    preserved = backup_root / "unlisted-dir"
                    preserved.mkdir()
                if mode.startswith("omit"):
                    receipt["receipt_sha256"] = contract._receipt_digest(receipt)
                    receipt_path.write_text(json.dumps(receipt) + "\n")
                frozen = receipt_path.read_bytes()
                with self.assertRaisesRegex(ManifestError, "backup inventory"):
                    rollback(receipt_path, manifest=manifest)
                self.assertEqual(frozen, receipt_path.read_bytes())
                for relative, data in managed.items():
                    self.assertEqual(data, (target / relative).read_bytes())
                self.assertTrue(preserved.exists())

    def test_two_level_rollback_restores_previous_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root, target = Path(temp), Path(temp) / "target"
            manifest = Manifest.load(ROOT)
            receipt_path = self.install(manifest, root, target)
            old_receipt = receipt_path.read_bytes()
            self.install(manifest, root, target)
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])
            self.assertEqual(old_receipt, receipt_path.read_bytes())
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])
            self.assertFalse(receipt_path.exists())

    def test_locked_target_must_match_receipt_on_second_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root, target = Path(temp), Path(temp) / "target"
            manifest = Manifest.load(ROOT)
            receipt_path = self.install(manifest, root, target)
            frozen = receipt_path.read_bytes()
            with self.assertRaisesRegex(ManifestError, "target changed after acquiring target lock"):
                transaction._rollback_locked(receipt_path, manifest, locked_target=root / "other")
            self.assertEqual(frozen, receipt_path.read_bytes())

    def test_managed_permission_drift_is_not_hidden_by_content_hash(self):
        from agent_dev_kit.model import sha256_tree
        from agent_dev_kit.installation_plan import validate_plan
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            receipt_path = self.install(manifest, root, target)
            receipt = json.loads(receipt_path.read_text())
            record = receipt["installed"][0]
            destination = target / record["destination"]
            original = int(record["file_mode"], 8)
            self.assertEqual(destination.stat().st_mode & 0o7777, original)
            plan = create_plan(manifest, "claude-code", str(target), ("core",), (),
                               "copy", asset_kind="agent")
            old_hash = sha256_tree(destination)
            altered = original ^ 0o022
            destination.chmod(altered)
            self.assertEqual(old_hash, sha256_tree(destination))
            try:
                review_plan = create_plan(manifest, "claude-code", str(target), ("core",), (),
                                          "copy", asset_kind="agent")
                self.assertEqual(review_plan["status"], "needs-review")
                self.assertTrue(any(
                    conflict["destination"] == record["destination"]
                    and "permission" in conflict["reason"]
                    for conflict in review_plan["conflicts"]
                ))
                with self.assertRaisesRegex(ManifestError, "permission mode drifted"):
                    validate_plan(manifest, plan)
                with self.assertRaisesRegex(ManifestError, "permission mode drifted"):
                    rollback(receipt_path, manifest=manifest)
                self.assertEqual(old_hash, sha256_tree(destination))
                self.assertTrue(receipt_path.exists())
            finally:
                destination.chmod(original)
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])

    def test_modified_backup_permissions_block_restore_without_data_loss(self):
        from agent_dev_kit.model import sha256_tree
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            manifest = Manifest.load(ROOT)
            self.install(manifest, root, target)
            receipt_path = self.install(manifest, root, target)
            receipt = json.loads(receipt_path.read_text())
            record = next(item for item in receipt["installed"] if item["backup"])
            backup = target / record["backup"]
            original = int(record["file_mode"], 8)
            before = sha256_tree(backup)
            backup.chmod(original ^ 0o022)
            self.assertEqual(before, sha256_tree(backup))
            try:
                with self.assertRaisesRegex(ManifestError, "permission mode drifted"):
                    rollback(receipt_path, manifest=manifest)
                self.assertEqual(before, sha256_tree(backup))
                self.assertTrue(receipt_path.exists())
            finally:
                backup.chmod(original)
            self.assertEqual("pass", rollback(receipt_path, manifest=manifest)["status"])


if __name__ == "__main__":
    unittest.main()
