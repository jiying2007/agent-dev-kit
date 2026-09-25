from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.native_campaign import (
    finalize_campaign,
    prepare_campaign,
    run_campaign,
)
from agent_dev_kit.native_campaign_contract import load_native_campaign_target_layouts

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
VERSION = platform.python_version()
SENTINEL = "native-campaign-raw-output-sentinel"


def stage_command(
    stage: str,
    *,
    project_config_dir: str = ".claude",
    fail: bool = False,
    flood: bool = False,
) -> list[str]:
    code = (
        "import os,sys;"
        "from pathlib import Path;"
        "assert 'HOME' not in os.environ;"
        "assert os.environ['ADK_TARGET_SMOKE_STAGE']==sys.argv[1];"
        "project=Path(os.environ['ADK_TARGET_PROJECT_ROOT']).resolve();"
        "config=Path(os.environ['ADK_TARGET_ROOT']).resolve();"
        "assert Path.cwd().resolve()==project;"
        "assert config==project/sys.argv[2];"
        "assert config.is_dir();"
        "assert (config/'skills').is_dir();"
    )
    if flood:
        code += "sys.stdout.write('x'*(1024*1024+1));"
    else:
        code += f"print('{SENTINEL}-'+sys.argv[1]);"
    if fail:
        code += "sys.exit(7);"
    return [sys.executable, "-c", code, stage, project_config_dir]


def commands(
    *,
    project_config_dir: str = ".claude",
    fail_stage: str | None = None,
    flood_stage: str | None = None,
) -> dict[str, list[str]]:
    return {
        "version": [sys.executable, "--version"],
        **{
            stage: stage_command(
                stage,
                project_config_dir=project_config_dir,
                fail=stage == fail_stage,
                flood=stage == flood_stage,
            )
            for stage in ("discovery", "load", "trigger")
        },
    }


class NativeCampaignTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="adk-native-campaign-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp, ignore_errors=True))
        runtime_reports = ROOT / "reports" / "runtime"
        runtime_reports.mkdir(parents=True, exist_ok=True)
        self.receipt_dir = Path(
            tempfile.mkdtemp(prefix="native-campaign-test-", dir=runtime_reports)
        )
        self.addCleanup(lambda: shutil.rmtree(self.receipt_dir, ignore_errors=True))
        self.receipt = self.receipt_dir / "receipt.json"
        self.receipt_rel = self.receipt.relative_to(ROOT).as_posix()
        self.active = ROOT / "manifests" / "target-contracts" / "claude-code.json"
        self.active_before = self.active.read_bytes()

    def prepare(
        self,
        command_set: dict[str, list[str]] | None = None,
        runtime_version: str = VERSION,
        target: str = "claude-code",
    ):
        return prepare_campaign(
            MANIFEST,
            target=target,
            profile="core",
            runtime_binary=Path(sys.executable),
            runtime_version=runtime_version,
            authority_id="ci-native-conformance",
            execution_authority="ci-approved",
            backend="ci-provenance-verifier",
            auth_mode="none",
            timeout_seconds=15,
            commands=command_set or commands(),
            receipt_path=self.receipt_rel,
        )

    def test_target_layout_manifest_covers_direct_targets(self) -> None:
        layouts = load_native_campaign_target_layouts(MANIFEST)
        self.assertEqual(set(layouts), set(MANIFEST.direct_targets()))
        self.assertEqual(layouts["claude-code"]["project_config_dir"], ".claude")
        self.assertEqual(layouts["opencode"]["project_config_dir"], ".opencode")
        self.assertTrue(all(item["discovery_scope"] == "project" for item in layouts.values()))

    def test_each_direct_target_runs_from_native_project_config_root(self) -> None:
        for target, config_dir in (("claude-code", ".claude"), ("opencode", ".opencode")):
            with self.subTest(target=target):
                command_set = commands(project_config_dir=config_dir)
                plan, candidate = self.prepare(command_set, target=target)
                evidence = run_campaign(
                    MANIFEST, plan, candidate, command_set, Path(sys.executable)
                )
                self.assertEqual(evidence["status"], "complete", evidence)
                self.assertEqual(
                    [item["status"] for item in evidence["stages"]],
                    ["pass", "pass", "pass"],
                )

    def test_api_complete_campaign_finalizes_without_raw_output_or_active_write(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, Path(sys.executable))
        self.assertEqual(evidence["status"], "complete", evidence)
        self.assertEqual([item["status"] for item in evidence["stages"]], ["pass", "pass", "pass"])
        self.assertNotIn(SENTINEL, json.dumps(evidence, ensure_ascii=False))

        result, receipt, final_contract = finalize_campaign(
            MANIFEST, plan, candidate, evidence, self.receipt
        )
        self.assertEqual(result["status"], "ready-for-signature-and-registry")
        self.assertFalse(result["release_authorized"])
        self.assertEqual(receipt["schema"], "adk-native-target-conformance-receipt/v1")
        self.assertEqual(
            [item["stage"] for item in receipt["stages"]],
            ["discovery", "load", "trigger"],
        )
        self.assertEqual(
            final_contract["adapter"]["conformance"]["evidence"][0]["receipt_schema"],
            receipt["schema"],
        )
        self.assertTrue(final_contract["adapter"]["conformance_trust_policy"]["enabled"])
        self.assertEqual(self.active.read_bytes(), self.active_before)

    def test_failed_stage_blocks_finalize_and_never_claims_release_authority(self) -> None:
        command_set = commands(fail_stage="load")
        plan, candidate = self.prepare(command_set)
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, Path(sys.executable))
        self.assertEqual(evidence["status"], "failed", evidence)
        self.assertEqual(
            [item["status"] for item in evidence["stages"]],
            ["pass", "fail", "blocked"],
        )
        self.assertFalse(evidence["release_authorized"])
        with self.assertRaisesRegex(ManifestError, "requires_complete_campaign"):
            finalize_campaign(MANIFEST, plan, candidate, evidence, self.receipt)
        self.assertEqual(self.active.read_bytes(), self.active_before)

    def test_version_mismatch_is_blocked_before_stages(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set, runtime_version="999.999")
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, Path(sys.executable))
        self.assertEqual(evidence["status"], "blocked", evidence)
        self.assertEqual(evidence["reason"], "runtime-version-probe-failed")
        self.assertEqual(evidence["stages"], [])

    def test_command_drift_and_output_flood_fail_closed(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        drifted = commands()
        drifted["load"] = [sys.executable, "-c", "raise SystemExit(0)", "load"]
        with self.assertRaisesRegex(ManifestError, "command_drift"):
            run_campaign(MANIFEST, plan, candidate, drifted, Path(sys.executable))

        flood = commands(flood_stage="discovery")
        flood_plan, flood_candidate = self.prepare(flood)
        evidence = run_campaign(
            MANIFEST, flood_plan, flood_candidate, flood, Path(sys.executable)
        )
        self.assertEqual(evidence["status"], "failed", evidence)
        self.assertIn("output_budget_exceeded", evidence["stages"][0]["reason"])


    def test_finalize_rejects_evidence_identity_and_stage_command_drift(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, Path(sys.executable))
        self.assertEqual(evidence["status"], "complete", evidence)

        changed_identity = json.loads(json.dumps(evidence))
        changed_identity["bundle_sha256"] = "0" * 64
        with self.assertRaisesRegex(ManifestError, "evidence_identity_mismatch"):
            finalize_campaign(MANIFEST, plan, candidate, changed_identity, self.receipt)

        changed_command = json.loads(json.dumps(evidence))
        changed_command["stages"][1]["command_sha256"] = "f" * 64
        with self.assertRaisesRegex(ManifestError, "stage_command_mismatch"):
            finalize_campaign(MANIFEST, plan, candidate, changed_command, self.receipt)



    def test_prepare_requires_governed_runtime_report_path(self) -> None:
        with self.assertRaisesRegex(
            ManifestError, "receipt_path_must_be_under_reports_runtime"
        ):
            prepare_campaign(
                MANIFEST,
                target="claude-code",
                profile="core",
                runtime_binary=Path(sys.executable),
                runtime_version=VERSION,
                authority_id="ci-native-conformance",
                execution_authority="ci-approved",
                backend="ci-provenance-verifier",
                auth_mode="none",
                timeout_seconds=15,
                commands=commands(),
                receipt_path="manifests/target-contracts/claude-code.json",
            )

    def test_prepare_rejects_relative_or_non_runtime_stage_executable(self) -> None:
        relative = commands()
        relative["load"][0] = "python3"
        with self.assertRaisesRegex(ManifestError, "requires_absolute_runtime"):
            self.prepare(relative)

        not_runtime = commands()
        foreign = self.temp / "foreign-runtime"
        foreign.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        foreign.chmod(0o755)
        not_runtime["trigger"][0] = str(foreign)
        with self.assertRaisesRegex(ManifestError, "must_use_runtime_binary"):
            self.prepare(not_runtime)


    def test_cli_rejects_repository_output_outside_runtime_reports(self) -> None:
        commands_path = self.temp / "commands.json"
        commands_path.write_text(json.dumps(commands()), encoding="utf-8")
        done = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_dev_kit.cli",
                "native-campaign",
                "--root",
                str(ROOT),
                "prepare",
                "--target",
                "claude-code",
                "--runtime-binary",
                sys.executable,
                "--runtime-version",
                VERSION,
                "--authority-id",
                "ci-native-conformance",
                "--execution-authority",
                "ci-approved",
                "--verification-backend",
                "ci-provenance-verifier",
                "--commands-json",
                str(commands_path),
                "--receipt-path",
                self.receipt_rel,
                "--plan-out",
                str(ROOT / "manifests" / "forbidden-plan.json"),
                "--candidate-contract-out",
                str(self.temp / "candidate.json"),
                "--summary-json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(done.returncode, 1, (done.stdout, done.stderr))
        value = json.loads(done.stdout)
        self.assertIn("repository_output_must_be_reports_runtime", value["error"])
        self.assertFalse((ROOT / "manifests" / "forbidden-plan.json").exists())

    def test_public_cli_prepare_run_finalize(self) -> None:
        commands_path = self.temp / "commands.json"
        plan_path = self.temp / "plan.json"
        candidate_path = self.temp / "candidate.json"
        evidence_path = self.temp / "evidence.json"
        final_contract_path = self.temp / "final-contract.json"
        commands_path.write_text(json.dumps(commands()), encoding="utf-8")

        def invoke(*args: str, expected: int = 0) -> dict:
            done = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_dev_kit.cli",
                    "native-campaign",
                    "--root",
                    str(ROOT),
                    *args,
                    "--summary-json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=90,
            )
            self.assertEqual(done.returncode, expected, (done.stdout, done.stderr))
            return json.loads(done.stdout)

        prepared = invoke(
            "prepare",
            "--target", "claude-code",
            "--profile", "core",
            "--runtime-binary", sys.executable,
            "--runtime-version", VERSION,
            "--authority-id", "ci-native-conformance",
            "--execution-authority", "ci-approved",
            "--verification-backend", "ci-provenance-verifier",
            "--auth-mode", "none",
            "--commands-json", str(commands_path),
            "--receipt-path", self.receipt_rel,
            "--plan-out", str(plan_path),
            "--candidate-contract-out", str(candidate_path),
        )
        self.assertEqual(prepared["status"], "ready")

        ran = invoke(
            "run",
            "--plan", str(plan_path),
            "--candidate-contract", str(candidate_path),
            "--commands-json", str(commands_path),
            "--runtime-binary", sys.executable,
            "--evidence-out", str(evidence_path),
        )
        self.assertEqual(ran["status"], "complete")

        finalized = invoke(
            "finalize",
            "--plan", str(plan_path),
            "--candidate-contract", str(candidate_path),
            "--evidence", str(evidence_path),
            "--receipt-out", str(self.receipt),
            "--final-contract-out", str(final_contract_path),
        )
        self.assertEqual(finalized["status"], "ready-for-signature-and-registry")
        self.assertTrue(self.receipt.is_file())
        self.assertTrue(final_contract_path.is_file())
        self.assertEqual(
            hashlib.sha256(self.receipt.read_bytes()).hexdigest(),
            finalized["receipt_sha256"],
        )
        self.assertEqual(self.active.read_bytes(), self.active_before)

        refused = invoke(
            "finalize",
            "--plan", str(plan_path),
            "--candidate-contract", str(candidate_path),
            "--evidence", str(evidence_path),
            "--receipt-out", str(self.receipt),
            "--final-contract-out", str(self.active),
            expected=1,
        )
        self.assertEqual(refused["status"], "fail")
        self.assertIn("repository_output_must_be_reports_runtime", refused["error"])
        self.assertEqual(self.active.read_bytes(), self.active_before)


if __name__ == "__main__":
    unittest.main()
