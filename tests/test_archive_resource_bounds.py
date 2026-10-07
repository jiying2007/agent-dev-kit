"""Archive limits at public verification and real extraction entrypoints."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_dev_kit.distribution import archive_io, release_artifacts, release_contract
from agent_dev_kit.model import ManifestError, canonical_json_bytes
from agent_dev_kit import release
from agent_dev_kit.cli import main as cli_main


class ArchiveResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "agent-dev-kit-7.0.0.tar.gz"
        source = b'{"version":"7.0.0"}'
        sbom = b'{"spdxVersion":"SPDX-2.3"}'
        release = {
            "schema_version": 2, "version": "7.0.0",
            "manifest_sha256": hashlib.sha256(canonical_json_bytes({"version": "7.0.0"})).hexdigest(),
            "direct_targets": [{"target": "claude-code", "agents": 1, "skills": 1}],
            "external_targets": ["external-runtime"], "source_distribution": True,
            "source_file_count": 2, "reproducible": False, "release_eligible": False,
            "source_provenance": {"kind": "unbound-snapshot", "release_eligible": False,
                                  "commit": None, "tree": None, "dirty": None,
                                  "source_distribution_sha256": "0" * 64},
            "sbom": {"path": "sbom.spdx.json", "sha256": hashlib.sha256(sbom).hexdigest(),
                     "validated": True},
        }
        self.members = [("manifest.json", source), ("release-manifest.json", json.dumps(release).encode()),
                        ("sbom.spdx.json", sbom)]
        self.write_archive(self.members)

    def write_archive(self, members, *, format=tarfile.PAX_FORMAT):
        with tarfile.open(self.path, "w:gz", format=format) as archive:
            for name, payload in members:
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))

    def test_valid_order_independence_and_no_getmembers(self):
        self.write_archive(list(reversed(self.members)))
        with mock.patch.object(tarfile.TarFile, "getmembers", side_effect=AssertionError("unbounded inventory")):
            value = release_contract.validate_release_artifact(self.path)
        self.assertEqual("pass", value["status"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), value["artifact_sha256"])

    def test_compressed_snapshot_is_bounded_before_decompression(self):
        with mock.patch.object(archive_io, "MAX_COMPRESSED_BYTES", 8), \
             mock.patch.object(gzip, "GzipFile", side_effect=AssertionError("must not decompress")):
            with self.assertRaisesRegex(ValueError, "bounded regular"):
                release_contract.validate_release_artifact(self.path)

    def test_member_count_is_bounded_even_without_payload(self):
        self.write_archive([(str(i), b"") for i in range(32)] + self.members)
        with mock.patch.object(archive_io, "MAX_MEMBERS", 8):
            with self.assertRaisesRegex(ValueError, "member budget"):
                release_contract.validate_release_artifact(self.path)

    def test_member_size_and_name_are_bounded(self):
        for extra, field, limit, message in (([("x", b"x" * 33)], "MAX_MEMBER_BYTES", 32, "member byte"),
                                              ([("x" * 65, b"")], "MAX_NAME_BYTES", 64, "member name")):
            self.write_archive(extra + self.members)
            with mock.patch.object(archive_io, field, limit):
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                    release_contract.validate_release_artifact(self.path)

    def test_decoded_padding_and_concatenated_gzip_count_toward_budget(self):
        raw = self.path.read_bytes()
        decoded = len(gzip.decompress(raw))
        with mock.patch.object(archive_io, "MAX_DECODED_BYTES", decoded - 1):
            with self.assertRaisesRegex(ValueError, "decoded byte"):
                release_contract.validate_release_artifact(self.path)
        self.path.write_bytes(raw + gzip.compress(b"\0" * 1024))
        with mock.patch.object(archive_io, "MAX_DECODED_BYTES", decoded + 64):
            with self.assertRaisesRegex(ValueError, "decoded byte"):
                release_contract.validate_release_artifact(self.path)

    def test_hidden_pax_header_read_is_bounded_before_materialization(self):
        header = tarfile.TarInfo("hidden")
        header.type = tarfile.XHDTYPE
        header.size = archive_io.MAX_HEADER_READ_BYTES + 1024
        self.path.write_bytes(gzip.compress(header.tobuf(format=tarfile.USTAR_FORMAT)))
        with self.assertRaisesRegex(ValueError, "header read budget"):
            release_contract.validate_release_artifact(self.path)

    def test_hidden_header_chain_fails_as_contract_error_before_recursion(self):
        header = tarfile.TarInfo("hidden")
        header.type = tarfile.XHDTYPE
        header.size = 0
        self.path.write_bytes(gzip.compress(header.tobuf(format=tarfile.USTAR_FORMAT) * 1200))
        with self.assertRaisesRegex(archive_io.ArchiveInputError, "hidden header chain"):
            release_contract.validate_release_artifact(self.path)

    def test_metadata_and_pax_keys_have_separate_budgets(self):
        with mock.patch.object(archive_io, "MAX_METADATA_BYTES", 512):
            with self.assertRaisesRegex(ValueError, "metadata byte"):
                release_contract.validate_release_artifact(self.path)
        with tarfile.open(self.path, "w:gz", pax_headers={str(i): "value" for i in range(8)}) as archive:
            for name, payload in self.members:
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        with mock.patch.object(archive_io, "MAX_PAX_KEYS", 4):
            with self.assertRaisesRegex(ValueError, "PAX key"):
                release_contract.validate_release_artifact(self.path)

    def test_member_cache_does_not_retain_global_pax_maps(self):
        with tarfile.open(self.path, "w:gz", pax_headers={str(i): "v" for i in range(32)}) as archive:
            for name, payload in [(str(i), b"") for i in range(256)] + self.members:
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        observed = []
        real = tarfile.TarFile.next

        def measured(archive):
            value = real(archive)
            observed.append(len(archive.members))
            return value

        with mock.patch.object(tarfile.TarFile, "next", measured):
            self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])
        self.assertLessEqual(max(observed), 1)

    def sidecar(self, path):
        path.with_name(path.name + ".sha256").write_text(
            hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n")

    def test_real_rehearsal_rejects_overbudget_and_unsafe_leaf_before_workspace(self):
        self.sidecar(self.path)
        link = self.root / "link.tar.gz"
        link.symlink_to(self.path)
        with mock.patch.object(release.tempfile, "mkdtemp", side_effect=AssertionError("premature workspace")):
            with self.assertRaises(ManifestError):
                release.rehearse_release(link, self.path)
            with mock.patch.object(archive_io, "MAX_COMPRESSED_BYTES", 8):
                with self.assertRaises(ManifestError):
                    release.rehearse_release(self.path, self.path)

    def test_real_delivery_cli_preserves_leaf_link_rejection(self):
        self.sidecar(self.path)
        folder = self.root / "links"
        folder.mkdir()
        link = folder / self.path.name
        link.symlink_to(self.path)
        for args in (["release", "rehearse", "--previous-artifact", str(link),
                      "--candidate-artifact", str(self.path)],
                     ["release", "publish", "--version", "7.0.0", "--backend", "github",
                      "--artifact", str(link), "--dry-run"]):
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                status = cli_main(args)
            self.assertNotEqual(0, status)
            self.assertIn("bounded regular file", output.getvalue())

    def test_real_rehearsal_checksum_input_is_bounded_regular(self):
        checksum = self.path.with_name(self.path.name + ".sha256")
        checksum.write_bytes(b"x" * 8193)
        with self.assertRaisesRegex(ManifestError, "bounded regular ASCII"):
            release.rehearse_release(self.path, self.path)
        checksum.unlink()
        checksum.symlink_to(self.path)
        with self.assertRaisesRegex(ManifestError, "bounded regular ASCII"):
            release.rehearse_release(self.path, self.path)

    def test_real_rehearsal_hash_and_extraction_share_captured_bytes(self):
        candidate = self.root / "candidate.tar.gz"
        candidate.write_bytes(self.path.read_bytes())
        self.sidecar(self.path)
        self.sidecar(candidate)
        real = release_artifacts._verified_archive_snapshot

        def captured(path):
            result = real(path)
            path.write_bytes(b"REPLACED")
            return result

        def prove_extracted(root):
            self.assertEqual(self.members[0][1], (root / "manifest.json").read_bytes())
            raise ManifestError("stopped after snapshot extraction proof")

        with mock.patch.object(release_artifacts, "_verified_archive_snapshot", side_effect=captured), \
             mock.patch.object(release_artifacts, "_release_source_root", side_effect=prove_extracted):
            with self.assertRaisesRegex(ManifestError, "snapshot extraction proof"):
                release.rehearse_release(self.path, candidate)

    def test_publish_uploads_snapshot_not_replaced_original(self):
        self.sidecar(self.path)
        expected = self.path.read_bytes()
        real = release_artifacts._verified_archive_snapshot
        uploads = []

        def captured(path):
            result = real(path)
            path.write_bytes(b"REPLACED")
            return result

        def upload(command, **_kwargs):
            path = Path(command[4])
            self.assertEqual(expected, path.read_bytes())
            self.assertEqual(hashlib.sha256(expected).hexdigest(), Path(command[5]).read_text().split()[0])
            uploads.append(path)
            return mock.Mock(returncode=0, stdout="published", stderr="")

        with mock.patch.object(release_artifacts, "_verified_archive_snapshot", side_effect=captured), \
             mock.patch.object(release_artifacts, "_assert_publishable_release_artifact"), \
             mock.patch.object(release.shutil, "which", return_value="/usr/bin/gh"), \
             mock.patch.object(release.subprocess, "run", side_effect=upload):
            self.assertEqual("pass", release.publish_release("7.0.0", "github", self.path)["status"])
        self.assertTrue(uploads)
        self.assertFalse(uploads[0].exists())

    def test_bad_crc_and_truncated_gzip_are_rejected_at_eof(self):
        raw = self.path.read_bytes()
        damaged = bytearray(raw)
        damaged[-8] ^= 1
        for value in (bytes(damaged), raw[:-5]):
            self.path.write_bytes(value)
            with self.subTest(value=value[-8:]), self.assertRaisesRegex(ValueError, "invalid release archive"):
                release_contract.validate_release_artifact(self.path)

    def test_required_members_missing_duplicate_and_special_are_rejected(self):
        for members in (self.members[:-1], self.members + [self.members[0]]):
            self.write_archive(members)
            with self.assertRaises(ValueError):
                release_contract.validate_release_artifact(self.path)
        with tarfile.open(self.path, "w:gz") as archive:
            link = tarfile.TarInfo("manifest.json")
            link.type = tarfile.SYMTYPE
            link.linkname = "outside"
            archive.addfile(link)
        with self.assertRaisesRegex(ValueError, "one regular file"):
            release_contract.validate_release_artifact(self.path)

    def test_long_pax_names_remain_compatible_within_budget(self):
        self.write_archive([("source/" + "a" * 200, b"safe")] + self.members)
        self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])

    def test_digest_and_extraction_use_exact_snapshot_after_path_replacement(self):
        expected = hashlib.sha256(self.path.read_bytes()).hexdigest()
        real = archive_io.load_archive_snapshot

        def captured(path, **kwargs):
            result = real(path, **kwargs)
            path.write_bytes(b"REPLACED")
            return result

        with mock.patch.object(release_contract, "load_archive_snapshot", side_effect=captured):
            value = release_contract.validate_release_artifact(self.path)
        self.assertEqual(expected, value["artifact_sha256"])
        self.write_archive(self.members)
        with mock.patch.object(release_artifacts, "load_archive_snapshot", side_effect=captured):
            output = release_artifacts._extract_release(self.path, self.root / "extracted")
        self.assertEqual(self.members[0][1], (output / "manifest.json").read_bytes())

    def test_extraction_budget_failure_precedes_destination_creation(self):
        target = self.root / "not-created"
        with mock.patch.object(archive_io, "MAX_MEMBERS", 1):
            with self.assertRaises(ManifestError):
                release_artifacts._extract_release(self.path, target)
        self.assertFalse(target.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX file boundaries")
    def test_snapshot_rejects_leaf_links_fifos_and_directories_without_hanging(self):
        link = self.root / "link.tar.gz"
        link.symlink_to(self.path)
        fifo = self.root / "fifo.tar.gz"
        os.mkfifo(fifo)
        for path in (link, fifo, self.root):
            with self.subTest(path=path), self.assertRaises(ValueError):
                release_contract.validate_release_artifact(path)


if __name__ == "__main__":
    unittest.main()
