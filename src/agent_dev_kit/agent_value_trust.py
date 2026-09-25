"""Managed trust verifier for Agent Value runtime/field invocation receipts.

The canonical Agent Value contract remains disabled by default. This module only
provides a repository-governed verifier path for a separately reviewed enabled
contract. It does not collect receipts, enable a runtime, or authorize lifecycle
mutation.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

from . import agent_value_contracts as value_contracts
from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within

REGISTRY_SCHEMA = "adk-agent-value-trust-registry/v1"
MAX_REGISTRY_BYTES = 256 * 1024
MAX_BUNDLE_BYTES = 1024 * 1024
SUPPORTED_POLICY_BACKENDS = frozenset(
    {"external-signature-verifier", "ci-provenance-verifier"}
)
SUPPORTED_VERIFIER = "sigstore-cosign-blob"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_object(path: Path, *, limit: int, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ManifestError(f"{label} is missing or unsafe: {path}")
    if path.stat().st_size > limit:
        raise ManifestError(f"{label} exceeds byte budget: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"{label} is invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a JSON object: {path}")
    return value


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _safe_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or any(
            ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-"
            for ch in value
        )
    ):
        raise ManifestError(f"agent_value_trust_registry_invalid: {label}")
    return value


def validate_agent_value_trust_registry(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    if set(value) != {"schema", "status", "authority_model", "authorities"}:
        raise ManifestError(
            "agent_value_trust_registry_invalid: top-level fields"
        )
    if value.get("schema") != REGISTRY_SCHEMA or value.get("status") != "active":
        raise ManifestError("agent_value_trust_registry_invalid: schema/status")
    if value.get("authority_model") != "owner-reviewed-managed-registry":
        raise ManifestError(
            "agent_value_trust_registry_invalid: authority_model"
        )
    authorities = value.get("authorities")
    if not isinstance(authorities, dict) or len(authorities) > 64:
        raise ManifestError(
            "agent_value_trust_registry_invalid: authorities must be a bounded object"
        )

    for authority_id, authority in authorities.items():
        _safe_identifier(authority_id, "authority_id")
        if not isinstance(authority, dict):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: authority entry: {authority_id}"
            )
        required = {
            "enabled",
            "policy_backend",
            "verifier",
            "allowed_layers",
            "runtime_targets",
            "certificate_identity",
            "certificate_oidc_issuer",
            "cosign_binary",
            "cosign_binary_sha256",
            "receipts",
        }
        if set(authority) != required:
            raise ManifestError(
                f"agent_value_trust_registry_invalid: authority fields: {authority_id}"
            )
        if not isinstance(authority["enabled"], bool):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: enabled: {authority_id}"
            )
        if authority["policy_backend"] not in SUPPORTED_POLICY_BACKENDS:
            raise ManifestError(
                f"agent_value_trust_registry_invalid: backend: {authority_id}"
            )
        if authority["verifier"] != SUPPORTED_VERIFIER:
            raise ManifestError(
                f"agent_value_trust_registry_invalid: verifier: {authority_id}"
            )

        layers = authority["allowed_layers"]
        if (
            not isinstance(layers, list)
            or not layers
            or len(layers) != len(set(layers))
            or any(layer not in ("runtime", "field") for layer in layers)
        ):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: allowed_layers: {authority_id}"
            )
        targets = authority["runtime_targets"]
        if (
            not isinstance(targets, list)
            or not targets
            or len(targets) > 32
            or len(targets) != len(set(targets))
        ):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: runtime_targets: {authority_id}"
            )
        for target in targets:
            _safe_identifier(target, "runtime_target")

        for field in (
            "certificate_identity",
            "certificate_oidc_issuer",
            "cosign_binary",
        ):
            item = authority[field]
            if (
                not isinstance(item, str)
                or "\x00" in item
                or "\n" in item
                or "\r" in item
            ):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: {field}: {authority_id}"
                )
        if authority["certificate_identity"] and not authority[
            "certificate_identity"
        ].startswith("https://"):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: certificate_identity: {authority_id}"
            )
        if authority["certificate_oidc_issuer"] and not authority[
            "certificate_oidc_issuer"
        ].startswith("https://"):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: certificate_oidc_issuer: {authority_id}"
            )
        binary_value = authority["cosign_binary"]
        if binary_value:
            if Path(binary_value).name != "cosign":
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: cosign binary name: {authority_id}"
                )
            if (
                not Path(binary_value).is_absolute()
                and any(
                    ch
                    not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
                    for ch in binary_value
                )
            ):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: cosign_binary: {authority_id}"
                )
        digest = authority["cosign_binary_sha256"]
        if digest is not None and not _valid_sha256(digest):
            raise ManifestError(
                f"agent_value_trust_registry_invalid: cosign digest: {authority_id}"
            )

        receipts = authority["receipts"]
        if not isinstance(receipts, dict) or len(receipts) > 1024:
            raise ManifestError(
                f"agent_value_trust_registry_invalid: receipts: {authority_id}"
            )
        for receipt_id, record in receipts.items():
            if (
                not isinstance(receipt_id, str)
                or not receipt_id.startswith("ref:")
                or len(receipt_id) != 68
                or not _valid_sha256(receipt_id[4:])
                or not isinstance(record, dict)
            ):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: receipt entry: {authority_id}"
                )
            if set(record) != {
                "receipt_canonical_sha256",
                "bundle_path",
                "bundle_sha256",
            }:
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: receipt fields: {receipt_id}"
                )
            if not _valid_sha256(record["receipt_canonical_sha256"]):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: receipt digest: {receipt_id}"
                )
            if not _valid_sha256(record["bundle_sha256"]):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: bundle digest: {receipt_id}"
                )
            bundle_path = record["bundle_path"]
            if (
                not isinstance(bundle_path, str)
                or not bundle_path
                or Path(bundle_path).is_absolute()
                or ".." in Path(bundle_path).parts
                or "\\" in bundle_path
                or "\x00" in bundle_path
                or "\n" in bundle_path
                or "\r" in bundle_path
            ):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: bundle_path: {receipt_id}"
                )

        if authority["enabled"]:
            if (
                not authority["certificate_identity"]
                or not authority["certificate_oidc_issuer"]
                or not authority["cosign_binary"]
                or not isinstance(authority["cosign_binary_sha256"], str)
            ):
                raise ManifestError(
                    f"agent_value_trust_registry_invalid: enabled authority trust identity: {authority_id}"
                )
    return value


def load_agent_value_trust_registry(root: Path) -> Mapping[str, Any]:
    path = ensure_within(
        root / "manifests" / "agent_value_trust_registry.json",
        root,
        "Agent Value trust registry",
    )
    value = _json_object(
        path, limit=MAX_REGISTRY_BYTES, label="Agent Value trust registry"
    )
    return validate_agent_value_trust_registry(value)


class ManagedAgentValueEvidenceVerifier:
    def __init__(
        self,
        manifest: Manifest,
        contract: Mapping[str, Any],
        registry: Mapping[str, Any],
    ) -> None:
        value_contracts.validate_contract(contract, manifest)
        policy = contract.get("evidence_authority_policy")
        if not isinstance(policy, dict) or policy.get("status") != "enabled":
            raise ManifestError("agent_value_trust_policy_disabled")
        if policy.get("backend") not in SUPPORTED_POLICY_BACKENDS:
            raise ManifestError("agent_value_trust_backend_unsupported")
        self._manifest = manifest
        self._contract = contract
        self._policy = policy
        self._registry = validate_agent_value_trust_registry(registry)

    def __call__(
        self,
        receipt: Mapping[str, Any],
        contract_authority: Mapping[str, Any],
    ) -> bool:
        authority_id = contract_authority.get("authority_id")
        if not isinstance(authority_id, str):
            raise ManifestError("agent_value_trust_authority_missing")
        policy_authority = next(
            (
                item
                for item in self._policy.get("authorities", [])
                if isinstance(item, dict) and item.get("authority_id") == authority_id
            ),
            None,
        )
        if policy_authority is None or dict(policy_authority) != dict(contract_authority):
            raise ManifestError("agent_value_trust_contract_authority_drift")

        registry_authority = self._registry["authorities"].get(authority_id)
        if (
            not isinstance(registry_authority, dict)
            or registry_authority.get("enabled") is not True
        ):
            raise ManifestError("agent_value_trust_authority_disabled_or_missing")
        if registry_authority.get("policy_backend") != self._policy.get("backend"):
            raise ManifestError("agent_value_trust_backend_policy_mismatch")
        if set(registry_authority.get("allowed_layers", [])) != set(
            contract_authority.get("allowed_layers", [])
        ):
            raise ManifestError("agent_value_trust_layer_scope_mismatch")
        if set(registry_authority.get("runtime_targets", [])) != set(
            contract_authority.get("runtime_targets", [])
        ):
            raise ManifestError("agent_value_trust_target_scope_mismatch")

        layer = receipt.get("evidence_layer")
        target = receipt.get("runtime_target")
        if layer not in registry_authority["allowed_layers"]:
            raise ManifestError("agent_value_trust_receipt_layer_not_allowed")
        if target not in registry_authority["runtime_targets"]:
            raise ManifestError("agent_value_trust_receipt_target_not_allowed")

        receipt_id = receipt.get("receipt_id")
        records = registry_authority.get("receipts", {})
        record = (
            records.get(receipt_id)
            if isinstance(receipt_id, str) and isinstance(records, dict)
            else None
        )
        if not isinstance(record, dict):
            raise ManifestError("agent_value_trust_receipt_not_registered")
        canonical = canonical_json_bytes(receipt)
        if (
            hashlib.sha256(canonical).hexdigest()
            != record["receipt_canonical_sha256"]
        ):
            raise ManifestError("agent_value_trust_receipt_digest_mismatch")

        bundle = ensure_within(
            self._manifest.root / str(record["bundle_path"]),
            self._manifest.root,
            "Agent Value signature bundle",
        )
        if bundle.suffix != ".json" or bundle.is_symlink() or not bundle.is_file():
            raise ManifestError("agent_value_trust_bundle_missing_or_unsafe")
        if bundle.stat().st_size > MAX_BUNDLE_BYTES:
            raise ManifestError("agent_value_trust_bundle_exceeds_byte_budget")
        if _sha256_file(bundle) != record["bundle_sha256"]:
            raise ManifestError("agent_value_trust_bundle_digest_mismatch")

        binary_name = registry_authority["cosign_binary"]
        binary = Path(binary_name)
        if binary.is_absolute():
            resolved_binary = binary.resolve()
        else:
            located = shutil.which(binary_name)
            if located is None:
                raise ManifestError("agent_value_trust_cosign_not_found")
            resolved_binary = Path(located).resolve()
        if not resolved_binary.is_file():
            raise ManifestError("agent_value_trust_cosign_not_regular")
        expected_binary_digest = registry_authority["cosign_binary_sha256"]
        if not isinstance(expected_binary_digest, str):
            raise ManifestError("agent_value_trust_cosign_digest_not_configured")
        if _sha256_file(resolved_binary) != expected_binary_digest:
            raise ManifestError("agent_value_trust_cosign_digest_mismatch")

        identity = registry_authority["certificate_identity"]
        issuer = registry_authority["certificate_oidc_issuer"]
        if not identity or not issuer:
            raise ManifestError(
                "agent_value_trust_certificate_identity_not_configured"
            )

        verifier_env = {
            "PATH": os.defpath,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        for key in ("HOME", "XDG_CACHE_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR"):
            value = os.environ.get(key)
            if value:
                verifier_env[key] = value

        stdin_path = Path("/dev/stdin")
        if not stdin_path.exists():
            raise ManifestError("agent_value_trust_in_memory_verification_unsupported")
        with tempfile.TemporaryDirectory(prefix="adk-agent-value-trust-") as temporary:
            try:
                completed = subprocess.run(
                    [
                        str(resolved_binary),
                        "verify-blob",
                        "--bundle",
                        str(bundle),
                        "--certificate-identity",
                        identity,
                        "--certificate-oidc-issuer",
                        issuer,
                        str(stdin_path),
                    ],
                    cwd=temporary,
                    env=verifier_env,
                    input=canonical,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=30,
                )
            except subprocess.TimeoutExpired as exc:
                raise ManifestError("agent_value_trust_cosign_timeout") from exc
        return completed.returncode == 0


def build_managed_agent_value_evidence_verifier(
    manifest: Manifest,
    contract: Mapping[str, Any],
) -> ManagedAgentValueEvidenceVerifier:
    value_contracts.validate_contract(contract, manifest)
    policy = contract.get("evidence_authority_policy")
    if not isinstance(policy, dict) or policy.get("status") != "enabled":
        raise ManifestError("agent_value_trust_policy_disabled")
    registry = load_agent_value_trust_registry(manifest.root)
    return ManagedAgentValueEvidenceVerifier(manifest, contract, registry)
