from __future__ import annotations

import hashlib
import json
import os
import sys
import tarfile
import tempfile
import unittest
import importlib.util
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.distribution.release_artifacts import _copy_runtime_skill
from agent_dev_kit.release import build_runtime_bundle


class RuntimeBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = Manifest.load(ROOT)

    def test_team_bundle_is_deterministic_and_source_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            one = build_runtime_bundle(self.manifest, first, "team-core")
            two = build_runtime_bundle(self.manifest, second, "team-core")
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertEqual(
                hashlib.sha256(Path(one["artifact"]).read_bytes()).hexdigest(),
                one["sha256"],
            )
            with tarfile.open(one["artifact"], "r:gz") as archive:
                names = archive.getnames()
                self.assertIn("bundle-manifest.json", names)
                self.assertIn("checksums.sha256", names)
                self.assertTrue(any(name.startswith("skills/adk-cross-team-handoff/1.0.0/") for name in names))
                forbidden = ("src/agent_dev_kit", "tests/", ".github/", "docs/changes/", "source/")
                self.assertFalse(any(name.startswith(forbidden) for name in names))
                manifest = json.load(archive.extractfile("bundle-manifest.json"))
            self.assertEqual(manifest["schema"], "adk-runtime-bundle/v1")
            self.assertFalse(manifest["source_distribution"])
            self.assertEqual(manifest["profile"], "team-core")
            self.assertIn("adk-cross-team-handoff", {item["name"] for item in manifest["assets"]})

    def test_runtime_skill_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("---\nname: sample\nversion: 1.0.0\n---\n", encoding="utf-8")
            os.symlink("SKILL.md", source / "linked.md")
            with self.assertRaisesRegex(ManifestError, "does not allow links"):
                _copy_runtime_skill(source, Path(temp) / "destination")

    def test_unknown_profile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ManifestError, "unknown profile"):
                build_runtime_bundle(self.manifest, Path(temp), "missing-profile")

    def test_identity_uses_isolated_clean_fixture_and_rejects_dirty_source(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "runtime_identity_test", ROOT / "scripts/verify-runtime-bundle-identity.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "source"
            fixture.mkdir()
            # Only ADK product/test surfaces enter this synthetic fixture.
            allowed = {"src", "scripts", "tests", "schemas", "manifests", "agents", "skills",
                       "optional-skills", "workflows", "profiles", "templates", "fixtures", "docs"}
            top_level = {"manifest.json", "pyproject.toml", ".version-lock", ".gitignore",
                         "README.md", "AGENTS.md", "CHANGELOG.md", "CONTEXT.md", "LICENSE", "OWNERS"}
            excluded = {".git", ".cache", "__pycache__"}
            if (ROOT / ".git").exists():
                names = subprocess.check_output(
                    ["git", "-C", str(ROOT), "ls-files", "--cached", "--others",
                     "--exclude-standard", "-z"], text=True).split("\0")
            else:
                # Docker parity exports source without Git metadata. Walk only
                # owned surfaces, pruning caches and links before descending.
                names = [name for name in top_level if (ROOT / name).is_file()]
                for surface in sorted(allowed):
                    directory = ROOT / surface
                    if not directory.is_dir() or directory.is_symlink():
                        continue
                    for current, directories, files in os.walk(directory, followlinks=False):
                        directories[:] = sorted(
                            name for name in directories
                            if not name.startswith(".") and name not in excluded
                            and not (Path(current) / name).is_symlink())
                        names.extend(str((Path(current) / name).relative_to(ROOT))
                                     for name in files if not name.startswith("."))
            for name in sorted(set(names)):
                if not name or ("/" in name and name.split("/", 1)[0] not in allowed):
                    continue
                if "/" not in name and name not in top_level:
                    continue
                if excluded.intersection(Path(name).parts):
                    continue
                source = ROOT / name
                if not source.is_file() or source.is_symlink():
                    continue
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            subprocess.run(["git", "init", "-q", str(fixture)], check=True)
            subprocess.run(["git", "-C", str(fixture), "add", "."], check=True)
            subprocess.run(["git", "-C", str(fixture), "-c", "user.name=Fixture",
                            "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
                            "commit", "-qm", "synthetic identity fixture"], check=True)
            manifest = Manifest.load(fixture)
            receipt = module.verify_runtime_bundle_identity(manifest, "embedded-fullstack")
            self.assertEqual(receipt["status"], "pass")
            self.assertTrue(receipt["reproducible"])
            self.assertEqual(receipt["independent_builds"], 2)
            (fixture / "README.md").write_text("dirty fixture\n")
            with self.assertRaisesRegex(ManifestError, "clean"):
                module.verify_runtime_bundle_identity(manifest, "embedded-fullstack")


if __name__ == "__main__":
    unittest.main()
