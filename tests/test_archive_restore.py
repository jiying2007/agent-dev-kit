"""Actual filesystem boundaries for the public directory-backup restore."""
from __future__ import annotations

import io
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit import installation_transaction as transaction
from agent_dev_kit.model import ManifestError

ROOT = Path(__file__).resolve().parents[1]


class ArchiveRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "runtime"
        self.target.mkdir()
        (self.target / "sentinel").write_bytes(b"original\x00bytes")
        self.archive = self.root / "backup.tar.gz"

    def make_archive(self, entries=None):
        if entries is None:
            entries = [("runtime", "dir", b""), ("runtime/restored", "file", b"restored\x00bytes")]
        with tarfile.open(self.archive, "w:gz") as stream:
            for name, kind, content in entries:
                item = tarfile.TarInfo(name)
                item.mode = 0o755 if kind == "dir" else 0o640
                item.type = {"dir": tarfile.DIRTYPE, "file": tarfile.REGTYPE,
                             "symlink": tarfile.SYMTYPE, "hardlink": tarfile.LNKTYPE,
                             "fifo": tarfile.FIFOTYPE}[kind]
                if kind in ("symlink", "hardlink"):
                    item.linkname = "../../outside"
                item.size = len(content) if kind == "file" else 0
                stream.addfile(item, io.BytesIO(content) if kind == "file" else None)

    def assert_original(self):
        self.assertEqual((self.target / "sentinel").read_bytes(), b"original\x00bytes")
        self.assertFalse((self.target / "restored").exists())

    def test_rejects_corrupt_and_crc_damaged_stream_before_target_move(self):
        for content in (b"not a gzip archive",):
            self.archive.write_bytes(content)
            with self.assertRaises(ManifestError):
                transaction.restore_archive(self.archive, self.target, overwrite=True)
            self.assert_original()
        self.make_archive()
        data = bytearray(self.archive.read_bytes())
        data[-8] ^= 1
        self.archive.write_bytes(data)
        with self.assertRaises(ManifestError):
            transaction.restore_archive(self.archive, self.target, overwrite=True)
        self.assert_original()

    def test_wrong_root_traversal_links_and_special_entries_do_not_touch_target(self):
        candidates = [
            [("other", "dir", b""), ("other/file", "file", b"bad")],
            [("runtime", "dir", b""), ("runtime/../outside", "file", b"bad")],
            [("runtime", "dir", b""), ("/runtime/file", "file", b"bad")],
            [("runtime", "dir", b""), ("runtime//file", "file", b"bad")],
            [("runtime", "dir", b""), (".", "dir", b"")],
        ]
        for kind in ("symlink", "hardlink", "fifo"):
            candidates.append([("runtime", "dir", b""), ("runtime/link", kind, b"")])
        candidates.append([("runtime", "dir", b""), ("runtime/a", "file", b"1"),
                           ("runtime/a", "file", b"2")])
        for entries in candidates:
            with self.subTest(entries=entries):
                self.make_archive(entries)
                with self.assertRaises(ManifestError):
                    transaction.restore_archive(self.archive, self.target, overwrite=True)
                self.assert_original()
                self.assertFalse((self.root / "outside").exists())
                self.assertFalse((self.root / "other").exists())

    def test_overwrite_requires_force_and_success_is_exact_target(self):
        self.make_archive()
        with self.assertRaises(ManifestError):
            transaction.restore_archive(self.archive, self.target)
        self.assert_original()
        result = transaction.restore_archive(self.archive, self.target, overwrite=True)
        self.assertEqual(result["status"], "pass")
        self.assertEqual((self.target / "restored").read_bytes(), b"restored\x00bytes")
        self.assertEqual((self.target / "restored").stat().st_mode & 0o777, 0o640)
        self.assertFalse((self.target / "sentinel").exists())
        self.assertEqual(list(self.root.glob(".runtime.adk-archive-restore-*")), [])

    def test_symlink_target_and_archive_ancestor_are_rejected(self):
        self.make_archive()
        alias = self.root / "alias"
        alias.symlink_to(self.target, target_is_directory=True)
        with self.assertRaises(ManifestError):
            transaction.restore_archive(self.archive, alias, overwrite=True)
        parent_alias = self.root / "parent-alias"
        parent_alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ManifestError):
            transaction.restore_archive(parent_alias / self.archive.name, self.target, overwrite=True)
        self.assert_original()

    def test_extraction_failure_preserves_target_and_blocks_unresolved_retry(self):
        self.make_archive()
        with patch.object(tarfile.TarFile, "extractfile", side_effect=OSError("injected extraction failure")):
            with self.assertRaisesRegex(ManifestError, "staging retained"):
                transaction.restore_archive(self.archive, self.target, overwrite=True)
        self.assert_original()
        self.assertEqual(len(list(self.root.glob(".runtime.adk-archive-restore-*"))), 1)
        with self.assertRaisesRegex(ManifestError, "unresolved"):
            transaction.restore_archive(self.archive, self.target, overwrite=True)

    def test_commit_failure_compensates_and_retains_staged_payload(self):
        self.make_archive()
        replace = os.replace

        def fail_commit(source, destination):
            if Path(source).name == "payload":
                raise OSError("injected commit failure")
            return replace(source, destination)

        with patch.object(transaction.os, "replace", side_effect=fail_commit):
            with self.assertRaisesRegex(ManifestError, "staging retained"):
                transaction.restore_archive(self.archive, self.target, overwrite=True)
        self.assert_original()
        stage, = self.root.glob(".runtime.adk-archive-restore-*")
        self.assertEqual((stage / "payload/restored").read_bytes(), b"restored\x00bytes")

    def test_second_compensation_failure_retains_only_original_copy(self):
        self.make_archive()
        replace = os.replace

        def fail_commit_and_compensation(source, destination):
            if Path(source).name in ("payload", "previous"):
                raise OSError("injected commit and compensation failure")
            return replace(source, destination)

        with patch.object(transaction.os, "replace", side_effect=fail_commit_and_compensation):
            with self.assertRaisesRegex(ManifestError, "staging retained"):
                transaction.restore_archive(self.archive, self.target, overwrite=True)
        stage, = self.root.glob(".runtime.adk-archive-restore-*")
        self.assertFalse(self.target.exists())
        self.assertEqual((stage / "previous/sentinel").read_bytes(), b"original\x00bytes")
        self.assertEqual((stage / "payload/restored").read_bytes(), b"restored\x00bytes")

    def test_public_script_round_trip_and_wrong_basename_preserve_selected_target(self):
        script = ROOT / "scripts/backup-rollback.sh"
        backups = self.root / "backups"
        args = ["bash", str(script), "backup", "--target", str(self.target),
                "--backup-dir", str(backups), "--version", "test"]
        created = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        (self.target / "sentinel").write_bytes(b"changed")
        restored = subprocess.run(["bash", str(script), "restore", "--target", str(self.target),
                                   "--backup-dir", str(backups), "--version", "test", "--force"],
                                  capture_output=True, text=True)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assert_original()
        other = self.root / "different"
        other.mkdir()
        (other / "sentinel").write_bytes(b"other content")
        rejected = subprocess.run(["bash", str(script), "restore", "--target", str(other),
                                   "--backup-dir", str(backups), "--version", "test", "--force"],
                                  capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual((other / "sentinel").read_bytes(), b"other content")
        self.assert_original()


if __name__ == "__main__":
    unittest.main()
