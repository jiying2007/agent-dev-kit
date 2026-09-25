from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest
from agent_dev_kit.profile_context_footprint import compare_profiles, profile_footprint

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)


class ProfileContextFootprintTest(unittest.TestCase):
    def test_all_profiles_are_deterministic_and_partition_entry_from_support(self) -> None:
        profiles = sorted(MANIFEST.data["profiles"])
        for name in profiles:
            with self.subTest(profile=name):
                first = profile_footprint(MANIFEST, name)
                second = profile_footprint(MANIFEST, name)
                self.assertEqual(first, second)
                self.assertEqual(first["status"], "pass")
                self.assertFalse(first["accounting"]["runtime_initial_context_measured"])
                self.assertFalse(first["frontmatter_surface"]["token_estimate_is_provider_measurement"])
                self.assertEqual(
                    first["potential_full_source_surface"]["bytes"],
                    first["entry_file_surface"]["bytes"] + first["deferred_support_surface"]["bytes"],
                )
                self.assertEqual(
                    first["entry_file_surface"]["bytes"],
                    first["frontmatter_surface"]["bytes"] + first["entry_body_surface"]["bytes"],
                )
                self.assertGreater(first["assets"]["total"], 0)
                self.assertGreater(first["entry_file_surface"]["bytes"], 0)

    def test_embedded_delta_is_explicit_not_a_quality_score(self) -> None:
        value = compare_profiles(MANIFEST, "core", "embedded-fullstack")
        self.assertEqual(value["status"], "pass")
        self.assertEqual(value["lifecycle_authority"], "none-evidence-only")
        self.assertFalse(value["release_authorized"])
        self.assertGreater(value["delta"]["assets"], 0)
        self.assertGreater(value["delta"]["entry_file_bytes"], 0)
        self.assertIn("not native runtime loading evidence", value["limitations"][0])

    def test_cli_matches_library_and_unknown_profile_fails(self) -> None:
        command = [
            sys.executable, "-m", "agent_dev_kit.cli", "profile-footprint",
            "--profile", "core", "--compare", "embedded-fullstack", "--summary-json",
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        cli = json.loads(completed.stdout)
        self.assertEqual(cli, compare_profiles(MANIFEST, "core", "embedded-fullstack"))

        failed = subprocess.run(
            [sys.executable, "-m", "agent_dev_kit.cli", "profile-footprint",
             "--profile", "missing-profile", "--summary-json"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["status"], "fail")


if __name__ == "__main__":
    unittest.main()
