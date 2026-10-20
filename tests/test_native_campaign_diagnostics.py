from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import platform
import re
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from agent_dev_kit.model import Manifest
from agent_dev_kit.native_campaign import prepare_campaign
from agent_dev_kit.native_campaign_contract import EVIDENCE_SCHEMA, MAX_JSON_BYTES
from agent_dev_kit.native_campaign_diagnostics import (
    INPUTS,
    MAX_DIAGNOSTIC_BYTES,
    PHASES,
    DiagnosticsError,
    collect_diagnostics,
    main,
)

ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64
# Non-secret test sentinel, assembled at runtime; every redaction assertion uses the same value.
SECRET = "_".join(("DO", "NOT", "RETAIN", "PRIVATE", "CANARY", "81c17"))


def phases(failed: str = "run") -> dict[str, str]:
    index = PHASES.index(failed)
    return {
        name: "success" if position < index else "failure" if position == index else "skipped"
        for position, name in enumerate(PHASES)
    }


def evidence(plan: dict, *, complete: bool = False) -> dict:
    observation = {
        "exit_code": 0, "duration_ms": 12, "stdout_bytes": 3, "stderr_bytes": 0,
        "stdout_sha256": HASH, "stderr_sha256": HASH,
    }
    stages = []
    for name in ("discovery", "load", "trigger"):
        stage = {
            "stage": name, "status": "pass", "command_sha256": HASH,
            "assertion_sha256": HASH, "assertion_result_sha256": HASH,
            "semantic_assertion_status": "pass", "result_sha256": HASH,
            "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:00:01Z",
            **observation,
            "environment": {
                "platform": "fixture", "architecture": "fixture", "cwd_sha256": HASH,
                "environment_sha256": HASH, "runtime_binary_sha256": HASH, "bundle_sha256": HASH,
            },
            "privacy": {"raw_content_stored": False, "secrets_stored": False, "sanitized": True},
        }
        if not complete and name == "load":
            stage.update(status="fail", reason="semantic-assertion-failed", semantic_assertion_status="fail")
        if not complete and name == "trigger":
            stage = {
                "stage": name, "status": "blocked", "reason": "previous-stage-failed",
                "command_sha256": HASH, "assertion_sha256": HASH, "semantic_assertion_status": "not-run",
            }
        stages.append(stage)
    return {
        "schema": EVIDENCE_SCHEMA, "status": "complete" if complete else "failed",
        "campaign_id": plan["campaign_id"], "target": "claude-code", "profile": "core",
        "runtime": copy.deepcopy(plan["runtime"]), "bundle_sha256": plan["bundle_sha256"],
        "candidate_contract_normalized_sha256": plan["candidate_contract_normalized_sha256"],
        "version_probe": observation, "stages": stages,
        "privacy": {"raw_command_stored": False, "raw_output_stored": False, "credentials_stored": False},
        "completed_at": "2026-01-01T00:00:01Z", "lifecycle_authority": "none-campaign-only",
        "release_authorized": False,
    }


class NativeCampaignDiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Plan generation only. This Python fixture never invokes a Native runtime.
        commands = {
            name: [sys.executable, "-c", f"print('fixture-command-{name}')"]
            for name in ("discovery", "load", "trigger")
        }
        commands["version"] = [sys.executable, "--version"]
        cls.plan, _ = prepare_campaign(
            Manifest.load(ROOT), target="claude-code", profile="core",
            runtime_binary=Path(sys.executable), runtime_version=platform.python_version(),
            authority_id="ci-native-conformance", execution_authority="ci-approved",
            backend="ci-provenance-verifier", auth_mode="none", timeout_seconds=15,
            commands=commands,
            assertions={
                name: {"stream": "stdout", "contains": f"fixture-independent-canary-{name}", "case_sensitive": True}
                for name in ("discovery", "load", "trigger")
            },
            receipt_path="reports/runtime/diagnostic-test-fixture.json",
        )

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="native-diagnostics-test-")
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.campaign = self.temp / "campaign"
        self.campaign.mkdir()
        self.output = self.temp / "output"

    def write(self, name: str, value: object) -> bytes:
        raw = (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")
        (self.campaign / name).write_bytes(raw)
        return raw

    def collect(self, failed: str = "run", *, output: Path | None = None) -> dict:
        return collect_diagnostics(
            ROOT, self.campaign, output or self.output,
            source_sha="1" * 40, run_id="123", run_attempt="2", phases=phases(failed),
        )

    def test_semantic_failure_retains_observed_failure_and_not_run_phases(self) -> None:
        self.write("plan.json", self.plan)
        raw = self.write("evidence.json", evidence(self.plan))
        report = self.collect()
        self.assertEqual(report["status"], "failed-campaign-diagnostics")
        self.assertEqual(report["last_successful_phase"], "prepare")
        self.assertEqual(report["failed_phases"], ["run"])
        self.assertIn({"phase": "finalize", "outcome": "not-run"}, report["workflow_phases"])
        self.assertEqual(report["native_stages"][1]["reason_code"], "semantic-assertion-failed")
        self.assertEqual(report["native_stages"][1]["exit_code"], 0)
        self.assertEqual(report["native_stages"][2]["semantic_assertion_status"], "not-run")
        self.assertEqual(report["files"]["evidence.json"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["files"]["plan.json"]["status"], "accepted-metadata-only")
        self.assertEqual([path.name for path in self.output.iterdir()], ["diagnostics.json"])
        payload = (self.output / "diagnostics.json").read_bytes()
        self.assertLessEqual(len(payload), MAX_DIAGNOSTIC_BYTES)
        self.assertFalse(report["release_authorized"])
        self.assertEqual(report["lifecycle_authority"], "none-diagnostics-only")
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((self.output / "diagnostics.json").stat().st_mode), 0o600)

    def test_authentication_failure_needs_no_campaign_directory_or_fake_evidence(self) -> None:
        self.campaign.rmdir()
        report = self.collect("authenticate")
        self.assertEqual(report["last_successful_phase"], "credentials")
        self.assertTrue(all(item["status"] == "not-run" for item in report["native_stages"]))
        self.assertTrue(all(item["status"] == "missing" for item in report["files"].values()))

    def test_unavailable_execution_evidence_is_not_not_run_or_pass(self) -> None:
        report = self.collect()
        self.assertTrue(all(item["status"] == "evidence-unavailable" for item in report["native_stages"]))

    def test_empty_or_partial_failed_evidence_does_not_invent_not_run(self) -> None:
        for count in (0, 1):
            with self.subTest(observed_stages=count):
                value = evidence(self.plan)
                value["stages"] = value["stages"][:count]
                self.write("evidence.json", value)
                report = self.collect(output=self.temp / f"partial-{count}")
                self.assertEqual(report["files"]["evidence.json"]["status"], "accepted-metadata-only")
                self.assertTrue(all(
                    item["status"] == "evidence-unavailable" for item in report["native_stages"][count:]
                ))

    def test_later_signing_failure_does_not_promote_complete_observations(self) -> None:
        self.write("evidence.json", evidence(self.plan, complete=True))
        report = self.collect("sign")
        self.assertTrue(all(item["status"] == "pass" for item in report["native_stages"]))
        self.assertEqual(report["workflow_conclusion"], "failure")
        self.assertEqual(report["status"], "failed-campaign-diagnostics")
        self.assertEqual(report["failed_phases"], ["sign"])
        self.assertFalse(report["target_promotion_performed"])
        self.assertFalse(report["registry_promotion_performed"])
        self.assertFalse(report["release_authorized"])

    def test_file_for_an_unstarted_phase_is_rejected_without_reading(self) -> None:
        self.write("evidence.json", evidence(self.plan, complete=True))
        with patch("agent_dev_kit.native_campaign_diagnostics.read_bytes", side_effect=AssertionError("must not read")):
            report = self.collect("authenticate")
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "unexpected-file-for-not-run-phase")
        self.assertTrue(all(item["status"] == "not-run" for item in report["native_stages"]))

    def test_private_and_unknown_sibling_files_are_never_opened(self) -> None:
        for name in (
            "native-commands.json", "native-assertions.json", "anthropic-api-key", "settings.json",
            "stdout.txt", "stderr.txt", "receipt.json", "receipt.sigstore.json", "registry-candidate.json",
        ):
            (self.campaign / name).write_text(SECRET, encoding="utf-8")
        with patch("agent_dev_kit.native_campaign_diagnostics.read_bytes", side_effect=AssertionError("must not read")):
            report = self.collect()
        self.assertEqual(set(report["files"]), {item[0] for item in INPUTS})
        self.assertNotIn(SECRET, (self.output / "diagnostics.json").read_text(encoding="utf-8"))

    def test_schema_valid_free_text_is_withheld(self) -> None:
        value = evidence(self.plan)
        value["runtime"].update(binary=SECRET, version=SECRET, version_pin=SECRET)
        value["reason"] = SECRET
        value["stages"][0]["environment"]["platform"] = SECRET
        value["stages"][0]["environment"]["architecture"] = SECRET
        value["stages"][1]["reason"] = SECRET
        self.write("evidence.json", value)
        report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["status"], "accepted-metadata-only")
        self.assertEqual(report["native_stages"][1]["reason_code"], "detail-withheld")
        self.assertNotIn(SECRET, json.dumps(report))

    def test_error_summary_does_not_copy_error_text(self) -> None:
        self.write("run-summary.json", {
            "schema": "adk-native-target-campaign-error/v1", "status": "fail",
            "error": SECRET, "release_authorized": False,
        })
        report = self.collect()
        self.assertEqual(report["files"]["run-summary.json"]["observation"]["reason_code"],
                         "operation-error-detail-withheld")
        self.assertNotIn(SECRET, json.dumps(report))

    def test_prepare_summary_only_projects_status_and_digest(self) -> None:
        self.write("prepare-summary.json", {
            "schema": "adk-native-target-campaign-operation/v1", "status": "ready",
            "campaign_id": self.plan["campaign_id"], "plan": "/private/" + SECRET,
            "candidate_contract": "/private/" + SECRET,
            "candidate_contract_normalized_sha256": HASH, "release_authorized": False,
        })
        report = self.collect()
        self.assertEqual(report["files"]["prepare-summary.json"]["observation"], {
            "operation_status": "ready", "candidate_contract_normalized_sha256": HASH,
        })
        self.assertNotIn(SECRET, json.dumps(report))

    def test_exact_run_finalize_and_loader_summaries_are_accepted_without_raw_files(self) -> None:
        self.write("run-summary.json", evidence(self.plan, complete=True))
        self.write("finalize-summary.json", {
            "schema": "adk-native-target-campaign-finalize/v2",
            "status": "ready-for-signature-and-registry", "campaign_id": self.plan["campaign_id"],
            "target": "claude-code", "receipt_id": SECRET, "receipt_path": "/private/" + SECRET,
            "receipt_sha256": HASH, "contract_sha256": HASH, "bundle_sha256": HASH,
            "next_required_evidence": [
                "sigstore-or-reviewed-external-signature-bundle",
                "managed-trust-registry-receipt-binding",
                "production-loader-verification",
                "owner-reviewed-target-contract-promotion",
            ],
            "lifecycle_authority": "none-candidate-only", "release_authorized": False,
        })
        self.write("production-loader.json", {"status": "pass", "target": "claude-code", "digest": HASH})
        report = self.collect("package")
        for name in ("run-summary.json", "finalize-summary.json", "production-loader.json"):
            self.assertEqual(report["files"][name]["status"], "accepted-metadata-only")
        self.assertEqual(report["status"], "failed-campaign-diagnostics")
        self.assertNotIn(SECRET, json.dumps(report))
        self.assertEqual([path.name for path in self.output.iterdir()], ["diagnostics.json"])

    def test_unknown_fields_are_rejected_at_every_evidence_depth(self) -> None:
        for index, target in enumerate(("root", "runtime", "stage", "environment", "privacy")):
            with self.subTest(target=target):
                value = evidence(self.plan)
                destination = {
                    "root": value, "runtime": value["runtime"], "stage": value["stages"][0],
                    "environment": value["stages"][0]["environment"], "privacy": value["privacy"],
                }[target]
                destination["unknown_raw_text"] = SECRET
                self.write("evidence.json", value)
                report = self.collect(output=self.temp / f"out-{index}")
                self.assertEqual(report["files"]["evidence.json"]["reason_code"], "schema-rejected")
                self.assertNotIn(SECRET, json.dumps(report))

    def test_unknown_operation_summary_fields_are_rejected(self) -> None:
        self.write("run-summary.json", {
            "schema": "adk-native-target-campaign-error/v1", "status": "fail", "error": "failure",
            "release_authorized": False, "raw_stdout": SECRET,
        })
        report = self.collect()
        self.assertEqual(report["files"]["run-summary.json"]["status"], "rejected")
        self.assertNotIn(SECRET, json.dumps(report))

    def test_ambiguous_nonfinite_deep_and_invalid_json_are_rejected(self) -> None:
        examples = (
            b'{"status":"fail","status":"pass"}', b'{"secret":NaN}', b'{"secret":Infinity}',
            b'{"secret":1e999}', b'[' * 65 + b'0' + b']' * 65, b'\xff', b'not-json', b'[]',
        )
        for index, raw in enumerate(examples):
            with self.subTest(raw=raw[:40]):
                (self.campaign / "run-summary.json").write_bytes(raw)
                report = self.collect(output=self.temp / f"out-{index}")
                self.assertEqual(report["files"]["run-summary.json"]["status"], "rejected")
                self.assertNotIn("observation", report["files"]["run-summary.json"])

    def test_oversized_input_is_rejected_before_read(self) -> None:
        (self.campaign / "evidence.json").write_bytes(b"x" * (MAX_JSON_BYTES + 1))
        with patch("agent_dev_kit.native_campaign_diagnostics.read_bytes", side_effect=AssertionError("must not read")):
            report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "input-over-byte-budget")

    def test_numeric_projection_has_a_fixed_budget(self) -> None:
        value = evidence(self.plan)
        value["version_probe"]["duration_ms"] = 2 ** 63
        self.write("evidence.json", value)
        report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "invalid-observation-number")

    def test_duplicate_native_stages_are_not_accepted_as_an_ordered_trace(self) -> None:
        value = evidence(self.plan)
        value["stages"][1]["stage"] = "discovery"
        self.write("evidence.json", value)
        report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "ambiguous-native-stage-order")

    @unittest.skipUnless(os.name == "posix", "requires native POSIX symlinks")
    def test_leaf_symlink_is_rejected_without_reading_target(self) -> None:
        secret = self.temp / "private.json"
        secret.write_text(SECRET, encoding="utf-8")
        (self.campaign / "evidence.json").symlink_to(secret)
        with patch("agent_dev_kit.native_campaign_diagnostics.read_bytes", side_effect=AssertionError("must not read")):
            report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "unsafe-input-file")
        self.assertNotIn(SECRET, json.dumps(report))

    @unittest.skipUnless(os.name == "posix", "requires native POSIX symlinks")
    def test_symlink_directory_components_and_output_leaf_are_rejected(self) -> None:
        link = self.temp / "alias"
        link.symlink_to(self.temp, target_is_directory=True)
        for campaign_dir, output_dir in (
            (link / "campaign", self.output), (self.campaign, link / "output"),
        ):
            with self.subTest(campaign=campaign_dir):
                with self.assertRaisesRegex(DiagnosticsError, "unsafe-directory"):
                    collect_diagnostics(ROOT, campaign_dir, output_dir, source_sha="1" * 40,
                                        run_id="123", run_attempt="1", phases=phases())
        self.output.symlink_to(self.campaign, target_is_directory=True)
        with self.assertRaisesRegex(DiagnosticsError, "unsafe-directory"):
            self.collect()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires native FIFO support")
    def test_fifo_is_rejected_without_open_or_hang(self) -> None:
        os.mkfifo(self.campaign / "evidence.json")
        with patch("agent_dev_kit.native_campaign_diagnostics.read_bytes", side_effect=AssertionError("must not read")):
            report = self.collect()
        self.assertEqual(report["files"]["evidence.json"]["reason_code"], "unsafe-input-file")

    def test_existing_output_directory_is_not_reused_or_uploaded(self) -> None:
        self.output.mkdir()
        private = self.output / "private.txt"
        private.write_text(SECRET, encoding="utf-8")
        with self.assertRaisesRegex(DiagnosticsError, "output-directory-must-be-new"):
            self.collect()
        self.assertEqual(private.read_text(encoding="utf-8"), SECRET)
        self.assertFalse((self.output / "diagnostics.json").exists())

    def test_success_and_untrusted_prerequisites_are_refused(self) -> None:
        examples = [dict.fromkeys(PHASES, "success"), phases("source"), phases("python"), phases("runtime")]
        for outcomes in examples:
            with self.subTest(phases=outcomes):
                with self.assertRaises(DiagnosticsError):
                    collect_diagnostics(ROOT, self.campaign, self.output, source_sha="1" * 40,
                                        run_id="123", run_attempt="1", phases=outcomes)
        self.assertFalse(self.output.exists())

    def test_unknown_phase_or_outcome_is_rejected(self) -> None:
        for value in ({**phases(), "secret": SECRET}, {**phases(), "run": SECRET}):
            with self.subTest(value=value):
                with self.assertRaises(DiagnosticsError):
                    collect_diagnostics(ROOT, self.campaign, self.output, source_sha="1" * 40,
                                        run_id="123", run_attempt="1", phases=value)

    def test_cli_failure_is_nonzero_and_does_not_echo_sensitive_input(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([
                "--root", str(ROOT), "--campaign-dir", str(self.campaign),
                "--output-dir", str(self.output), "--source-sha", SECRET,
                "--run-id", "123", "--run-attempt", "1", "--phases-json", json.dumps(phases()),
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())["status"], "not-collected")
        self.assertNotIn(SECRET, out.getvalue())
        self.assertFalse(self.output.exists())


class NativeCampaignDiagnosticsWorkflowTest(unittest.TestCase):
    def test_failure_collection_preserves_success_only_qualification_steps(self) -> None:
        workflow = (ROOT / ".github/workflows/native-claude-conformance.yml").read_text(encoding="utf-8")
        blocks = workflow.split("\n      - name: ")[1:]
        by_name = {block.splitlines()[0]: block for block in blocks}
        collector = by_name["Collect bounded failed-campaign diagnostics"]
        uploader = by_name["Upload failed-campaign diagnostics only"]
        scoped_steps = {
            step["name"]: step for step in yaml.safe_load(workflow)["jobs"]["campaign"]["steps"]
        }
        for name in ("Collect bounded failed-campaign diagnostics", "Upload failed-campaign diagnostics only"):
            self.assertEqual(scoped_steps[name]["timeout-minutes"], 2)
        self.assertIn("failure() && steps.source_identity.outcome == 'success'", collector)
        self.assertIn("steps.python.outcome == 'success'", collector)
        self.assertIn("steps.runtime.outcome == 'success'", collector)
        self.assertIn("failure() && steps.failure_diagnostics.outcome == 'success'", uploader)
        self.assertIn("timeout-minutes: 2", collector)
        self.assertIn("timeout-minutes: 2", uploader)
        self.assertIn("path: ${{ runner.temp }}/g21-native-diagnostics/diagnostics.json", uploader)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("always()", workflow)
        self.assertNotIn("ANTHROPIC_API_KEY", collector)
        self.assertNotIn("toJSON(steps)", collector)
        self.assertEqual(set(re.findall(r'"([a-z]+)":"\$\{\{ steps\.', collector)), set(PHASES))
        for name in (
            "Authenticate Claude Code noninteractively", "Prepare semantic-v2 native campaign",
            "Run semantic-v2 native campaign", "Finalize unsigned native receipt candidate",
            "Sign exact canonical native receipt with GitHub OIDC",
            "Build managed trust registry candidate and verify production loader",
            "Package retained candidate evidence", "Upload candidate native conformance package",
        ):
            self.assertNotRegex(by_name[name], r"(?m)^        if:")
        candidate = by_name["Upload candidate native conformance package"]
        self.assertIn("path: ${{ runner.temp }}/g21-native\n", candidate)
        self.assertLess(workflow.index("Upload candidate native conformance package"),
                        workflow.index("Collect bounded failed-campaign diagnostics"))


if __name__ == "__main__":
    unittest.main()
