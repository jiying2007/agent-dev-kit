"""Validate privacy-bounded Agent Value invocation receipts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from . import agent_value_contracts as value_contracts
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import (
    opaque_ref_for_sha256,
    validate_identifier,
    validate_no_secrets,
    validate_opaque_ref,
    validate_sha256,
)


RECEIPT_SCHEMA_VERSION = "adk-asset-invocation-receipt/v1"
EvidenceVerifier = Callable[[Mapping[str, Any], Mapping[str, Any]], bool]


def validate_receipt(
    receipt: Mapping[str, Any],
    manifest: Manifest,
    contract: Mapping[str, Any],
    schema_path: Optional[Path] = None,
    evidence_verifier: Optional[EvidenceVerifier] = None,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    value_contracts.validate_contract(contract, manifest)
    validate_no_secrets(receipt, "invocation receipt")
    receipt_contract = contract.get("receipt_contract")
    if not isinstance(receipt_contract, dict):
        raise ManifestError("agent value contract receipt_contract is invalid")
    if receipt_contract.get("evidence_ref_format") != "ref:<sha256>":
        raise ManifestError("agent value contract must require opaque evidence refs")
    schema_path = schema_path or manifest.root / str(receipt_contract.get("schema_path", ""))
    value_contracts._validate_schema(receipt, schema_path, "asset invocation receipt")
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise ManifestError("unsupported asset invocation receipt schema")
    if receipt.get("measurement_status") != "measured":
        raise ManifestError("persisted invocation receipts must contain measured evidence")
    if receipt.get("raw_content_stored") is not False:
        raise ManifestError("invocation receipt must not store raw content")
    receipt_id = validate_opaque_ref(receipt.get("receipt_id"), "receipt_id")
    validate_opaque_ref(receipt.get("invocation_ref"), "receipt invocation_ref")
    validate_opaque_ref(receipt.get("source_trace_ref"), "receipt source_trace_ref")
    manifest_ref = validate_opaque_ref(receipt.get("manifest_ref"), "receipt manifest_ref")
    expected_manifest_ref = opaque_ref_for_sha256(manifest.digest)
    if manifest_ref != expected_manifest_ref:
        raise ManifestError("receipt manifest_ref differs from the current manifest digest")
    validate_sha256(receipt.get("asset_bundle_sha256"), "receipt asset_bundle_sha256")
    validate_identifier(receipt.get("runtime_target"), "receipt runtime_target")
    evidence_refs = receipt.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        raise ManifestError("receipt evidence_refs must be a non-empty array")
    for index, evidence_ref in enumerate(evidence_refs):
        validate_opaque_ref(evidence_ref, "receipt evidence_refs[{}]".format(index))

    receipt_payload = dict(receipt)
    receipt_payload.pop("receipt_id", None)
    receipt_payload.pop("authority_attestation", None)
    receipt_payload_sha256 = sha256_bytes(canonical_json_bytes(receipt_payload))

    receipt_body = dict(receipt)
    receipt_body.pop("receipt_id", None)
    expected_receipt_id = opaque_ref_for_sha256(sha256_bytes(canonical_json_bytes(receipt_body)))
    if receipt_id != expected_receipt_id:
        raise ManifestError("receipt_id must bind the canonical receipt body; hash integrity is not source authority")

    observed_at = receipt.get("observed_at")
    try:
        parsed_observed_at = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("receipt observed_at must be a valid RFC 3339 timestamp") from exc
    if parsed_observed_at.tzinfo is None:
        raise ManifestError("receipt observed_at must include a timezone")
    system_now = datetime.now(timezone.utc)
    upper_bound = as_of or system_now
    if upper_bound.tzinfo is None:
        raise ManifestError("receipt as_of must include a timezone")
    upper_bound = upper_bound.astimezone(timezone.utc)
    if upper_bound > system_now:
        raise ManifestError("receipt as_of must not be in the future")
    if parsed_observed_at.astimezone(timezone.utc) > upper_bound.astimezone(timezone.utc):
        raise ManifestError("receipt observed_at must not be in the future")
    max_age_days = int(receipt_contract["max_age_days"])
    if parsed_observed_at.astimezone(timezone.utc) < upper_bound - timedelta(days=max_age_days):
        raise ManifestError("receipt observed_at exceeds the configured max_age_days")

    evidence_layer = receipt.get("evidence_layer")
    authority_production = False
    if evidence_layer in ("runtime", "field"):
        authority_policy = contract["evidence_authority_policy"]
        if authority_policy.get("status") != "enabled":
            raise ManifestError("runtime/field receipt requires an enabled managed evidence authority registry")
        attestation = receipt.get("authority_attestation")
        if not isinstance(attestation, dict):
            raise ManifestError("runtime/field receipt requires an authority attestation")
        authority_id = attestation.get("authority_id")
        authority = next(
            (
                item
                for item in authority_policy.get("authorities", [])
                if isinstance(item, dict) and item.get("authority_id") == authority_id
            ),
            None,
        )
        if authority is None:
            raise ManifestError("runtime/field receipt authority is not registered")
        runtime_target = receipt.get("runtime_target")
        if evidence_layer not in authority.get("allowed_layers", []):
            raise ManifestError("receipt evidence layer is outside authority scope")
        if runtime_target not in authority.get("runtime_targets", []):
            raise ManifestError("receipt runtime target is outside authority scope")
        expected_attestation = {
            "authority_id": authority_id,
            "body_sha256": receipt_payload_sha256,
            "manifest_ref": receipt["manifest_ref"],
            "asset_bundle_sha256": receipt["asset_bundle_sha256"],
            "evidence_layer": evidence_layer,
            "runtime_target": runtime_target,
            "source_trace_ref": receipt["source_trace_ref"],
        }
        if attestation != expected_attestation:
            raise ManifestError("authority attestation does not bind the canonical receipt payload and scope")
        if evidence_verifier is None:
            raise ManifestError("runtime/field receipt requires an injected evidence verifier")
        try:
            verifier_input = json.loads(canonical_json_bytes(receipt).decode("utf-8"))
            authority_input = json.loads(canonical_json_bytes(authority).decode("utf-8"))
            verified = evidence_verifier(verifier_input, authority_input)
        except Exception as exc:
            raise ManifestError("runtime/field evidence verifier failed") from exc
        if verified is not True:
            raise ManifestError("runtime/field evidence verifier did not attest the receipt")
        authority_production = authority.get("production") is True

    identities = value_contracts._manifest_identity_index(manifest)
    asset_kind = receipt.get("asset_kind")
    asset_id = receipt.get("asset_id")
    if asset_kind not in identities or asset_id not in identities[str(asset_kind)]:
        raise ManifestError("invocation receipt references an unknown manifest asset")

    routing = receipt.get("routing")
    if not isinstance(routing, dict):
        raise ManifestError("invocation receipt routing must be an object")
    routed = routing.get("routed")
    abstained = routing.get("abstained")
    wrong_route = routing.get("wrong_route")
    if not all(isinstance(item, bool) for item in (routed, abstained, wrong_route)):
        raise ManifestError("invocation receipt routing metrics must be boolean")
    if routed == abstained:
        raise ManifestError("invocation receipt must be exactly one of routed or abstained")
    if wrong_route and not routed:
        raise ManifestError("wrong_route requires routed=true")
    if (receipt.get("outcome") == "abstained") != abstained:
        raise ManifestError("abstained routing and outcome must agree")
    interventions = receipt.get("human_interventions")
    if not isinstance(interventions, int) or isinstance(interventions, bool) or interventions < 0:
        raise ManifestError("human_interventions must be a non-negative integer")
    signals = set(contract["asset_lifecycle"]["retirement_signals"])
    if receipt.get("retirement_signal") not in signals:
        raise ManifestError("invocation receipt retirement signal is not allowed by the contract")

    return {
        "status": "pass",
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_id": receipt["receipt_id"],
        "asset_id": asset_id,
        "asset_kind": asset_kind,
        "measurement_status": "measured",
        "evidence_layer": evidence_layer,
        "source_verification": "managed-authority-verified" if evidence_layer in ("runtime", "field") else "structural-only",
        "authority_production": authority_production,
        "privacy_status": receipt["privacy_status"],
        "raw_content_stored": False,
        "retirement_authority": "signal-only-owner-decision-required",
    }
