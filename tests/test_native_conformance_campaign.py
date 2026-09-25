from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.native_conformance_campaign import run_native_candidate

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)


def commands(path: Path, *, fail_stage: str | None = None, duplicate: bool = False, flood: bool = False) -> Path:
    stages = {}
    for stage in ("discovery", "load", "trigger"):
        if fail_stage == stage:
            code = "import sys; sys.exit(7)"
        elif flood and stage == "load":
            code = "import sys; sys.stdout.write('x'*200000)"
        else:
            label = "same" if duplicate else stage
            code = (
                "import os; assert os.path.isdir(os.environ['ADK_TARGET_ROOT']); "
                f"print('{label}-canary')"
            )
        stages[stage] = [sys.executable, "-c", code]
    path.write_text(json.dumps({"schema": "adk-native-target-campaign-commands/v1", "stages": stages}), encoding="utf-8")
    return path


class NativeConformanceCampaignTest(unittest.TestCase):
    def run_campaign(self, temp: Path, command_path: Path, **overrides):
        values = dict(
            manifest=MANIFEST,
            target="claude-code",
            profile="core",
            runtime_binary=Path(sys.executable),
            runtime_name="python3",
            runtime_version="3.11.0",
            commands_path=command_path,
            authority_id="owner-reviewed-native-candidate",
            execution_authority="human-approved",
            verification_backend="external-signature-verifier",
            output=temp / "receipt.json",
            timeout_seconds=30,
            max_output_bytes=64 * 1024,
        )
        values.update(overrides)
        return run_native_candidate(**values)

    def test_candidate_receipt_is_strict_but_never_certified(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            result = self.run_campaign(temp, commands(temp / "commands.json"))
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["certification"], "not-certified")
            self.assertFalse(result["promotion_eligible"])
            self.assertEqual(result["trust_verification"], "not-run")
            self.assertEqual(result["lifecycle_authority"], "none-evidence-only")
            self.assertFalse(result["release_authorized"])
            self.assertGreater(result["bundle_files"], 0)
            self.assertEqual(len(result["prospective_contract_sha256"]), 64)
            self.assertNotIn("discovery-canary", json.dumps(result))

            receipt_path = temp / "receipt.json"
            self.assertTrue(receipt_path.is_file())
            self.assertEqual(stat.S_IMODE(receipt_path.stat().st_mode), 0o600)
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(receipt["schema"], "adk-native-target-conformance-receipt/v1")
            self.assertEqual(receipt["target"], "claude-code")
            self.assertEqual(receipt["runtime"]["binary_sha256"], result["runtime"]["binary_sha256"])
            self.assertEqual(receipt["runtime"]["version"], receipt["runtime"]["version_pin"])
            self.assertEqual([item["stage"] for item in receipt["stages"]], ["discovery", "load", "trigger"])
            self.assertEqual(len({item["command_sha256"] for item in receipt["stages"]}), 3)
            self.assertEqual(len({item["result_sha256"] for item in receipt["stages"]}), 3)
            for item in receipt["stages"]:
                self.assertFalse(item["privacy"]["raw_content_stored"])
                self.assertFalse(item["privacy"]["secrets_stored"])
                self.assertTrue(item["privacy"]["sanitized"])
                self.assertEqual(item["authority"]["scope"], item["stage"])
                self.assertEqual(len(item["authority"]["attestation_sha256"]), 64)
            raw_receipt = receipt_path.read_text()
            for value in ("discovery-canary", "load-canary", "trigger-canary"):
                self.assertNotIn(value, raw_receipt)

    def test_public_cli_emits_candidate_without_certification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            command_path = commands(temp / "commands.json")
            output = temp / "cli-receipt.json"
            done = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_dev_kit.cli",
                    "target",
                    "native-campaign",
                    "--target",
                    "claude-code",
                    "--profile",
                    "core",
                    "--runtime-binary",
                    sys.executable,
                    "--runtime-name",
                    "python3",
                    "--runtime-version",
                    "3.11.0",
                    "--commands",
                    str(command_path),
                    "--authority-id",
                    "ci-native-candidate",
                    "--execution-authority",
                    "ci-approved",
                    "--verification-backend",
                    "ci-provenance-verifier",
                    "--output",
                    str(output),
                    "--timeout-seconds",
                    "30",
                    "--summary-json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=60,
            )
            self.assertEqual(done.returncode, 0, (done.stdout, done.stderr))
            value = json.loads(done.stdout)
            self.assertEqual(value["status"], "pass")
            self.assertEqual(value["trust_verification"], "not-run")
            self.assertEqual(value["certification"], "not-certified")
            self.assertFalse(value["promotion_eligible"])
            self.assertTrue(output.is_file())

    def test_nonzero_stage_fails_without_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            result = self.run_campaign(temp, commands(temp / "commands.json", fail_stage="load"))
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["stage"], "load")
            self.assertEqual(result["reason"], "runtime-nonzero-exit")
            self.assertFalse(result["receipt_written"])
            self.assertFalse((temp / "receipt.json").exists())

    def test_output_budget_is_fail_closed_and_raw_output_is_not_returned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            result = self.run_campaign(
                temp,
                commands(temp / "commands.json", flood=True),
                max_output_bytes=1024,
            )
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["reason"], "output-budget-exceeded")
            self.assertFalse(result["receipt_written"])
            self.assertNotIn("x" * 100, json.dumps(result))
            self.assertFalse((temp / "receipt.json").exists())

    def test_duplicate_stage_commands_are_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            path = commands(temp / "commands.json", duplicate=True)
            with self.assertRaisesRegex(ManifestError, "commands_must_be_independent"):
                self.run_campaign(temp, path)
            self.assertFalse((temp / "receipt.json").exists())

    def test_existing_output_and_missing_runtime_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            path = commands(temp / "commands.json")
            (temp / "receipt.json").write_text("{}")
            with self.assertRaisesRegex(ManifestError, "output_must_not_exist"):
                self.run_campaign(temp, path)
            (temp / "receipt.json").unlink()
            with self.assertRaisesRegex(ManifestError, "runtime_binary_missing"):
                self.run_campaign(temp, path, runtime_binary=temp / "missing-runtime")


if __name__ == "__main__":
    unittest.main()
