"""Public release behavior binds Git inputs, archive contents and published assets."""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_dev_kit import release
from agent_dev_kit.distribution import release_artifacts, release_contract
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]


class ReleaseInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "agent-dev-kit-7.0.0.tar.gz"
        source = b'{"version":"7.0.0"}\n'
        readme = b"source inventory fixture\n"
        sbom = b'{"spdxVersion":"SPDX-2.3"}\n'
        digest = hashlib.sha256()
        for name, value in (("README.md", readme), ("manifest.json", source)):
            digest.update(name.encode() + b"\0" + hashlib.sha256(value).digest())
        self.manifest = {
            "schema_version": 2, "version": "7.0.0",
            "manifest_sha256": hashlib.sha256(canonical_json_bytes({"version": "7.0.0"})).hexdigest(),
            "direct_targets": [{"target": "claude-code", "agents": 1, "skills": 1}],
            "external_targets": ["external-runtime"], "source_distribution": True,
            "source_file_count": 2, "reproducible": False, "release_eligible": False,
            "source_provenance": {"kind": "unbound-snapshot", "release_eligible": False,
                                  "commit": None, "tree": None, "dirty": None,
                                  "source_distribution_sha256": digest.hexdigest()},
            "sbom": {"path": "sbom.spdx.json", "sha256": hashlib.sha256(sbom).hexdigest(),
                     "validated": True},
        }
        self.members = [("manifest.json", source), ("source/manifest.json", source),
                        ("source/README.md", readme), ("sbom.spdx.json", sbom)]

    def write(self, members=None, special=None):
        values = list(self.members if members is None else members)
        values.append(("release-manifest.json", json.dumps(self.manifest).encode()))
        with tarfile.open(self.path, "w:gz") as archive:
            for name, payload in values:
                item = tarfile.TarInfo(name)
                item.size = len(payload)
                archive.addfile(item, io.BytesIO(payload))
            if special is not None:
                archive.addfile(special)
        self.path.with_name(self.path.name + ".sha256").write_text(
            hashlib.sha256(self.path.read_bytes()).hexdigest() + "  " + self.path.name + "\n")

    def test_real_source_inventory_is_accepted_in_any_member_order(self):
        self.write(list(reversed(self.members)))
        self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])

    def test_source_payload_drift_rejected_after_outer_checksum_is_recomputed(self):
        self.write([(name, b"changed\n" if name == "source/README.md" else raw)
                    for name, raw in self.members])
        with self.assertRaisesRegex(ValueError, "source distribution digest"):
            release_contract.validate_release_artifact(self.path)

    def test_missing_extra_and_false_source_count_are_rejected(self):
        for members in (self.members[:-2] + self.members[-1:],
                        self.members + [("source/extra.txt", b"extra")]):
            self.write(members)
            with self.subTest(members=len(members)), self.assertRaisesRegex(ValueError, "source file count"):
                release_contract.validate_release_artifact(self.path)
        self.manifest["source_file_count"] = 3
        self.write()
        with self.assertRaisesRegex(ValueError, "source file count"):
            release_contract.validate_release_artifact(self.path)

    def test_embedded_source_manifest_must_match_top_level(self):
        self.write([(name, b'{"version":"7.0.1"}' if name == "source/manifest.json" else raw)
                    for name, raw in self.members])
        with self.assertRaisesRegex(ValueError, "source manifest"):
            release_contract.validate_release_artifact(self.path)

    def test_renamed_public_publish_is_rejected_before_github_discovery(self):
        self.write()
        renamed = self.path.with_name("agent-dev-kit-9.9.9.tar.gz")
        self.path.rename(renamed)
        renamed.with_name(renamed.name + ".sha256").write_text(
            hashlib.sha256(renamed.read_bytes()).hexdigest() + "  " + renamed.name + "\n")
        with mock.patch.object(release.shutil, "which", side_effect=AssertionError("premature gh discovery")):
            with self.assertRaisesRegex(ManifestError, "filename.*version"):
                release.publish_release("9.9.9", "github", renamed, dry_run=True)

    def test_all_duplicate_unsafe_and_special_members_are_rejected(self):
        for extra in (("source/README.md", b"duplicate"), ("source/../escape", b"bad"),
                      ("source//alias.txt", b"bad"), ("/absolute", b"bad"),
                      ("source", b"file hiding a directory")):
            self.write(self.members + [extra])
            with self.subTest(name=extra[0]), self.assertRaises(ValueError):
                release_contract.validate_release_artifact(self.path)
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE):
            item = tarfile.TarInfo("source/special")
            item.type = kind
            item.linkname = "README.md"
            self.write(special=item)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                release_contract.validate_release_artifact(self.path)


class ReleaseGitInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.template = cls.work / "template"
        release_artifacts._copy_source_distribution(Manifest.load(ROOT), cls.template)
        (cls.template / ".gitignore").write_text("docs/.cache/\n")
        cls.git(cls.template, "init", "-q")
        cls.git(cls.template, "add", "--all")
        cls.git(cls.template, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "frozen release inputs")
        cls.baseline = release.build_release(Manifest.load(cls.template), cls.work / "baseline")
        cls.baseline_bytes = Path(cls.baseline["artifact"]).read_bytes()

    @staticmethod
    def git(root, *arguments):
        return subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True,
                              env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull),
                              text=True, timeout=60).stdout.strip()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.case.cleanup)
        self.root = Path(self.case.name)
        self.source = self.root / "source"
        self.git(self.work, "clone", "-q", "--no-hardlinks", str(self.template), str(self.source))

    def build(self):
        return release.build_release(Manifest.load(self.source), self.root / "dist")

    def test_ignored_file_cannot_enter_clean_commit_release(self):
        ignored = self.source / "docs/.cache/review-sentinel.txt"
        ignored.parent.mkdir()
        ignored.write_text("ignored residue\n")
        self.assertEqual("", self.git(self.source, "status", "--porcelain", "--untracked-files=all"))
        result = self.build()
        self.assertTrue(result["release_eligible"])
        self.assertEqual(self.baseline["source_file_count"], result["source_file_count"])
        self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_hidden_tracked_drift_cannot_change_frozen_release(self):
        for flag in ("--assume-unchanged", "--skip-worktree"):
            self.git(self.source, "update-index", "--no-assume-unchanged", "README.md")
            self.git(self.source, "update-index", flag, "README.md")
            (self.source / "README.md").write_text("hidden worktree drift\n")
            self.assertEqual("", self.git(self.source, "status", "--porcelain", "--untracked-files=all"))
            result = self.build()
            with self.subTest(flag=flag):
                self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_git_export_attributes_do_not_substitute_or_omit_tracked_blobs(self):
        (self.source / ".gitattributes").write_text("README.md export-ignore\ndocs/identity.txt export-subst\n")
        (self.source / "docs/identity.txt").write_text("$Format:%H$\n")
        self.git(self.source, "add", ".gitattributes", "docs/identity.txt")
        self.git(self.source, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "attributes are not release authority")
        result = self.build()
        with tarfile.open(result["artifact"], "r:gz") as archive:
            self.assertIsNotNone(archive.getmember("source/README.md"))
            self.assertEqual(b"$Format:%H$\n", archive.extractfile("source/docs/identity.txt").read())

    def test_local_replacement_ref_cannot_redefine_a_frozen_blob(self):
        original = self.git(self.source, "rev-parse", "HEAD:README.md")
        replacement = self.root / "replacement.txt"
        replacement.write_text("local replacement is not a commit blob\n")
        substituted = self.git(self.source, "hash-object", "-w", str(replacement))
        self.git(self.source, "replace", original, substituted)
        result = self.build()
        self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_dirty_developer_build_remains_explicitly_ineligible(self):
        with (self.source / "README.md").open("a") as stream:
            stream.write("developer edit\n")
        with self.assertRaisesRegex(ManifestError, "clean source"):
            self.build()
        result = release.build_release(Manifest.load(self.source), self.root / "developer",
                                       allow_unbound_snapshot=True)
        self.assertFalse(result["release_eligible"])
        self.assertEqual("git-working-tree-snapshot", result["source_provenance"]["kind"])
        self.assertFalse(release_contract.validate_release_artifact(Path(result["artifact"]))["release_eligible"])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink")
    def test_tracked_symlink_rejected_without_copying_its_target(self):
        (self.source / "docs/linked").symlink_to("../README.md")
        self.git(self.source, "add", "docs/linked")
        self.git(self.source, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "unsupported tracked type")
        with self.assertRaisesRegex(ManifestError, "unsupported.*type|symlinks"):
            self.build()

    def test_public_publish_plans_and_uploads_the_complete_verified_snapshot(self):
        artifact = self.root / Path(self.baseline["artifact"]).name
        artifact.write_bytes(self.baseline_bytes)
        checksum = artifact.with_name(artifact.name + ".sha256")
        checksum.write_text(hashlib.sha256(self.baseline_bytes).hexdigest() + "  " + artifact.name + "\n")
        version = self.baseline["version"]
        with mock.patch.object(release.shutil, "which", return_value="/fixture/gh"):
            plan = release.publish_release(version, "github", artifact, dry_run=True)
        self.assertEqual([artifact.name, checksum.name, "release-contract.json"],
                         [Path(value).name for value in plan["command"][4:7]])
        self.assertFalse((self.root / "release-contract.json").exists())
        capture = release_artifacts._verified_archive_snapshot
        observed = []

        def captured(path):
            value = capture(path)
            path.write_bytes(b"REPLACED AFTER VERIFICATION")
            return value

        def uploaded(command, **_kwargs):
            archive, sidecar, contract = map(Path, command[4:7])
            self.assertEqual(self.baseline_bytes, archive.read_bytes())
            self.assertEqual(hashlib.sha256(self.baseline_bytes).hexdigest(), sidecar.read_text().split()[0])
            data = json.loads(contract.read_text())
            self.assertEqual("adk-release-artifact-contract-set/v1", data["schema"])
            self.assertEqual(hashlib.sha256(self.baseline_bytes).hexdigest(), data["artifacts"][0]["artifact_sha256"])
            self.assertTrue(data["artifacts"][0]["release_eligible"])
            observed.append(archive)
            return mock.Mock(returncode=0, stdout="fixture publication", stderr="")

        with mock.patch.object(release_artifacts, "_verified_archive_snapshot", side_effect=captured), \
             mock.patch.object(release.shutil, "which", return_value="/fixture/gh"), \
             mock.patch.object(release.subprocess, "run", side_effect=uploaded):
            self.assertEqual("pass", release.publish_release(version, "github", artifact)["status"])
        self.assertEqual(1, len(observed))
        self.assertFalse(observed[0].exists())


if __name__ == "__main__":
    unittest.main()
