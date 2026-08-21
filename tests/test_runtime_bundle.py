from __future__ import annotations

import hashlib
import json
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.release import _copy_runtime_skill, build_runtime_bundle


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


if __name__ == "__main__":
    unittest.main()
