"""Managed trust verifier for native target conformance receipts.

The verifier is deliberately opt-in. Static targets never invoke it. Runtime
conformance may use it only when both the target trust policy and the managed
registry enable the same authority/backend. Signature verification is delegated
to a digest-pinned cosign binary without a shell.
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

from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within

REGISTRY_SCHEMA = "adk-native-conformance-trust-registry/v1"
MAX_REGISTRY_BYTES = 256 * 1024
MAX_BUNDLE_BYTES = 1024 * 1024
SUPPORTED_POLICY_BACKENDS = frozenset({"external-signature-verifier", "ci-provenance-verifier"})
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


def load_native_trust_registry(root: Path) -> Mapping[str, Any]:
    path = ensure_within(
        root / "manifests" / "native_conformance_trust_registry.json",
        root,
        "native conformance trust registry",
    )
    value = _json_object(path, limit=MAX_REGISTRY_BYTES, label="native conformance trust registry")
    if set(value) != {"schema", "status", "authority_model", "authorities"}:
        raise ManifestError("native_trust_registry_invalid: top-level fields")
    if value.get("schema") != REGISTRY_SCHEMA or value.get("status") != "active":
        raise ManifestError("native_trust_registry_invalid: schema/status")
    if value.get("authority_model") != "owner-reviewed-managed-registry":
        raise ManifestError("native_trust_registry_invalid: authority_model")
    authorities = value.get("authorities")
    if not isinstance(authorities, dict):
        raise ManifestError("native_trust_registry_invalid: authorities must be an object")
    for authority_id, authority in authorities.items():
        if (
            not isinstance(authority_id, str)
            or not authority_id
            or len(authority_id) > 128
            or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-" for ch in authority_id)
            or not isinstance(authority, dict)
        ):
            raise ManifestError("native_trust_registry_invalid: authority entry")
        required = {
            "enabled",
            "policy_backend",
            "verifier",
            "allowed_targets",
            "certificate_identity",
            "certificate_oidc_issuer",
            "cosign_binary",
            "cosign_binary_sha256",
            "receipts",
        }
        if set(authority) != required:
            raise ManifestError(f"native_trust_registry_invalid: authority fields: {authority_id}")
        if authority["policy_backend"] not in SUPPORTED_POLICY_BACKENDS:
            raise ManifestError(f"native_trust_registry_invalid: backend: {authority_id}")
        if authority["verifier"] != SUPPORTED_VERIFIER:
            raise ManifestError(f"native_trust_registry_invalid: verifier: {authority_id}")
        if not isinstance(authority["enabled"], bool):
            raise ManifestError(f"native_trust_registry_invalid: enabled: {authority_id}")
        if (
            not isinstance(authority["allowed_targets"], list)
            or len(authority["allowed_targets"]) > 32
            or len(set(authority["allowed_targets"])) != len(authority["allowed_targets"])
            or not all(isinstance(item, str) and item for item in authority["allowed_targets"])
        ):
            raise ManifestError(f"native_trust_registry_invalid: allowed_targets: {authority_id}")
        for field in ("certificate_identity", "certificate_oidc_issuer", "cosign_binary"):
            if not isinstance(authority[field], str) or "\x00" in authority[field] or "\n" in authority[field] or "\r" in authority[field]:
                raise ManifestError(f"native_trust_registry_invalid: {field}: {authority_id}")
        if authority["certificate_identity"] and not authority["certificate_identity"].startswith("https://"):
            raise ManifestError(f"native_trust_registry_invalid: certificate_identity: {authority_id}")
        if authority["certificate_oidc_issuer"] and not authority["certificate_oidc_issuer"].startswith("https://"):
            raise ManifestError(f"native_trust_registry_invalid: certificate_oidc_issuer: {authority_id}")
        binary_value = authority["cosign_binary"]
        if binary_value and not Path(binary_value).is_absolute() and any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-" for ch in binary_value):
            raise ManifestError(f"native_trust_registry_invalid: cosign_binary: {authority_id}")
        digest = authority["cosign_binary_sha256"]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise ManifestError(f"native_trust_registry_invalid: cosign digest: {authority_id}")
        receipts = authority["receipts"]
        if not isinstance(receipts, dict) or len(receipts) > 256:
            raise ManifestError(f"native_trust_registry_invalid: receipts: {authority_id}")
        for receipt_id, record in receipts.items():
            if not isinstance(receipt_id, str) or not receipt_id or len(receipt_id) > 128 or not isinstance(record, dict):
                raise ManifestError(f"native_trust_registry_invalid: receipt entry: {authority_id}")
            if set(record) != {"receipt_canonical_sha256", "bundle_path", "bundle_sha256"}:
                raise ManifestError(f"native_trust_registry_invalid: receipt fields: {receipt_id}")
            for field in ("receipt_canonical_sha256", "bundle_sha256"):
                item = record[field]
                if (
                    not isinstance(item, str)
                    or len(item) != 64
                    or any(ch not in "0123456789abcdef" for ch in item)
                ):
                    raise ManifestError(f"native_trust_registry_invalid: {field}: {receipt_id}")
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
                raise ManifestError(f"native_trust_registry_invalid: bundle_path: {receipt_id}")
        if authority["enabled"] is True:
            if not authority["allowed_targets"] or not authority["certificate_identity"] or not authority["certificate_oidc_issuer"]:
                raise ManifestError(f"native_trust_registry_invalid: enabled authority identity/scope: {authority_id}")
            if not isinstance(authority["cosign_binary_sha256"], str) or not authority["cosign_binary"]:
                raise ManifestError(f"native_trust_registry_invalid: enabled authority cosign pin: {authority_id}")
    return value


class ManagedNativeTrustVerifier:
    def __init__(
        self,
        manifest: Manifest,
        target: str,
        trust_policy: Mapping[str, Any],
        registry: Mapping[str, Any],
    ) -> None:
        self._manifest = manifest
        self._target = target
        self._policy = trust_policy
        self._registry = registry

    def __call__(self, receipt: Mapping[str, Any], trust_policy: Mapping[str, Any]) -> bool:
        if trust_policy != self._policy:
            raise ManifestError("native_trust_policy_changed_during_verification")
        backend = trust_policy.get("verification_backend")
        if backend not in SUPPORTED_POLICY_BACKENDS:
            raise ManifestError("native_trust_backend_unsupported")
        stages = receipt.get("stages")
        if not isinstance(stages, list) or not stages:
            raise ManifestError("native_trust_receipt_stages_missing")
        authority_ids = {
            stage.get("authority", {}).get("authority_id")
            for stage in stages
            if isinstance(stage, dict) and isinstance(stage.get("authority"), dict)
        }
        if len(authority_ids) != 1:
            raise ManifestError("native_trust_requires_one_receipt_authority")
        authority_id = next(iter(authority_ids))
        if not isinstance(authority_id, str):
            raise ManifestError("native_trust_authority_missing")
        if authority_id not in trust_policy.get("trusted_authorities", []):
            raise ManifestError("native_trust_authority_not_in_target_policy")
        authority = self._registry["authorities"].get(authority_id)
        if not isinstance(authority, dict) or authority.get("enabled") is not True:
            raise ManifestError("native_trust_authority_disabled_or_missing")
        if authority.get("policy_backend") != backend:
            raise ManifestError("native_trust_backend_policy_mismatch")
        if self._target not in authority.get("allowed_targets", []):
            raise ManifestError("native_trust_target_not_allowed")

        receipt_id = receipt.get("receipt_id")
        records = authority.get("receipts", {})
        record = records.get(receipt_id) if isinstance(receipt_id, str) and isinstance(records, dict) else None
        if not isinstance(record, dict):
            raise ManifestError("native_trust_receipt_not_registered")
        canonical = canonical_json_bytes(receipt)
        if hashlib.sha256(canonical).hexdigest() != record["receipt_canonical_sha256"]:
            raise ManifestError("native_trust_receipt_digest_mismatch")

        bundle = ensure_within(
            self._manifest.root / str(record["bundle_path"]),
            self._manifest.root,
            "native trust signature bundle",
        )
        if bundle.suffix != ".json" or bundle.is_symlink() or not bundle.is_file():
            raise ManifestError("native_trust_bundle_missing_or_unsafe")
        if bundle.stat().st_size > MAX_BUNDLE_BYTES:
            raise ManifestError("native_trust_bundle_exceeds_byte_budget")
        if _sha256_file(bundle) != record["bundle_sha256"]:
            raise ManifestError("native_trust_bundle_digest_mismatch")

        binary_name = authority["cosign_binary"]
        binary = Path(binary_name)
        if binary.is_absolute():
            resolved_binary = binary.resolve()
        else:
            located = shutil.which(binary_name)
            if located is None:
                raise ManifestError("native_trust_cosign_not_found")
            resolved_binary = Path(located).resolve()
        if not resolved_binary.is_file():
            raise ManifestError("native_trust_cosign_not_regular")
        expected_binary_digest = authority["cosign_binary_sha256"]
        if not isinstance(expected_binary_digest, str):
            raise ManifestError("native_trust_cosign_digest_not_configured")
        if _sha256_file(resolved_binary) != expected_binary_digest:
            raise ManifestError("native_trust_cosign_digest_mismatch")

        identity = authority["certificate_identity"]
        issuer = authority["certificate_oidc_issuer"]
        if not identity or not issuer:
            raise ManifestError("native_trust_certificate_identity_not_configured")

        descriptor, name = tempfile.mkstemp(prefix="adk-native-receipt-", suffix=".json")
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical)
                stream.flush()
                os.fsync(stream.fileno())
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
                    name,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise ManifestError("native_trust_cosign_timeout") from exc
        finally:
            try:
                os.unlink(name)
            except OSError:
                pass
        return completed.returncode == 0


def build_managed_native_trust_verifier(
    manifest: Manifest,
    target: str,
    trust_policy: Mapping[str, Any],
) -> ManagedNativeTrustVerifier:
    if trust_policy.get("enabled") is not True:
        raise ManifestError("native_trust_policy_disabled")
    registry = load_native_trust_registry(manifest.root)
    return ManagedNativeTrustVerifier(manifest, target, trust_policy, registry)
