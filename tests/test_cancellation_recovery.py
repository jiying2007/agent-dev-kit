"""Cancellation recovery contracts; all mutations use disposable directories."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_dev_kit import atomic_io
from agent_dev_kit import installation_contract as contract
from agent_dev_kit import installation_transaction as transaction
from agent_dev_kit.installation_plan import create_plan, write_plan
from agent_dev_kit.model import Manifest, ManifestError

ROOT = Path(__file__).resolve().parents[1]


class DocumentCancellationTest(unittest.TestCase):
    def assert_original_recoverable(self, path: Path, original: bytes) -> None:
        candidates = [path, *path.parent.glob("." + path.name + ".*.previous")]
        self.assertTrue(any(p.is_file() and p.read_bytes() == original for p in candidates))

    def test_cancellation_preserves_originals_before_and_after_publication(self):
        for cancellation in (KeyboardInterrupt, SystemExit):
            for boundary in ("backup", "publish"):
                with self.subTest(cancellation=cancellation, boundary=boundary), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    first, second = root / "first.json", root / "second.json"
                    first.write_bytes(b"original-first")
                    second.write_bytes(b"original-second")
                    replace = atomic_io.os.replace

                    def cancel_after_rename(source, destination):
                        result = replace(source, destination)
                        backup = Path(source) == first
                        publish = Path(destination) == first and Path(source).suffix == ".stage"
                        if (boundary == "backup" and backup) or (boundary == "publish" and publish):
                            raise cancellation("cancelled fixture publication")
                        return result

                    with patch.object(atomic_io.os, "replace", side_effect=cancel_after_rename):
                        with self.assertRaises(cancellation):
                            atomic_io.write_texts_atomic(((first, "new-first"), (second, "new-second")))
                    self.assert_original_recoverable(first, b"original-first")
                    self.assert_original_recoverable(second, b"original-second")
                    self.assertTrue(list(root.glob("*.stage")))

    def test_recovery_cancellation_also_preserves_originals(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "first.json", root / "second.json"
            first.write_bytes(b"original-first")
            second.write_bytes(b"original-second")
            replace = atomic_io.os.replace

            def interrupt_recovery(source, destination):
                if Path(destination) == second and Path(source).suffix == ".stage":
                    raise OSError("fixture publication failure")
                if Path(destination) == first and Path(source).suffix == ".previous":
                    raise KeyboardInterrupt("fixture recovery cancellation")
                return replace(source, destination)

            with patch.object(atomic_io.os, "replace", side_effect=interrupt_recovery):
                with self.assertRaises(KeyboardInterrupt):
                    atomic_io.write_texts_atomic(((first, "new-first"), (second, "new-second")))
            self.assert_original_recoverable(first, b"original-first")
            self.assert_original_recoverable(second, b"original-second")

    def test_success_and_complete_recovery_clean_temporary_material(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first, second = root / "first.json", root / "second.json"
                first.write_text("original-first")
                second.write_text("original-second")
                replace = atomic_io.os.replace

                def publish(source, destination):
                    if fail and Path(destination) == second and Path(source).suffix == ".stage":
                        raise OSError("fixture publication failure")
                    return replace(source, destination)

                with patch.object(atomic_io.os, "replace", side_effect=publish):
                    if fail:
                        with self.assertRaises(OSError):
                            atomic_io.write_texts_atomic(((first, "new-first"), (second, "new-second")))
                    else:
                        atomic_io.write_texts_atomic(((first, "new-first"), (second, "new-second")))
                self.assertEqual(first.read_text(), "original-first" if fail else "new-first")
                self.assertEqual(second.read_text(), "original-second" if fail else "new-second")
                self.assertEqual(set(root.iterdir()), {first, second})


class InstallCancellationTest(unittest.TestCase):
    def prepare(self, root: Path):
        manifest = Manifest.load(ROOT)
        target, plan_path = root / "target", root / "plan.json"
        write_plan(create_plan(manifest, "claude-code", str(target), ("core",), (),
                               "copy", asset_kind="agent"), plan_path)
        transaction.apply_plan(manifest, plan_path)
        plan = create_plan(manifest, "claude-code", str(target), ("core",), (),
                           "copy", asset_kind="agent")
        write_plan(plan, plan_path)
        return manifest, target, plan_path, plan

    def assert_blocked(self, manifest, target: Path, plan_path: Path):
        self.assertTrue(list((target / ".adk-staging").iterdir()))
        with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
            transaction.apply_plan(manifest, plan_path)
        with self.assertRaisesRegex(ManifestError, "unresolved ADK transaction"):
            transaction.rollback(target / contract.RECEIPT_NAME, manifest=manifest)

    def test_apply_cancellation_preserves_marker_originals_and_previous_receipt(self):
        for cancellation in (KeyboardInterrupt, SystemExit):
            for boundary in ("backup", "publish"):
                with self.subTest(cancellation=cancellation, boundary=boundary), tempfile.TemporaryDirectory() as temp:
                    manifest, target, plan_path, plan = self.prepare(Path(temp))
                    receipt_path = target / contract.RECEIPT_NAME
                    previous_receipt = receipt_path.read_bytes()
                    relative = plan["operations"][0]["destination"]
                    asset = target / relative
                    original = asset.read_bytes()
                    replace = transaction.os.replace

                    def cancel_after_rename(source, destination):
                        result = replace(source, destination)
                        backup = Path(source) == asset
                        publish = Path(destination) == asset and ".adk-staging" in Path(source).parts
                        if (boundary == "backup" and backup) or (boundary == "publish" and publish):
                            raise cancellation("cancelled fixture install")
                        return result

                    with patch.object(transaction.os, "replace", side_effect=cancel_after_rename):
                        with self.assertRaises(cancellation):
                            transaction.apply_plan(manifest, plan_path)
                    self.assertEqual(receipt_path.read_bytes(), previous_receipt)
                    backups = list((target / ".adk-backups").glob("*/" + relative))
                    self.assertTrue(any(path.read_bytes() == original for path in backups))
                    self.assert_blocked(manifest, target, plan_path)

    def test_cancellation_after_receipt_publication_keeps_conservative_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, target, plan_path, _ = self.prepare(Path(temp))
            receipt_path = target / contract.RECEIPT_NAME
            previous_receipt = receipt_path.read_bytes()
            write_document = contract._write_document

            def publish_then_cancel(text, path):
                write_document(text, path)
                raise KeyboardInterrupt("cancelled after fixture receipt publication")

            with patch.object(contract, "_write_document", side_effect=publish_then_cancel):
                with self.assertRaises(KeyboardInterrupt):
                    transaction.apply_plan(manifest, plan_path)
            self.assertNotEqual(receipt_path.read_bytes(), previous_receipt)
            self.assert_blocked(manifest, target, plan_path)


if __name__ == "__main__":
    unittest.main()
