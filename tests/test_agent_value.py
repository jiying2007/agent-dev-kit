from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_dev_kit.agent_value import emit_measurements, load_contract, validate_contract, validate_receipt
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests" / "agent_value_contracts.json")
AS_OF = datetime(2026, 8, 29, 18, 0, tzinfo=timezone.utc)
AGGREGATION_WINDOW = {
    "from": datetime(2026, 8, 29, 11, 0, tzinfo=timezone.utc),
    "through": datetime(2026, 8, 29, 13, 0, tzinfo=timezone.utc),
}


def opaque(marker: str) -> str:
    return "ref:" + marker * 64


def bind_receipt(value: dict) -> dict:
    attestation = value.get("authority_attestation")
    if isinstance(attestation, dict):
        payload = dict(value)
        payload.pop("receipt_id", None)
        payload.pop("authority_attestation", None)
        value["authority_attestation"] = {
            "authority_id": attestation["authority_id"],
            "body_sha256": sha256_bytes(canonical_json_bytes(payload)),
            "manifest_ref": value["manifest_ref"],
            "asset_bundle_sha256": value["asset_bundle_sha256"],
            "evidence_layer": value["evidence_layer"],
            "runtime_target": value["runtime_target"],
            "source_trace_ref": value["source_trace_ref"],
        }
    return bind_receipt_id(value)


def bind_receipt_id(value: dict) -> dict:
    body = dict(value)
    body.pop("receipt_id", None)
    value["receipt_id"] = "ref:" + sha256_bytes(canonical_json_bytes(body))
    return value


def receipt(asset_id: str, asset_kind: str, marker: str = "1", evidence_layer: str = "test") -> dict:
    return bind_receipt({
        "schema_version": "adk-asset-invocation-receipt/v1",
        "invocation_ref": opaque("2" if marker != "2" else "3"),
        "source_trace_ref": opaque("4" if marker != "4" else "5"),
        "manifest_ref": "ref:" + MANIFEST.digest,
        "asset_bundle_sha256": ("5" if marker != "5" else "6") * 64,
        "runtime_target": "test-harness" if evidence_layer == "test" else "test-runtime",
        "evidence_layer": evidence_layer,
        "observed_at": "2026-08-29T12:00:00Z",
        "measurement_status": "measured",
        "asset_id": asset_id,
        "asset_kind": asset_kind,
        "routing": {"routed": True, "abstained": False, "wrong_route": False},
        "outcome": "succeeded",
        "human_interventions": 0,
        "first_pass": True,
        "retirement_signal": "insufficient-evidence",
        "evidence_refs": [opaque("6" if marker != "6" else "7")],
        "privacy_status": "no-sensitive-content",
        "raw_content_stored": False,
    })


def managed_contract(production: bool = False) -> dict:
    value = copy.deepcopy(CONTRACT)
    value["evidence_authority_policy"] = {
        "managed": True,
        "status": "enabled",
        "backend": "test-only",
        "authorities": [
            {
                "authority_id": "test-authority",
                "backend": "test-only",
                "allowed_layers": ["runtime", "field"],
                "runtime_targets": ["test-runtime"],
                "production": production,
            }
        ],
    }
    return value


def attest(value: dict, authority_id: str = "test-authority") -> dict:
    value["authority_attestation"] = {"authority_id": authority_id}
    return bind_receipt(value)


def test_verifier(receipt_value: dict, authority: dict) -> bool:
    return authority["backend"] == "test-only" and receipt_value["runtime_target"] == "test-runtime"


def emit(receipts: list, contract: dict = CONTRACT, evidence_verifier=None) -> dict:
    return emit_measurements(
        receipts,
        MANIFEST,
        contract,
        evidence_verifier=evidence_verifier,
        aggregation_window=AGGREGATION_WINDOW,
        as_of=AS_OF,
    )


class AgentValueContractTest(unittest.TestCase):
    def test_contract_covers_live_manifest_without_parallel_identity_catalog(self) -> None:
        report = validate_contract(CONTRACT, MANIFEST)
        self.assertEqual("pass", report["status"])
        self.assertEqual(13, report["agent_count"])
        self.assertEqual(len(MANIFEST.data["skills"]) + len(MANIFEST.data["optional_skills"]), report["skill_count"])
        self.assertEqual(len(MANIFEST.data["profiles"]), report["profile_count"])
        self.assertEqual("not-measured", report["emitter_status"])
        self.assertFalse(report["runtime_enabled"])
        self.assertEqual("none-claimed", report["usage_evidence"])
        self.assertEqual("ref:<sha256>", CONTRACT["receipt_contract"]["evidence_ref_format"])
        self.assertEqual("explicit-validated-receipts-only", CONTRACT["emitter"]["input_mode"])
        self.assertEqual("explicit-not-measured-never-zero", CONTRACT["emitter"]["missing_metric_policy"])
        self.assertEqual("available", CONTRACT["emitter"]["api_status"])
        self.assertEqual("emit_measurements", CONTRACT["emitter"]["api"])
        self.assertFalse(CONTRACT["emitter"]["automatic_runtime_integration"])
        self.assertNotIn("skills", CONTRACT)
        self.assertNotIn("profiles", CONTRACT)
        for item in CONTRACT["agent_contracts"]:
            self.assertNotIn("description", item)
            self.assertNotIn("path", item)
            self.assertNotIn("default_skills", item)

    def test_permission_and_handoff_cannot_exceed_manifest(self) -> None:
        elevated = copy.deepcopy(CONTRACT)
        analyst = next(item for item in elevated["agent_contracts"] if item["agent_id"] == "requirements-analyst")
        analyst["permission_envelope"]["permission_profile"] = "code-write"
        with self.assertRaises(ManifestError):
            validate_contract(elevated, MANIFEST)

        effect_escape = copy.deepcopy(CONTRACT)
        analyst = next(
            item for item in effect_escape["agent_contracts"] if item["agent_id"] == "requirements-analyst"
        )
        analyst["permission_envelope"]["allowed_effects"].append("workspace-write")
        with self.assertRaises(ManifestError):
            validate_contract(effect_escape, MANIFEST)

        tool_escape = copy.deepcopy(CONTRACT)
        analyst = next(item for item in tool_escape["agent_contracts"] if item["agent_id"] == "requirements-analyst")
        analyst["permission_envelope"]["tool_capabilities"].append("workspace-edit")
        with self.assertRaises(ManifestError):
            validate_contract(tool_escape, MANIFEST)

        dangling = copy.deepcopy(CONTRACT)
        analyst = next(item for item in dangling["agent_contracts"] if item["agent_id"] == "requirements-analyst")
        analyst["handoff"]["allowed_targets"][0] = "unknown-agent"
        with self.assertRaises(ManifestError):
            validate_contract(dangling, MANIFEST)

    def test_agent_coverage_eval_and_quality_kpis_fail_closed(self) -> None:
        missing = copy.deepcopy(CONTRACT)
        missing["agent_contracts"].pop()
        with self.assertRaises(ManifestError):
            validate_contract(missing, MANIFEST)

        duplicate = copy.deepcopy(CONTRACT)
        duplicate["agent_contracts"].append(copy.deepcopy(duplicate["agent_contracts"][0]))
        with self.assertRaises(ManifestError):
            validate_contract(duplicate, MANIFEST)

        weak_eval = copy.deepcopy(CONTRACT)
        weak_eval["agent_contracts"][0]["eval_suite"]["required_case_types"].pop()
        with self.assertRaises(ManifestError):
            validate_contract(weak_eval, MANIFEST)

        volume_kpi = copy.deepcopy(CONTRACT)
        volume_kpi["quality_kpi_policy"]["quality_kpis"].append("report-count")
        with self.assertRaises(ManifestError):
            validate_contract(volume_kpi, MANIFEST)

        token_kpi = copy.deepcopy(CONTRACT)
        token_kpi["quality_kpi_policy"]["quality_kpis"].append("tokens-per-task")
        with self.assertRaises(ManifestError):
            validate_contract(token_kpi, MANIFEST)

    def test_emitter_cannot_claim_unmeasured_usage(self) -> None:
        measured = copy.deepcopy(CONTRACT)
        measured["emitter"]["status"] = "measured"
        measured["emitter"]["runtime_enabled"] = True
        measured["emitter"]["usage_evidence"] = "claimed"
        with self.assertRaises(ManifestError):
            validate_contract(measured, MANIFEST)

    def test_receipt_resolves_agent_skill_and_profile_from_manifest(self) -> None:
        cases = [
            ("requirements-analyst", "agent"),
            ("adk-runtime-router", "skill"),
            ("core", "profile"),
        ]
        for asset_id, asset_kind in cases:
            with self.subTest(asset_kind=asset_kind):
                report = validate_receipt(receipt(asset_id, asset_kind), MANIFEST, CONTRACT)
                self.assertEqual("pass", report["status"])
                self.assertEqual(asset_id, report["asset_id"])
                self.assertFalse(report["raw_content_stored"])
                self.assertEqual("signal-only-owner-decision-required", report["retirement_authority"])

        abstained = receipt("core", "profile")
        abstained["routing"] = {"routed": False, "abstained": True, "wrong_route": False}
        abstained["outcome"] = "abstained"
        abstained.pop("first_pass")
        abstained["abstain_correct"] = True
        bind_receipt(abstained)
        self.assertEqual("pass", validate_receipt(abstained, MANIFEST, CONTRACT)["status"])

    def test_receipt_metrics_identity_and_routing_fail_closed(self) -> None:
        unknown = receipt("missing-skill", "skill")
        with self.assertRaises(ManifestError):
            validate_receipt(unknown, MANIFEST, CONTRACT)

        wrong_type = receipt("core", "profile")
        wrong_type["human_interventions"] = True
        with self.assertRaises(ManifestError):
            validate_receipt(wrong_type, MANIFEST, CONTRACT)

        contradictory = receipt("core", "profile")
        contradictory["routing"]["abstained"] = True
        with self.assertRaises(ManifestError):
            validate_receipt(contradictory, MANIFEST, CONTRACT)

        invalid_wrong_route = receipt("core", "profile")
        invalid_wrong_route["routing"] = {"routed": False, "abstained": True, "wrong_route": True}
        invalid_wrong_route["outcome"] = "abstained"
        invalid_wrong_route.pop("first_pass")
        invalid_wrong_route["abstain_correct"] = True
        bind_receipt(invalid_wrong_route)
        with self.assertRaises(ManifestError):
            validate_receipt(invalid_wrong_route, MANIFEST, CONTRACT)

        outcome_mismatch = receipt("core", "profile")
        outcome_mismatch["outcome"] = "abstained"
        with self.assertRaises(ManifestError):
            validate_receipt(outcome_mismatch, MANIFEST, CONTRACT)

    def test_receipt_sensitive_and_raw_content_fail_closed(self) -> None:
        raw = receipt("core", "profile")
        raw["raw_content_stored"] = True
        with self.assertRaises(ManifestError):
            validate_receipt(raw, MANIFEST, CONTRACT)

        sensitive_field = receipt("core", "profile")
        sensitive_field["raw_prompt"] = "do not persist"
        with self.assertRaises(ManifestError):
            validate_receipt(sensitive_field, MANIFEST, CONTRACT)

        for secret in (
            "ghp_abcdefghijklmnopqrstuv",
            "github_pat_abcdefghijklmnopqrstuv",
            "sk-abcdefghijklmnop",
            "Bearer abcdefghijklmnop",
            "AKIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
            "raw prompt",
            "tool payload",
        ):
            secret_like = receipt("core", "profile")
            secret_like["evidence_refs"] = [secret]
            with self.subTest(secret=secret), self.assertRaises(ManifestError):
                validate_receipt(secret_like, MANIFEST, CONTRACT)

        free_ref = receipt("core", "profile")
        free_ref["evidence_refs"] = ["tests/raw-log.txt"]
        with self.assertRaises(ManifestError):
            validate_receipt(free_ref, MANIFEST, CONTRACT)

        source_path = receipt("core", "profile")
        source_path["source_trace_ref"] = "reports/raw-trace.json"
        with self.assertRaises(ManifestError):
            validate_receipt(source_path, MANIFEST, CONTRACT)

    def test_empty_emitter_is_not_measured_and_never_fills_zero(self) -> None:
        report = emit_measurements([], MANIFEST, CONTRACT)
        self.assertEqual("not-measured", report["measurement_status"])
        self.assertEqual("no-valid-receipts", report["reason"])
        self.assertEqual([], report["asset_measurements"])
        self.assertNotIn("source_receipt_count", report)
        self.assertNotIn("metrics", report)

    def test_emitter_measures_receipts_without_volume_or_token_value_proxies(self) -> None:
        succeeded = receipt("requirements-analyst", "agent", "8")
        succeeded["time_to_trustworthy_change_ms"] = 1200
        bind_receipt(succeeded)
        failed = receipt("requirements-analyst", "agent", "9")
        failed["invocation_ref"] = opaque("a")
        failed["outcome"] = "failed"
        failed["first_pass"] = False
        failed["routing"]["wrong_route"] = True
        failed["human_interventions"] = 2
        bind_receipt(failed)

        report = emit([succeeded, failed])
        self.assertEqual("measured", report["measurement_status"])
        self.assertEqual(2, report["source_receipt_count"])
        self.assertEqual(
            {"from": "2026-08-29T12:00:00Z", "through": "2026-08-29T12:00:00Z"},
            report["asset_measurements"][0]["observation_window"],
        )
        self.assertEqual("test-only", report["evidence_scope"])
        self.assertFalse(report["quality_evidence_eligible"])
        self.assertEqual("test-only-evidence", report["quality_ineligibility_reason"])
        self.assertTrue(report["owner_review_required"])
        self.assertEqual("none-evidence-only", report["lifecycle_authority"])
        self.assertNotIn("reason", report)
        self.assertNotIn("tokens", str(report).casefold())
        measurement = report["asset_measurements"][0]
        self.assertEqual("requirements-analyst", measurement["asset_id"])
        self.assertEqual("test", measurement["evidence_layer"])
        metrics = measurement["metrics"]
        self.assertEqual(0.5, metrics["task-success-rate"]["value"])
        self.assertEqual(0.5, metrics["first-pass-success-rate"]["value"])
        self.assertEqual(0.5, metrics["wrong-route-rate"]["value"])
        self.assertEqual(1.0, metrics["human-interventions-per-task"]["value"])
        self.assertEqual("not-measured", metrics["time-to-trustworthy-change"]["status"])
        self.assertEqual("incomplete-coverage", metrics["time-to-trustworthy-change"]["reason"])
        self.assertEqual(2, metrics["time-to-trustworthy-change"]["applicable_sample_size"])
        self.assertEqual(1, metrics["time-to-trustworthy-change"]["observed_sample_size"])
        self.assertEqual(0.5, metrics["time-to-trustworthy-change"]["coverage"])
        self.assertEqual("not-measured", metrics["abstain-precision"]["status"])
        self.assertEqual("no-applicable-receipts", metrics["abstain-precision"]["reason"])
        self.assertEqual("not-measured", metrics["escaped-defect-rate"]["status"])
        self.assertEqual("field-not-observed", metrics["escaped-defect-rate"]["reason"])
        self.assertNotIn("value", metrics["escaped-defect-rate"])
        for key in ("receipt_refs", "invocation_refs", "source_trace_refs", "evidence_refs"):
            self.assertTrue(all(value.startswith("ref:") for value in measurement[key]))

    def test_emitter_measures_agent_skill_and_profile_without_parallel_identity_data(self) -> None:
        report = emit(
            [
                receipt("requirements-analyst", "agent", "1"),
                receipt("adk-runtime-router", "skill", "2"),
                receipt("core", "profile", "3"),
            ]
        )
        self.assertEqual(
            {("agent", "requirements-analyst"), ("skill", "adk-runtime-router"), ("profile", "core")},
            {(item["asset_kind"], item["asset_id"]) for item in report["asset_measurements"]},
        )
        for item in report["asset_measurements"]:
            self.assertNotIn("description", item)
            self.assertNotIn("path", item)
            self.assertNotIn("token", str(item).casefold())

    def test_emitter_keeps_evidence_layers_separate_and_validates_abstention(self) -> None:
        test_receipt = receipt("core", "profile", "b", "test")
        runtime_receipt = receipt("core", "profile", "c", "runtime")
        runtime_receipt["invocation_ref"] = opaque("d")
        runtime_receipt["routing"] = {"routed": False, "abstained": True, "wrong_route": False}
        runtime_receipt["outcome"] = "abstained"
        runtime_receipt.pop("first_pass")
        runtime_receipt["abstain_correct"] = True
        attest(runtime_receipt)
        trusted_contract = managed_contract()
        report = emit(
            [test_receipt, runtime_receipt],
            trusted_contract,
            evidence_verifier=test_verifier,
        )
        self.assertEqual(["runtime", "test"], sorted(item["evidence_layer"] for item in report["asset_measurements"]))
        runtime = next(item for item in report["asset_measurements"] if item["evidence_layer"] == "runtime")
        self.assertEqual(1.0, runtime["metrics"]["abstain-precision"]["value"])
        self.assertEqual("no-applicable-receipts", runtime["metrics"]["wrong-route-rate"]["reason"])
        self.assertEqual("no-applicable-receipts", runtime["metrics"]["task-success-rate"]["reason"])
        self.assertEqual("mixed", report["evidence_scope"])
        self.assertFalse(report["quality_evidence_eligible"])
        self.assertEqual("mixed-evidence-scope", report["quality_ineligibility_reason"])

    def test_runtime_and_field_require_injected_trust_verifier(self) -> None:
        for layer in ("runtime", "field"):
            candidate = attest(receipt("core", "profile", "e", layer))
            with self.subTest(layer=layer), self.assertRaises(ManifestError):
                validate_receipt(candidate, MANIFEST, CONTRACT)
            with self.subTest(layer=layer, default_policy="lambda-true"), self.assertRaises(ManifestError):
                validate_receipt(candidate, MANIFEST, CONTRACT, evidence_verifier=lambda _item, _authority: True)
            trusted_contract = managed_contract()
            with self.subTest(layer=layer, verifier="reject"), self.assertRaises(ManifestError):
                validate_receipt(
                    candidate,
                    MANIFEST,
                    trusted_contract,
                    evidence_verifier=lambda _item, _authority: False,
                )
            report = validate_receipt(
                candidate,
                MANIFEST,
                trusted_contract,
                evidence_verifier=test_verifier,
            )
            self.assertEqual("managed-authority-verified", report["source_verification"])
            nonproduction_measurement = emit(
                [candidate],
                trusted_contract,
                evidence_verifier=test_verifier,
            )
            self.assertFalse(nonproduction_measurement["quality_evidence_eligible"])
            self.assertEqual(
                "non-production-authority",
                nonproduction_measurement["quality_ineligibility_reason"],
            )
            mutable_production_contract = managed_contract(production=True)
            with self.subTest(layer=layer, production="input-contract"), self.assertRaises(ManifestError):
                validate_contract(mutable_production_contract, MANIFEST)
            with self.subTest(layer=layer, production="lambda-true"), self.assertRaises(ManifestError):
                emit(
                    [candidate],
                    mutable_production_contract,
                    evidence_verifier=lambda _item, _authority: True,
                )
            self.assertTrue(nonproduction_measurement["owner_review_required"])
            self.assertEqual("none-evidence-only", nonproduction_measurement["lifecycle_authority"])

        test_report = validate_receipt(receipt("core", "profile"), MANIFEST, CONTRACT)
        self.assertEqual("structural-only", test_report["source_verification"])

    def test_future_receipt_and_body_tamper_fail_closed(self) -> None:
        future = receipt("core", "profile")
        future["observed_at"] = "2999-01-01T00:00:00Z"
        bind_receipt(future)
        with self.assertRaises(ManifestError):
            validate_receipt(future, MANIFEST, CONTRACT)

        stale = receipt("core", "profile")
        stale["observed_at"] = "2020-01-01T00:00:00Z"
        bind_receipt(stale)
        with self.assertRaises(ManifestError):
            validate_receipt(stale, MANIFEST, CONTRACT)

        wrong_manifest = receipt("core", "profile")
        wrong_manifest["manifest_ref"] = opaque("f")
        bind_receipt(wrong_manifest)
        with self.assertRaises(ManifestError):
            validate_receipt(wrong_manifest, MANIFEST, CONTRACT)

        outside_window = receipt("core", "profile")
        outside_window["observed_at"] = "2026-08-29T10:00:00Z"
        bind_receipt(outside_window)
        with self.assertRaises(ManifestError):
            emit([outside_window])

        tampered = receipt("core", "profile")
        tampered["human_interventions"] = 9
        with self.assertRaises(ManifestError):
            validate_receipt(tampered, MANIFEST, CONTRACT)

    def test_abstain_does_not_reduce_task_or_first_pass_success(self) -> None:
        success = receipt("requirements-analyst", "agent", "1")
        abstain = receipt("requirements-analyst", "agent", "2")
        abstain["routing"] = {"routed": False, "abstained": True, "wrong_route": False}
        abstain["outcome"] = "abstained"
        abstain.pop("first_pass")
        abstain["abstain_correct"] = True
        bind_receipt(abstain)
        metrics = emit([success, abstain])["asset_measurements"][0]["metrics"]
        self.assertEqual(1.0, metrics["task-success-rate"]["value"])
        self.assertEqual(1, metrics["task-success-rate"]["sample_size"])
        self.assertEqual(1.0, metrics["first-pass-success-rate"]["value"])
        self.assertEqual(1, metrics["first-pass-success-rate"]["sample_size"])
        self.assertEqual(1.0, metrics["abstain-precision"]["value"])

    def test_field_only_metrics_cannot_be_claimed_by_test_or_runtime(self) -> None:
        test_claim = receipt("core", "profile")
        test_claim["escaped_defect"] = False
        bind_receipt(test_claim)
        with self.assertRaises(ManifestError):
            validate_receipt(test_claim, MANIFEST, CONTRACT)

        runtime_claim = receipt("core", "profile", "a", "runtime")
        runtime_claim["escaped_defect"] = False
        attest(runtime_claim)
        with self.assertRaises(ManifestError):
            validate_receipt(
                runtime_claim,
                MANIFEST,
                managed_contract(),
                evidence_verifier=test_verifier,
            )

        field_claim = receipt("core", "profile", "b", "field")
        field_claim["escaped_defect"] = False
        field_claim["rollback"] = True
        attest(field_claim)
        metrics = emit(
            [field_claim],
            managed_contract(),
            evidence_verifier=test_verifier,
        )["asset_measurements"][0]["metrics"]
        self.assertEqual(0.0, metrics["escaped-defect-rate"]["value"])
        self.assertEqual(1.0, metrics["rollback-rate"]["value"])

        partial_field = receipt("core", "profile", "c", "field")
        partial_field["invocation_ref"] = opaque("d")
        attest(partial_field)
        partial_metrics = emit(
            [field_claim, partial_field],
            managed_contract(),
            evidence_verifier=test_verifier,
        )["asset_measurements"][0]["metrics"]
        for metric_name in ("escaped-defect-rate", "rollback-rate"):
            self.assertEqual("not-measured", partial_metrics[metric_name]["status"])
            self.assertEqual("incomplete-coverage", partial_metrics[metric_name]["reason"])
            self.assertEqual(2, partial_metrics[metric_name]["applicable_sample_size"])
            self.assertEqual(1, partial_metrics[metric_name]["observed_sample_size"])
            self.assertNotIn("value", partial_metrics[metric_name])

    def test_partial_first_pass_coverage_is_not_measured(self) -> None:
        observed = receipt("core", "profile", "1")
        missing = receipt("core", "profile", "2")
        missing.pop("first_pass")
        bind_receipt(missing)
        metric = emit([observed, missing])["asset_measurements"][0]["metrics"]["first-pass-success-rate"]
        self.assertEqual("not-measured", metric["status"])
        self.assertEqual("incomplete-coverage", metric["reason"])
        self.assertEqual(0.5, metric["coverage"])

    def test_authority_attestation_binding_fails_before_external_verifier(self) -> None:
        candidate = attest(receipt("core", "profile", "a", "runtime"))
        candidate["authority_attestation"]["manifest_ref"] = opaque("f")
        bind_receipt_id(candidate)
        with self.assertRaises(ManifestError):
            validate_receipt(
                candidate,
                MANIFEST,
                managed_contract(),
                evidence_verifier=lambda _item, _authority: True,
            )

    def test_emitter_truthfulness_and_state_semantics_fail_closed(self) -> None:
        duplicate = receipt("core", "profile", "d")
        with self.assertRaises(ManifestError):
            emit([duplicate, copy.deepcopy(duplicate)])

        duplicate_observation = receipt("core", "profile", "d")
        duplicate_observation_id = copy.deepcopy(duplicate_observation)
        duplicate_observation_id["evidence_refs"] = [opaque("e")]
        bind_receipt(duplicate_observation_id)
        with self.assertRaises(ManifestError):
            emit([duplicate_observation, duplicate_observation_id])

        relabeled_layer = copy.deepcopy(duplicate_observation)
        relabeled_layer["evidence_layer"] = "runtime"
        relabeled_layer["runtime_target"] = "test-runtime"
        attest(relabeled_layer)
        with self.assertRaises(ManifestError):
            emit(
                [duplicate_observation, relabeled_layer],
                managed_contract(),
                evidence_verifier=test_verifier,
            )

        claimed_without_measurement = receipt("core", "profile")
        claimed_without_measurement["measurement_status"] = "not-measured"
        with self.assertRaises(ManifestError):
            emit([claimed_without_measurement])

        impossible_first_pass = receipt("core", "profile")
        impossible_first_pass["outcome"] = "failed"
        with self.assertRaises(ManifestError):
            validate_receipt(impossible_first_pass, MANIFEST, CONTRACT)

        non_abstain_with_precision_label = receipt("core", "profile")
        non_abstain_with_precision_label["abstain_correct"] = True
        with self.assertRaises(ManifestError):
            validate_receipt(non_abstain_with_precision_label, MANIFEST, CONTRACT)


if __name__ == "__main__":
    unittest.main()
