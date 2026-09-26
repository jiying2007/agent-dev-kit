from __future__ import annotations

import copy
import hashlib
import json
import shutil
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_dev_kit.agent_value import emit_measurements
from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.agent_value_receipts import (
    ManagedInvocationObservation,
    prepare_managed_receipt,
    validate_receipt,
)
from agent_dev_kit.agent_value_trust import (
    ManagedAgentValueEvidenceVerifier,
    build_managed_agent_value_evidence_verifier,
    build_portable_managed_agent_value_evidence_verifier,
    load_agent_value_trust_registry,
)
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from agent_dev_kit.privacy_ref import opaque_ref_for_sha256

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
CONTRACT = load_contract(ROOT / "manifests" / "agent_value_contracts.json")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_cosign(directory: Path, exit_code: int = 0) -> Path:
    path = directory / "cosign"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib,sys\n"
        "a=sys.argv[1:]\n"
        "blob=sys.stdin.buffer.read()\n"
        "ok=(len(a)==8 and a[0]=='verify-blob' and a[1]=='--bundle' "
        "and a[3]=='--certificate-identity' and a[5]=='--certificate-oidc-issuer' "
        "and pathlib.Path(a[2]).is_file() and a[7]=='/dev/stdin' and len(blob)>0)\n"
        f"sys.exit({exit_code} if ok else 97)\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path.resolve()


def enabled_contract() -> dict:
    value = copy.deepcopy(CONTRACT)
    value["evidence_authority_policy"] = {
        "managed": True,
        "status": "enabled",
        "backend": "ci-provenance-verifier",
        "authorities": [
            {
                "authority_id": "agent-value-ci",
                "backend": "ci-provenance-verifier",
                "allowed_layers": ["runtime"],
                "runtime_targets": ["claude-code"],
                "production": False,
            }
        ],
    }
    return value


def runtime_receipt(observed_at: datetime) -> dict:
    agent_id = str(MANIFEST.data["agents"][0]["name"])
    return prepare_managed_receipt(
        ManagedInvocationObservation(
            invocation_ref=opaque_ref_for_sha256("1" * 64),
            source_trace_ref=opaque_ref_for_sha256("2" * 64),
            asset_bundle_sha256="a" * 64,
            runtime_target="claude-code",
            evidence_layer="runtime",
            observed_at=observed_at,
            asset_id=agent_id,
            asset_kind="agent",
            routed=True,
            abstained=False,
            wrong_route=False,
            outcome="succeeded",
            human_interventions=0,
            retirement_signal="retain",
            evidence_refs=(opaque_ref_for_sha256("3" * 64),),
            privacy_status="sanitized",
            first_pass=True,
            time_to_trustworthy_change_ms=250,
        ),
        MANIFEST,
        enabled_contract(),
        "agent-value-ci",
    )


def registry_for(
    receipt: dict,
    bundle: Path,
    binary: Path,
    *,
    bundle_root: Path = ROOT,
) -> dict:
    return {
        "schema": "adk-agent-value-trust-registry/v1",
        "status": "active",
        "authority_model": "owner-reviewed-managed-registry",
        "authorities": {
            "agent-value-ci": {
                "enabled": True,
                "policy_backend": "ci-provenance-verifier",
                "verifier": "sigstore-cosign-blob",
                "allowed_layers": ["runtime"],
                "runtime_targets": ["claude-code"],
                "certificate_identity": "https://github.com/example/repo/.github/workflows/value.yml@refs/heads/main",
                "certificate_oidc_issuer": "https://token.actions.githubusercontent.com",
                "cosign_binary": str(binary),
                "cosign_binary_sha256": file_sha256(binary),
                "receipts": {
                    receipt["receipt_id"]: {
                        "receipt_canonical_sha256": hashlib.sha256(
                            canonical_json_bytes(receipt)
                        ).hexdigest(),
                        "bundle_path": bundle.relative_to(bundle_root).as_posix(),
                        "bundle_sha256": file_sha256(bundle),
                    }
                },
            }
        },
    }


class AgentValueTrustTest(unittest.TestCase):
    def setUp(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        fixtures.mkdir(exist_ok=True)
        self.repo_temp = Path(
            tempfile.mkdtemp(prefix="agent-value-trust-", dir=fixtures)
        )
        self.external_temp = Path(tempfile.mkdtemp(prefix="agent-value-cosign-"))
        self.addCleanup(lambda: shutil.rmtree(self.repo_temp, ignore_errors=True))
        self.addCleanup(lambda: shutil.rmtree(self.external_temp, ignore_errors=True))

    def test_repository_registry_is_empty_and_canonical_contract_is_disabled(self) -> None:
        registry = load_agent_value_trust_registry(ROOT)
        self.assertEqual(registry["schema"], "adk-agent-value-trust-registry/v1")
        self.assertEqual(registry["authorities"], {})
        with self.assertRaisesRegex(ManifestError, "policy_disabled"):
            build_managed_agent_value_evidence_verifier(MANIFEST, CONTRACT)

    def test_prepared_managed_receipt_is_deterministic_but_not_verified(self) -> None:
        contract = enabled_contract()
        observed = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
        first = runtime_receipt(observed)
        second = runtime_receipt(observed)
        self.assertEqual(first, second)
        self.assertEqual(first["evidence_layer"], "runtime")
        self.assertEqual(
            first["authority_attestation"]["authority_id"], "agent-value-ci"
        )
        with self.assertRaisesRegex(ManifestError, "injected evidence verifier"):
            validate_receipt(first, MANIFEST, contract, as_of=observed + timedelta(minutes=1))

        bad = ManagedInvocationObservation(
            invocation_ref=opaque_ref_for_sha256("1" * 64),
            source_trace_ref=opaque_ref_for_sha256("2" * 64),
            asset_bundle_sha256="a" * 64,
            runtime_target="opencode",
            evidence_layer="runtime",
            observed_at=observed,
            asset_id=str(MANIFEST.data["agents"][0]["name"]),
            asset_kind="agent",
            routed=True,
            abstained=False,
            wrong_route=False,
            outcome="succeeded",
            human_interventions=0,
            retirement_signal="retain",
            evidence_refs=(opaque_ref_for_sha256("3" * 64),),
            privacy_status="sanitized",
        )
        with self.assertRaisesRegex(ManifestError, "outside authority scope"):
            prepare_managed_receipt(bad, MANIFEST, contract, "agent-value-ci")

    def test_managed_runtime_receipt_flows_through_canonical_measurement(self) -> None:
        contract = enabled_contract()
        observed = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
        as_of = observed + timedelta(minutes=1)
        receipt = runtime_receipt(observed)
        bundle = self.repo_temp / "receipt.sigstore.json"
        bundle.write_text('{"fixture":"sigstore"}\n', encoding="utf-8")
        binary = fake_cosign(self.external_temp)
        verifier = ManagedAgentValueEvidenceVerifier(
            MANIFEST, contract, registry_for(receipt, bundle, binary)
        )

        validation = validate_receipt(
            receipt,
            MANIFEST,
            contract,
            evidence_verifier=verifier,
            as_of=as_of,
        )
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(validation["source_verification"], "managed-authority-verified")
        self.assertFalse(validation["authority_production"])

        measurement = emit_measurements(
            [receipt],
            MANIFEST,
            contract,
            evidence_verifier=verifier,
            aggregation_window={
                "from": observed - timedelta(seconds=1),
                "through": observed + timedelta(seconds=1),
            },
            as_of=as_of,
        )
        self.assertEqual(measurement["measurement_status"], "measured")
        self.assertEqual(measurement["evidence_scope"], "runtime-verified")
        self.assertFalse(measurement["quality_evidence_eligible"])
        self.assertEqual(
            measurement["quality_ineligibility_reason"], "non-production-authority"
        )
        self.assertTrue(measurement["owner_review_required"])
        self.assertEqual(measurement["lifecycle_authority"], "none-evidence-only")
        asset = measurement["asset_measurements"][0]
        self.assertEqual(asset["source_verification"], "managed-authority-verified")
        self.assertEqual(asset["retirement_signals"], ["retain"])
        self.assertFalse(asset["production_authority"])
        self.assertEqual(asset["metrics"]["task-success-rate"]["value"], 1.0)
        self.assertEqual(asset["metrics"]["wrong-route-rate"]["value"], 0.0)
        self.assertEqual(asset["metrics"]["first-pass-success-rate"]["value"], 1.0)
        self.assertEqual(asset["metrics"]["human-interventions-per-task"]["value"], 0.0)

    def test_portable_bundle_root_recomputes_managed_measurement_without_source_mutation(self) -> None:
        contract = enabled_contract()
        observed = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
        as_of = observed + timedelta(minutes=1)
        receipt = runtime_receipt(observed)

        bundle_root = self.external_temp / "portable-evidence"
        bundle_root.mkdir()
        bundle = bundle_root / "receipt.sigstore.json"
        bundle.write_text('{"fixture":"portable-sigstore"}\n', encoding="utf-8")
        binary = fake_cosign(self.external_temp)
        registry = registry_for(
            receipt,
            bundle,
            binary,
            bundle_root=bundle_root,
        )

        verifier = build_portable_managed_agent_value_evidence_verifier(
            MANIFEST,
            contract,
            registry,
            bundle_root=bundle_root,
        )
        measurement = emit_measurements(
            [receipt],
            MANIFEST,
            contract,
            evidence_verifier=verifier,
            aggregation_window={
                "from": observed - timedelta(seconds=1),
                "through": observed + timedelta(seconds=1),
            },
            as_of=as_of,
        )
        self.assertEqual(measurement["measurement_status"], "measured")
        self.assertEqual(measurement["evidence_scope"], "runtime-verified")
        self.assertEqual(
            measurement["asset_measurements"][0]["source_verification"],
            "managed-authority-verified",
        )
        self.assertFalse((ROOT / "receipt.sigstore.json").exists())

        missing_root = self.external_temp / "missing"
        with self.assertRaisesRegex(ManifestError, "bundle_root_missing_or_unsafe"):
            build_portable_managed_agent_value_evidence_verifier(
                MANIFEST,
                contract,
                registry,
                bundle_root=missing_root,
            )

    def test_scope_digest_binary_bundle_and_signature_fail_closed(self) -> None:
        contract = enabled_contract()
        observed = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
        receipt = runtime_receipt(observed)
        bundle = self.repo_temp / "receipt.sigstore.json"
        bundle.write_text("{}\n", encoding="utf-8")
        binary = fake_cosign(self.external_temp)
        base = registry_for(receipt, bundle, binary)

        wrong_target = copy.deepcopy(base)
        wrong_target["authorities"]["agent-value-ci"]["runtime_targets"] = ["opencode"]
        verifier = ManagedAgentValueEvidenceVerifier(MANIFEST, contract, wrong_target)
        with self.assertRaisesRegex(ManifestError, "target_scope_mismatch"):
            verifier(receipt, contract["evidence_authority_policy"]["authorities"][0])

        wrong_receipt = copy.deepcopy(base)
        record = wrong_receipt["authorities"]["agent-value-ci"]["receipts"][receipt["receipt_id"]]
        record["receipt_canonical_sha256"] = "0" * 64
        verifier = ManagedAgentValueEvidenceVerifier(MANIFEST, contract, wrong_receipt)
        with self.assertRaisesRegex(ManifestError, "receipt_digest_mismatch"):
            verifier(receipt, contract["evidence_authority_policy"]["authorities"][0])

        wrong_bundle = copy.deepcopy(base)
        wrong_bundle["authorities"]["agent-value-ci"]["receipts"][receipt["receipt_id"]][
            "bundle_sha256"
        ] = "0" * 64
        verifier = ManagedAgentValueEvidenceVerifier(MANIFEST, contract, wrong_bundle)
        with self.assertRaisesRegex(ManifestError, "bundle_digest_mismatch"):
            verifier(receipt, contract["evidence_authority_policy"]["authorities"][0])

        wrong_binary = copy.deepcopy(base)
        wrong_binary["authorities"]["agent-value-ci"]["cosign_binary_sha256"] = "0" * 64
        verifier = ManagedAgentValueEvidenceVerifier(MANIFEST, contract, wrong_binary)
        with self.assertRaisesRegex(ManifestError, "cosign_digest_mismatch"):
            verifier(receipt, contract["evidence_authority_policy"]["authorities"][0])

        failed_binary = fake_cosign(self.external_temp, exit_code=1)
        failed = registry_for(receipt, bundle, failed_binary)
        verifier = ManagedAgentValueEvidenceVerifier(MANIFEST, contract, failed)
        self.assertFalse(
            verifier(receipt, contract["evidence_authority_policy"]["authorities"][0])
        )


if __name__ == "__main__":
    unittest.main()
