from __future__ import annotations

import asyncio
import contextlib
import hashlib
import io
import os
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.native_campaign import (
    _safe_output_path,
    finalize_campaign,
    main as native_campaign_main,
    prepare_campaign,
    run_campaign,
)
from agent_dev_kit.native_campaign_contract import _write_json, load_native_campaign_target_layouts
from agent_dev_kit.native_campaign_execution import _execute, _semantic_assertion

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
VERSION = platform.python_version()
SENTINEL = hashlib.sha256(b"semantic:discovery").hexdigest()


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
        code += "import hashlib;print(hashlib.sha256(('semantic:'+sys.argv[1]).encode()).hexdigest());"
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


def assertions(*, mismatch_stage: str | None = None) -> dict[str, dict[str, object]]:
    return {
        stage: {
            "stream": "stdout",
            "contains": (
                "semantic-assertion-mismatch"
                if stage == mismatch_stage
                else hashlib.sha256(f"semantic:{stage}".encode()).hexdigest()
            ),
            "case_sensitive": True,
        }
        for stage in ("discovery", "load", "trigger")
    }


class NativeCampaignOutputBudgetTest(unittest.TestCase):
    def test_combined_streams_at_exact_budget_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-dual-stream-") as temp:
            result = _execute(
                [sys.executable, "-c", "import sys;sys.stdout.write('A'*8);sys.stderr.write('B'*8)"],
                cwd=Path(temp),
                env={},
                timeout_seconds=10,
                output_limit=16,
            )
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout_bytes"] + result["stderr_bytes"], 16)

    def test_combined_streams_exceed_one_shared_budget(self) -> None:
        # Each individual stream is below the budget. Their sum must still
        # fail closed so real native-runtime output cannot consume 2x policy.
        with tempfile.TemporaryDirectory(prefix="native-dual-stream-") as temp:
            with self.assertRaisesRegex(ManifestError, "native_campaign_output_budget_exceeded"):
                _execute(
                    [sys.executable, "-c", "import sys;sys.stdout.write('A'*9);sys.stderr.write('B'*8)"],
                    cwd=Path(temp),
                    env={},
                    timeout_seconds=10,
                    output_limit=16,
                )


    @unittest.skipUnless(os.name == "posix", "requires a native POSIX process group")
    def test_exited_launcher_cannot_escape_pipe_drain_deadline(self) -> None:
        # The direct launcher exits quickly, but its grandchild keeps both
        # pipes open for three seconds. The one-second execution deadline
        # must cover the drains, not just the direct child's process.wait().
        launcher = (
            "import subprocess,sys;"
            "subprocess.Popen([sys.executable,'-c','import time;time.sleep(3)'],"
            "stdin=subprocess.DEVNULL,stdout=sys.stdout,stderr=sys.stderr);"
            "print('launcher-exited',flush=True)"
        )
        with tempfile.TemporaryDirectory(prefix="native-grandchild-deadline-") as temp:
            with self.assertRaises(asyncio.TimeoutError):
                _execute(
                    [sys.executable, "-c", launcher],
                    cwd=Path(temp),
                    env={},
                    timeout_seconds=1,
                    output_limit=4096,
                )



class NativeCampaignBoundaryTest(unittest.TestCase):
    def test_combined_assertion_uses_lf_separator_not_literal_backslash_n(self) -> None:
        result = {"stdout": b"alpha", "stderr": b"beta"}
        common = {"stream": "combined", "case_sensitive": True}
        matched, _ = _semantic_assertion(
            "discovery", result, {**common, "contains": "alpha\nbeta"}
        )
        self.assertTrue(matched)
        mistaken_match, _ = _semantic_assertion(
            "discovery", result, {**common, "contains": r"alpha\nbeta"}
        )
        self.assertFalse(mistaken_match)

    def test_json_writer_does_not_resolve_leaf_symlink_before_rejecting(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-output-link-") as temp:
            target = Path(temp) / "target.json"
            alias = Path(temp) / "alias.json"
            target.write_text("original\n", encoding="utf-8")
            try:
                alias.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(ManifestError, "output path must not be a symlink"):
                _write_json(alias, {"status": "should-not-write"})
            self.assertEqual(target.read_text(encoding="utf-8"), "original\n")


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

    def test_repository_output_rejects_same_root_symlink_aliases(self) -> None:
        target_dir = self.receipt_dir / "real"
        target_dir.mkdir()
        leaf = target_dir / "target.json"
        leaf.write_text("untouched\n", encoding="utf-8")
        direct_link = self.receipt_dir / "linked.json"
        parent_link = self.receipt_dir / "linked-dir"
        try:
            direct_link.symlink_to(leaf)
            parent_link.symlink_to(target_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        for path in (direct_link, parent_link / "candidate.json"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ManifestError, "native_campaign_output_symlink_path"):
                    _safe_output_path(MANIFEST, str(path), "test-out")
        self.assertEqual(leaf.read_text(encoding="utf-8"), "untouched\n")

    def prepare(
        self,
        command_set: dict[str, list[str]] | None = None,
        assertion_set: dict[str, dict[str, object]] | None = None,
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
            assertions=assertion_set or assertions(),
            receipt_path=self.receipt_rel,
        )

    def test_target_layout_manifest_covers_direct_targets(self) -> None:
        layouts = load_native_campaign_target_layouts(MANIFEST)
        self.assertEqual(set(layouts), set(MANIFEST.direct_targets()))
        self.assertEqual(layouts["claude-code"]["project_config_dir"], ".claude")
        self.assertEqual(layouts["opencode"]["project_config_dir"], ".opencode")
        self.assertTrue(all(item["discovery_scope"] == "project" for item in layouts.values()))

    def test_target_layout_manifest_fails_closed_on_missing_or_unsafe_mapping(self) -> None:
        source = json.loads(
            (ROOT / "manifests" / "native_campaign_target_layouts.json").read_text(
                encoding="utf-8"
            )
        )
        missing = json.loads(json.dumps(source))
        del missing["targets"]["opencode"]
        with patch(
            "agent_dev_kit.native_campaign_contract._load_json",
            return_value=missing,
        ):
            with self.assertRaisesRegex(ManifestError, "must_cover_direct_targets"):
                load_native_campaign_target_layouts(MANIFEST)

        unsafe = json.loads(json.dumps(source))
        unsafe["targets"]["claude-code"]["project_config_dir"] = ".claude/../escape"
        with patch(
            "agent_dev_kit.native_campaign_contract._load_json",
            return_value=unsafe,
        ):
            with self.assertRaisesRegex(ManifestError, "project_config_dir_invalid"):
                load_native_campaign_target_layouts(MANIFEST)

    def test_each_direct_target_runs_from_native_project_config_root(self) -> None:
        for target, config_dir in (("claude-code", ".claude"), ("opencode", ".opencode")):
            with self.subTest(target=target):
                command_set = commands(project_config_dir=config_dir)
                plan, candidate = self.prepare(command_set, target=target)
                evidence = run_campaign(
                    MANIFEST, plan, candidate, command_set, assertions(), Path(sys.executable)
                )
                self.assertEqual(evidence["status"], "complete", evidence)
                self.assertEqual(
                    [item["status"] for item in evidence["stages"]],
                    ["pass", "pass", "pass"],
                )

    def test_api_complete_campaign_finalizes_without_raw_output_or_active_write(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, assertions(), Path(sys.executable))
        self.assertEqual(evidence["status"], "complete", evidence)
        self.assertEqual([item["status"] for item in evidence["stages"]], ["pass", "pass", "pass"])
        self.assertEqual(
            len({item["assertion_result_sha256"] for item in evidence["stages"]}),
            3,
            evidence,
        )
        self.assertNotIn(SENTINEL, json.dumps(evidence, ensure_ascii=False))

        result, receipt, final_contract = finalize_campaign(
            MANIFEST, plan, candidate, evidence, self.receipt
        )
        self.assertEqual(result["status"], "ready-for-signature-and-registry")
        self.assertFalse(result["release_authorized"])
        self.assertEqual(receipt["schema"], "adk-native-target-conformance-receipt/v2")
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
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, assertions(), Path(sys.executable))
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
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, assertions(), Path(sys.executable))
        self.assertEqual(evidence["status"], "blocked", evidence)
        self.assertEqual(evidence["reason"], "runtime-version-probe-failed")
        self.assertEqual(evidence["stages"], [])

    def test_command_drift_and_output_flood_fail_closed(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        drifted = commands()
        drifted["load"] = [sys.executable, "-c", "raise SystemExit(0)", "load"]
        with self.assertRaisesRegex(ManifestError, "command_drift"):
            run_campaign(MANIFEST, plan, candidate, drifted, assertions(), Path(sys.executable))

        flood = commands(flood_stage="discovery")
        flood_plan, flood_candidate = self.prepare(flood)
        evidence = run_campaign(
            MANIFEST, flood_plan, flood_candidate, flood, assertions(), Path(sys.executable)
        )
        self.assertEqual(evidence["status"], "failed", evidence)
        self.assertIn("output_budget_exceeded", evidence["stages"][0]["reason"])


    def test_assertion_canary_cannot_be_embedded_in_stage_command(self) -> None:
        command_set = commands()
        assertion_set = assertions()
        exposed = assertion_set["load"]["contains"]
        command_set["load"] = [
            sys.executable,
            "-c",
            f"print({exposed!r})",
            "load",
        ]
        with self.assertRaisesRegex(
            ManifestError, "assertion_canary_exposed_in_command"
        ):
            self.prepare(command_set, assertion_set=assertion_set)


    def test_exit_zero_without_semantic_match_fails_closed(self) -> None:
        command_set = commands()
        assertion_set = assertions(mismatch_stage="load")
        plan, candidate = self.prepare(command_set, assertion_set=assertion_set)
        evidence = run_campaign(
            MANIFEST,
            plan,
            candidate,
            command_set,
            assertion_set,
            Path(sys.executable),
        )
        self.assertEqual(evidence["status"], "failed", evidence)
        self.assertEqual(
            [item["status"] for item in evidence["stages"]],
            ["pass", "fail", "blocked"],
        )
        self.assertEqual(evidence["stages"][1]["exit_code"], 0)
        self.assertEqual(
            evidence["stages"][1]["semantic_assertion_status"], "fail"
        )
        self.assertEqual(
            evidence["stages"][1]["reason"], "semantic-assertion-failed"
        )
        self.assertEqual(
            evidence["stages"][2]["semantic_assertion_status"], "not-run"
        )
        with self.assertRaisesRegex(ManifestError, "requires_complete_campaign"):
            finalize_campaign(MANIFEST, plan, candidate, evidence, self.receipt)


    def test_finalize_rejects_evidence_identity_and_stage_command_drift(self) -> None:
        command_set = commands()
        plan, candidate = self.prepare(command_set)
        evidence = run_campaign(MANIFEST, plan, candidate, command_set, assertions(), Path(sys.executable))
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
                assertions=assertions(),
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
        assertions_path = self.temp / "assertions.json"
        commands_path.write_text(json.dumps(commands()), encoding="utf-8")
        assertions_path.write_text(json.dumps(assertions()), encoding="utf-8")
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
                "--assertions-json",
                str(assertions_path),
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

    def prepare_cli(self, plan_path: Path, candidate_path: Path) -> subprocess.CompletedProcess:
        commands_path = self.temp / "commands.json"
        assertions_path = self.temp / "assertions.json"
        commands_path.write_text(json.dumps(commands()), encoding="utf-8")
        assertions_path.write_text(json.dumps(assertions()), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable, "-m", "agent_dev_kit.cli", "native-campaign",
                "--root", str(ROOT), "prepare", "--target", "claude-code",
                "--runtime-binary", sys.executable, "--runtime-version", VERSION,
                "--authority-id", "ci-native-conformance",
                "--execution-authority", "ci-approved",
                "--verification-backend", "ci-provenance-verifier",
                "--commands-json", str(commands_path),
                "--assertions-json", str(assertions_path),
                "--receipt-path", self.receipt_rel,
                "--plan-out", str(plan_path),
                "--candidate-contract-out", str(candidate_path), "--summary-json",
            ],
            cwd=ROOT, text=True, capture_output=True, timeout=60,
        )

    def test_cli_prepare_rejects_external_output_leaf_symlinks(self) -> None:
        for linked_output in ("plan", "candidate"):
            for target_exists in (True, False):
                with self.subTest(linked_output=linked_output, target_exists=target_exists):
                    case = self.temp / f"{linked_output}-{target_exists}"
                    case.mkdir()
                    target = case / "target.json"
                    alias = case / "alias.json"
                    companion = case / "companion.json"
                    if target_exists:
                        target.write_bytes(b"original-target\n")
                    try:
                        alias.symlink_to(target)
                    except (OSError, NotImplementedError):
                        self.skipTest("symlink creation is unavailable")
                    plan, candidate = (
                        (alias, companion) if linked_output == "plan" else (companion, alias)
                    )
                    done = self.prepare_cli(plan, candidate)
                    self.assertEqual(done.returncode, 1, (done.stdout, done.stderr))
                    self.assertIn("native_campaign_output_symlink_path", json.loads(done.stdout)["error"])
                    self.assertTrue(alias.is_symlink())
                    self.assertEqual(os.readlink(alias), str(target))
                    if target_exists:
                        self.assertEqual(target.read_bytes(), b"original-target\n")
                    else:
                        self.assertFalse(target.exists())
                    self.assertFalse(companion.exists())

    def test_cli_prepare_preserves_regular_external_output_support(self) -> None:
        plan, candidate = self.temp / "plan.json", self.temp / "candidate.json"
        plan.write_bytes(b"old-plan\n")
        candidate.write_bytes(b"old-candidate\n")
        done = self.prepare_cli(plan, candidate)
        self.assertEqual(done.returncode, 0, (done.stdout, done.stderr))
        self.assertEqual(json.loads(done.stdout)["status"], "ready")
        self.assertEqual(json.loads(plan.read_text())["schema"], "adk-native-target-campaign-plan/v2")
        self.assertEqual(json.loads(candidate.read_text())["target"], "claude-code")

    def test_run_rejects_external_output_leaf_before_campaign(self) -> None:
        plan, candidate = self.prepare()
        inputs = {
            "plan": plan, "candidate": candidate,
            "commands": commands(), "assertions": assertions(),
        }
        for name, value in inputs.items():
            (self.temp / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        for target_exists in (True, False):
            with self.subTest(target_exists=target_exists):
                target = self.temp / f"run-target-{target_exists}.json"
                alias = self.temp / f"run-alias-{target_exists}.json"
                if target_exists:
                    target.write_bytes(b"original-evidence\n")
                try:
                    alias.symlink_to(target)
                except (OSError, NotImplementedError):
                    self.skipTest("symlink creation is unavailable")
                output = io.StringIO()
                with patch(
                    "agent_dev_kit.native_campaign.run_campaign",
                    side_effect=ManifestError("fixture-runner-must-not-be-called"),
                ) as runner, contextlib.redirect_stdout(output):
                    code = native_campaign_main([
                        "--root", str(ROOT), "run",
                        "--plan", str(self.temp / "plan.json"),
                        "--candidate-contract", str(self.temp / "candidate.json"),
                        "--commands-json", str(self.temp / "commands.json"),
                        "--assertions-json", str(self.temp / "assertions.json"),
                        "--runtime-binary", sys.executable,
                        "--evidence-out", str(alias), "--summary-json",
                    ])
                self.assertEqual(code, 1)
                runner.assert_not_called()
                self.assertIn("native_campaign_output_symlink_path", json.loads(output.getvalue())["error"])
                self.assertTrue(alias.is_symlink())
                if target_exists:
                    self.assertEqual(target.read_bytes(), b"original-evidence\n")
                else:
                    self.assertFalse(target.exists())

    def test_public_cli_prepare_run_finalize(self) -> None:
        commands_path = self.temp / "commands.json"
        assertions_path = self.temp / "assertions.json"
        plan_path = self.temp / "plan.json"
        candidate_path = self.temp / "candidate.json"
        evidence_path = self.temp / "evidence.json"
        final_contract_path = self.temp / "final-contract.json"
        commands_path.write_text(json.dumps(commands()), encoding="utf-8")
        assertions_path.write_text(json.dumps(assertions()), encoding="utf-8")

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
            "--assertions-json", str(assertions_path),
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
            "--assertions-json", str(assertions_path),
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
