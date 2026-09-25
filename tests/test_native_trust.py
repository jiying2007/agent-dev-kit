from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes
from agent_dev_kit.native_trust import build_managed_native_trust_verifier, load_native_trust_registry
from agent_dev_kit.target_contracts import (
    _authority_digest,
    _native_contract_digest,
    load_target_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_cosign(root: Path, exit_code: int = 0) -> Path:
    path = root / "cosign-fixture"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib,sys\n"
        "args=sys.argv[1:]\n"
        "ok=(len(args)==8 and args[0]=='verify-blob' and args[1]=='--bundle' "
        "and args[3]=='--certificate-identity' and args[5]=='--certificate-oidc-issuer' "
        "and pathlib.Path(args[2]).is_file() and pathlib.Path(args[7]).is_file())\n"
        f"sys.exit({exit_code} if ok else 97)\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path.resolve()


def registry(
    root: Path,
    receipt: dict,
    bundle: Path,
    binary: Path,
    *,
    backend: str = "external-signature-verifier",
    enabled: bool = True,
    allowed_targets: list[str] | None = None,
) -> dict:
    return {
        "schema": "adk-native-conformance-trust-registry/v1",
        "status": "active",
        "authority_model": "owner-reviewed-managed-registry",
        "authorities": {
            "ci-native-conformance": {
                "enabled": enabled,
                "policy_backend": backend,
                "verifier": "sigstore-cosign-blob",
                "allowed_targets": allowed_targets or ["claude-code"],
                "certificate_identity": "https://github.com/example/repo/.github/workflows/native.yml@refs/heads/main",
                "certificate_oidc_issuer": "https://token.actions.githubusercontent.com",
                "cosign_binary": str(binary),
                "cosign_binary_sha256": sha256(binary),
                "receipts": {
                    receipt["receipt_id"]: {
                        "receipt_canonical_sha256": hashlib.sha256(
                            canonical_json_bytes(receipt)
                        ).hexdigest(),
                        "bundle_path": bundle.relative_to(root).as_posix(),
                        "bundle_sha256": sha256(bundle),
                    }
                },
            }
        },
    }


class ManagedNativeTrustVerifierTest(unittest.TestCase):
    def test_repository_registry_enables_no_authority_by_default(self) -> None:
        value = load_native_trust_registry(ROOT)
        self.assertEqual(value["schema"], "adk-native-conformance-trust-registry/v1")
        self.assertEqual(value["status"], "active")
        self.assertEqual(value["authorities"], {})

    def test_managed_verifier_accepts_only_registered_exact_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "manifests").mkdir()
            (root / "reports").mkdir()
            binary = fake_cosign(root)
            bundle = root / "reports" / "receipt.sigstore.json"
            bundle.write_text('{"fixture":"bundle"}\n', encoding="utf-8")
            receipt = {
                "receipt_id": "native-r1",
                "stages": [
                    {"authority": {"authority_id": "ci-native-conformance"}},
                    {"authority": {"authority_id": "ci-native-conformance"}},
                    {"authority": {"authority_id": "ci-native-conformance"}},
                ],
            }
            (root / "manifests" / "native_conformance_trust_registry.json").write_text(
                json.dumps(registry(root, receipt, bundle, binary), indent=2) + "\n",
                encoding="utf-8",
            )
            manifest = Manifest(root, {}, root / "manifest.json")
            policy = {
                "enabled": True,
                "trusted_authorities": ["ci-native-conformance"],
                "verification_backend": "external-signature-verifier",
            }
            verifier = build_managed_native_trust_verifier(manifest, "claude-code", policy)
            self.assertTrue(verifier(receipt, policy))

            changed = copy.deepcopy(receipt)
            changed["extra"] = "drift"
            with self.assertRaisesRegex(ManifestError, "receipt_digest_mismatch"):
                verifier(changed, policy)

            other_policy = dict(policy)
            other_policy["verification_backend"] = "ci-provenance-verifier"
            with self.assertRaisesRegex(ManifestError, "policy_changed"):
                verifier(receipt, other_policy)

    def test_verifier_fails_closed_for_scope_binary_bundle_and_signature(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "manifests").mkdir()
            (root / "reports").mkdir()
            binary = fake_cosign(root)
            bundle = root / "reports" / "receipt.sigstore.json"
            bundle.write_text("{}\n", encoding="utf-8")
            receipt = {
                "receipt_id": "native-r2",
                "stages": [
                    {"authority": {"authority_id": "ci-native-conformance"}},
                    {"authority": {"authority_id": "ci-native-conformance"}},
                    {"authority": {"authority_id": "ci-native-conformance"}},
                ],
            }
            policy = {
                "enabled": True,
                "trusted_authorities": ["ci-native-conformance"],
                "verification_backend": "external-signature-verifier",
            }
            base = registry(root, receipt, bundle, binary)

            def verify(value: dict) -> bool:
                (root / "manifests" / "native_conformance_trust_registry.json").write_text(
                    json.dumps(value), encoding="utf-8"
                )
                verifier = build_managed_native_trust_verifier(
                    Manifest(root, {}, root / "manifest.json"), "claude-code", policy
                )
                return verifier(receipt, policy)

            wrong_target = copy.deepcopy(base)
            wrong_target["authorities"]["ci-native-conformance"]["allowed_targets"] = ["opencode"]
            with self.assertRaisesRegex(ManifestError, "target_not_allowed"):
                verify(wrong_target)

            wrong_binary = copy.deepcopy(base)
            wrong_binary["authorities"]["ci-native-conformance"]["cosign_binary_sha256"] = "0" * 64
            with self.assertRaisesRegex(ManifestError, "cosign_digest_mismatch"):
                verify(wrong_binary)

            wrong_bundle = copy.deepcopy(base)
            wrong_bundle["authorities"]["ci-native-conformance"]["receipts"]["native-r2"][
                "bundle_sha256"
            ] = "0" * 64
            with self.assertRaisesRegex(ManifestError, "bundle_digest_mismatch"):
                verify(wrong_bundle)

            failed_binary = fake_cosign(root, exit_code=1)
            failed = registry(root, receipt, bundle, failed_binary)
            self.assertFalse(verify(failed))

    def test_production_loader_auto_injects_managed_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "manifests" / "target-contracts").mkdir(parents=True)
            (root / "schemas").mkdir()
            (root / "reports" / "runtime").mkdir(parents=True)

            for source, destination in (
                (ROOT / "manifests" / "target-contract.schema.json", root / "manifests" / "target-contract.schema.json"),
                (
                    ROOT / "schemas" / "native-target-conformance-receipt-v1.schema.json",
                    root / "schemas" / "native-target-conformance-receipt-v1.schema.json",
                ),
            ):
                destination.write_bytes(source.read_bytes())

            contract = json.loads(
                (ROOT / "manifests" / "target-contracts" / "claude-code.json").read_text(
                    encoding="utf-8"
                )
            )
            today = dt.date.today()
            contract["source"]["retrieved_at"] = today.isoformat()
            contract["source"]["expires_at"] = (today + dt.timedelta(days=30)).isoformat()
            for capability in ("discovery", "load", "trigger"):
                contract["adapter"]["capabilities"][capability] = "native-verified"
            conformance = {
                "level": "runtime",
                "certification": "conformance-certified",
                "native_runtime_smoke": "pass",
                "runtime_binary": "claude",
                "runtime_binary_sha256": "b" * 64,
                "runtime_version": "2.1.138",
                "runtime_version_pin": "2.1.138",
                "last_verified_at": None,
                "evidence": [],
            }
            contract["adapter"]["conformance"] = conformance
            contract["adapter"]["conformance_trust_policy"] = {
                "enabled": True,
                "trusted_authorities": ["ci-native-conformance"],
                "verification_backend": "ci-provenance-verifier",
            }
            contract_digest = _native_contract_digest(contract)
            bundle_digest = "c" * 64
            now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
            base = now - dt.timedelta(minutes=4)
            stages = []
            for index, stage_name in enumerate(("discovery", "load", "trigger")):
                started = base + dt.timedelta(minutes=index)
                completed = started + dt.timedelta(seconds=10)
                authority = {
                    "execution_authority": "ci-approved",
                    "authority_id": "ci-native-conformance",
                    "scope": stage_name,
                }
                authority["attestation_sha256"] = _authority_digest(authority)
                stages.append(
                    {
                        "stage": stage_name,
                        "command_sha256": str(index + 1) * 64,
                        "result_sha256": str(index + 4) * 64,
                        "exit_code": 0,
                        "started_at": started.isoformat().replace("+00:00", "Z"),
                        "completed_at": completed.isoformat().replace("+00:00", "Z"),
                        "duration_ms": 10000,
                        "environment": {
                            "platform": "linux",
                            "architecture": "x86_64",
                            "cwd_sha256": "7" * 64,
                            "environment_sha256": "8" * 64,
                            "runtime_binary_sha256": "b" * 64,
                            "bundle_sha256": bundle_digest,
                            "contract_sha256": contract_digest,
                        },
                        "privacy": {
                            "raw_content_stored": False,
                            "secrets_stored": False,
                            "sanitized": True,
                        },
                        "authority": authority,
                    }
                )
            receipt = {
                "schema": "adk-native-target-conformance-receipt/v1",
                "receipt_id": "claude-native-managed",
                "target": "claude-code",
                "runtime": {
                    "binary": "claude",
                    "binary_sha256": "b" * 64,
                    "version": "2.1.138",
                    "version_pin": "2.1.138",
                },
                "bundle_sha256": bundle_digest,
                "contract_sha256": contract_digest,
                "verified_at": now.isoformat().replace("+00:00", "Z"),
                "stages": stages,
            }
            receipt_path = root / "reports" / "runtime" / "receipt.json"
            receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
            conformance["last_verified_at"] = receipt["verified_at"]
            conformance["evidence"] = [
                {
                    "receipt_schema": receipt["schema"],
                    "path": receipt_path.relative_to(root).as_posix(),
                    "sha256": sha256(receipt_path),
                    "target": "claude-code",
                    "runtime_version": "2.1.138",
                    "bundle_sha256": bundle_digest,
                    "contract_sha256": contract_digest,
                    "layer": "runtime",
                }
            ]
            contract_path = root / "manifests" / "target-contracts" / "claude-code.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

            binary = fake_cosign(root)
            bundle = root / "reports" / "runtime" / "receipt.sigstore.json"
            bundle.write_text('{"fixture":"sigstore"}\n', encoding="utf-8")
            reg = registry(
                root,
                receipt,
                bundle,
                binary,
                backend="ci-provenance-verifier",
            )
            (root / "manifests" / "native_conformance_trust_registry.json").write_text(
                json.dumps(reg, indent=2) + "\n", encoding="utf-8"
            )
            manifest = Manifest(
                root,
                {
                    "tool_targets": {
                        "claude-code": {
                            "contract": "manifests/target-contracts/claude-code.json"
                        }
                    },
                    "external_handoff_targets": {},
                },
                root / "manifest.json",
            )
            loaded = load_target_contract(manifest, "claude-code")
            self.assertEqual(loaded.adapter["conformance"]["level"], "runtime")

            empty = copy.deepcopy(reg)
            empty["authorities"] = {}
            (root / "manifests" / "native_conformance_trust_registry.json").write_text(
                json.dumps(empty), encoding="utf-8"
            )
            with self.assertRaisesRegex(ManifestError, "native trust verifier failed"):
                load_target_contract(manifest, "claude-code")


if __name__ == "__main__":
    unittest.main()
