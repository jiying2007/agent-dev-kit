"""Independent release review probes; no network or real publication.

Reviewer: ai/root/external_methods. Author of implementation: ai/root/implement_release.
Run from the repository with PYTHONPATH=src. All mutations occur in temporary fixtures.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

from agent_dev_kit import release
from agent_dev_kit.distribution import archive_io, release_artifacts, release_contract
from agent_dev_kit.model import Manifest, canonical_json_bytes, sha256_tree

ROOT = Path(__file__).resolve().parents[4]


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
        text=True, timeout=60,
        env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull),
    ).stdout.strip()


def commit(root, message):
    git(root, "add", "--all")
    git(root, "-c", "user.name=Independent Review", "-c", "user.email=review@adk.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", message)


class FrozenAuthorityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="adk-independent-release-review-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.template = cls.work / "template"
        release_artifacts._copy_source_distribution(Manifest.load(ROOT), cls.template)
        executable = cls.template / "docs/independent-review-executable.sh"
        executable.write_bytes(b"#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        git(cls.template, "init", "-q")
        commit(cls.template, "independent clean fixture")
        cls.commit = git(cls.template, "rev-parse", "HEAD")
        cls.tree = git(cls.template, "rev-parse", "HEAD^{tree}")
        cls.baseline = release.build_release(Manifest.load(cls.template), cls.work / "baseline")
        cls.archive_bytes = Path(cls.baseline["artifact"]).read_bytes()

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.temp_case.cleanup)
        self.case = Path(self.temp_case.name)
        self.source = self.case / "source"
        git(self.work, "clone", "-q", "--no-hardlinks", str(self.template), str(self.source))

    def assert_frozen(self):
        result = release.build_release(Manifest.load(self.source), self.case / "dist")
        self.assertEqual(self.archive_bytes, Path(result["artifact"]).read_bytes())
        self.assertEqual(self.commit, result["source_provenance"]["commit"])
        self.assertEqual(self.tree, result["source_provenance"]["tree"])
        self.assertTrue(result["release_eligible"])
        return result

    def test_commit_and_tree_replacement_refs_cannot_change_authority(self):
        (self.source / "README.md").write_text("replacement commit contents\n")
        commit(self.source, "alternative tree")
        replacement_commit = git(self.source, "rev-parse", "HEAD")
        replacement_tree = git(self.source, "rev-parse", "HEAD^{tree}")
        git(self.source, "reset", "--hard", self.commit)
        for original, replacement in ((self.commit, replacement_commit), (self.tree, replacement_tree)):
            with self.subTest(object=original):
                git(self.source, "replace", original, replacement)
                self.assert_frozen()
                git(self.source, "replace", "-d", original)

    def test_hidden_manifest_and_compiled_asset_drift_cannot_change_archive(self):
        skill = next((self.source / "skills").glob("*/SKILL.md"))
        git(self.source, "update-index", "--assume-unchanged", "manifest.json",
            skill.relative_to(self.source).as_posix())
        manifest = json.loads((self.source / "manifest.json").read_text())
        manifest["version"] = "99.0.0"
        (self.source / "manifest.json").write_text(json.dumps(manifest))
        skill.write_text("invalid replacement of a compiled asset\n")
        self.assertEqual("", git(self.source, "status", "--porcelain", "--untracked-files=all"))
        self.assert_frozen()

    def test_worktree_modes_do_not_override_tracked_executable_mode(self):
        git(self.source, "config", "core.filemode", "false")
        (self.source / "docs/independent-review-executable.sh").chmod(0o600)
        (self.source / "README.md").chmod(0o755)
        self.assertEqual("", git(self.source, "status", "--porcelain", "--untracked-files=all"))
        result = self.assert_frozen()
        with tarfile.open(result["artifact"], "r:gz") as archive:
            self.assertEqual(0o755, archive.getmember("source/docs/independent-review-executable.sh").mode)
            self.assertEqual(0o644, archive.getmember("source/README.md").mode)

    def test_publish_cli_contract_equality_and_preexisting_dry_run_asset(self):
        artifact = self.case / Path(self.baseline["artifact"]).name
        artifact.write_bytes(self.archive_bytes)
        checksum = artifact.with_name(artifact.name + ".sha256")
        expected_checksum = hashlib.sha256(self.archive_bytes).hexdigest() + "  " + artifact.name + "\n"
        checksum.write_text(expected_checksum)
        local_contract = self.case / "release-contract.json"
        local_contract.write_bytes(b"preexisting local contract sentinel\n")
        cli = subprocess.run([sys.executable, "-m", "agent_dev_kit.distribution.release_contract", str(artifact)],
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        with mock.patch.object(release.shutil, "which", return_value="/fixture/gh"), \
             mock.patch.object(release.subprocess, "run", side_effect=AssertionError("dry-run executed a process")):
            plan = release.publish_release(self.baseline["version"], "github", artifact, dry_run=True)
        self.assertEqual("planned", plan["status"])
        self.assertEqual(b"preexisting local contract sentinel\n", local_contract.read_bytes())
        self.assertEqual(self.archive_bytes, artifact.read_bytes())
        self.assertEqual(expected_checksum, checksum.read_text())
        capture = release_artifacts._verified_archive_snapshot
        observed = []

        def capture_then_replace(path):
            result = capture(path)
            artifact.write_bytes(b"post-verification archive replacement")
            checksum.write_bytes(b"post-verification sidecar replacement")
            local_contract.write_bytes(b"post-verification contract replacement")
            return result

        def observe_upload(command, **kwargs):
            self.assertEqual(["release", "create", "v" + self.baseline["version"]], command[1:4])
            uploaded_archive, uploaded_checksum, uploaded_contract = map(Path, command[4:7])
            self.assertEqual(self.archive_bytes, uploaded_archive.read_bytes())
            self.assertEqual(expected_checksum.encode(), uploaded_checksum.read_bytes())
            self.assertEqual(cli.stdout, uploaded_contract.read_bytes())
            self.assertEqual(["--verify-tag", "--repo", "fixture/fixture"], command[7:])
            observed.append(uploaded_archive.parent)
            return subprocess.CompletedProcess(command, 0, "fixture only", "")

        with mock.patch.object(release_artifacts, "_verified_archive_snapshot", side_effect=capture_then_replace), \
             mock.patch.object(release.shutil, "which", return_value="/fixture/gh"), \
             mock.patch.object(release.subprocess, "run", side_effect=observe_upload):
            result = release.publish_release(self.baseline["version"], "github", artifact,
                                             repository="fixture/fixture")
        self.assertEqual("pass", result["status"])
        self.assertEqual(1, len(observed))
        self.assertFalse(observed[0].exists())


class InventoryReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="adk-independent-inventory-review-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.artifact = self.work / "agent-dev-kit-7.0.0.tar.gz"
        self.source = {
            "manifest.json": b'{"version":"7.0.0"}\n',
            "docs/a/z.txt": b"nested path sort order\n",
            "docs/a-b.txt": b"sibling path sort order\n",
            "docs/z/large.bin": b"X" * (9 * 1024 * 1024 + 57),
        }
        source_tree = self.work / "source"
        for name, raw in self.source.items():
            path = source_tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.sbom = b'{"spdxVersion":"SPDX-2.3"}\n'
        self.release_manifest = {
            "schema_version": 2, "version": "7.0.0",
            "manifest_sha256": hashlib.sha256(canonical_json_bytes({"version": "7.0.0"})).hexdigest(),
            "direct_targets": [{"target": "claude-code", "agents": 1, "skills": 1}],
            "external_targets": ["external-runtime"], "source_distribution": True,
            "source_file_count": len(self.source), "reproducible": False, "release_eligible": False,
            "source_provenance": {"kind": "unbound-snapshot", "release_eligible": False,
                                  "commit": None, "tree": None, "dirty": None,
                                  "source_distribution_sha256": sha256_tree(source_tree)},
            "sbom": {"path": "sbom.spdx.json", "sha256": hashlib.sha256(self.sbom).hexdigest(),
                     "validated": True},
        }

    def write(self, before=(), after=(), tamper=False):
        members = [("manifest.json", self.source["manifest.json"]), ("sbom.spdx.json", self.sbom),
                   ("release-manifest.json", json.dumps(self.release_manifest).encode())]
        members += [("source/" + name, raw[:-1] + b"Y" if tamper and name.endswith("large.bin") else raw)
                    for name, raw in reversed(list(self.source.items()))]
        with tarfile.open(self.artifact, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for member in before:
                archive.addfile(member, io.BytesIO(b"!" * member.size))
            for name, raw in members:
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
            for member in after:
                archive.addfile(member, io.BytesIO(b"!" * member.size))

    def test_nested_sort_and_large_source_streaming(self):
        directories = []
        for name in ("source", "source/docs", "source/docs/a", "source/docs/z"):
            member = tarfile.TarInfo(name)
            member.type = tarfile.DIRTYPE
            directories.append(member)
        self.write(after=directories)
        self.assertEqual("pass", release_contract.validate_release_artifact(self.artifact)["status"])
        inventory = {}
        _, payloads = archive_io.load_archive_snapshot(self.artifact, source_inventory=inventory)
        self.assertEqual(set(payloads), {"manifest.json", "source/manifest.json", "sbom.spdx.json",
                                         "release-manifest.json"})
        self.assertEqual(len(self.source), inventory["file_count"])
        self.assertEqual(self.release_manifest["source_provenance"]["source_distribution_sha256"],
                         inventory["sha256"])
        self.write(tamper=True)
        with self.assertRaisesRegex(ValueError, "source distribution digest"):
            release_contract.validate_release_artifact(self.artifact)

    def test_conflicts_duplicate_directories_and_pax_override_are_rejected(self):
        ancestor = tarfile.TarInfo("source/docs")
        duplicate1 = tarfile.TarInfo("source/docs/")
        duplicate1.type = tarfile.DIRTYPE
        duplicate2 = tarfile.TarInfo("source/docs")
        duplicate2.type = tarfile.DIRTYPE
        pax = tarfile.TarInfo("innocent-name")
        pax.pax_headers = {"path": "source/../escape"}
        payload_directory = tarfile.TarInfo("source/payload-directory")
        payload_directory.type = tarfile.DIRTYPE
        payload_directory.size = 1
        for label, before, after in (
            ("ancestor-before-child", [ancestor], []),
            ("ancestor-after-child", [], [ancestor]),
            ("duplicate-directory", [duplicate1], [duplicate2]),
            ("pax-path-override", [], [pax]),
            ("directory-payload", [], [payload_directory]),
        ):
            with self.subTest(label=label):
                self.write(before=before, after=after)
                with self.assertRaises(ValueError):
                    release_contract.validate_release_artifact(self.artifact)

    def test_oversized_source_header_rejected_before_payload_read(self):
        member = tarfile.TarInfo("source/large.bin")
        member.size = archive_io.MAX_MEMBER_BYTES + 1
        self.artifact.write_bytes(gzip.compress(member.tobuf() + bytes(1024), mtime=0))
        with self.assertRaisesRegex(ValueError, "member byte budget"):
            release_contract.validate_release_artifact(self.artifact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
