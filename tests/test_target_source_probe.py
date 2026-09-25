from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest
from agent_dev_kit.target_source_probe import probe_target_source

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)


class TargetSourceProbeTest(unittest.TestCase):
    def test_all_direct_targets_discover_and_load_isolated_core(self) -> None:
        for target in MANIFEST.direct_targets():
            with self.subTest(target=target):
                result = probe_target_source(MANIFEST, target, "core")
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["source_discovery"], "pass")
                self.assertEqual(result["source_load"], "pass")
                self.assertEqual(result["evidence_level"], "source-layout")
                self.assertFalse(result["native_runtime_evidence"])
                self.assertEqual(result["certification"], "not-certified")
                self.assertFalse(result["release_authorized"])
                self.assertGreater(result["files"], 0)
                self.assertGreater(result["bytes"], 0)

    def test_cli_and_invalid_target(self) -> None:
        target = sorted(MANIFEST.direct_targets())[0]
        done = subprocess.run(
            [sys.executable, "-m", "agent_dev_kit.cli", "target-source-probe",
             "--target", target, "--profile", "core", "--summary-json"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        value = json.loads(done.stdout)
        self.assertEqual(value["status"], "pass")
        self.assertFalse(value["native_runtime_evidence"])

        failed = subprocess.run(
            [sys.executable, "-m", "agent_dev_kit.cli", "target-source-probe",
             "--target", "missing-target", "--profile", "core", "--summary-json"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["status"], "fail")


if __name__ == "__main__":
    unittest.main()
