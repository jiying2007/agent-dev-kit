"""Validate Agent role contracts and privacy-bounded asset invocation receipts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import (
    opaque_ref_for_sha256,
    validate_identifier,
    validate_no_secrets,
    validate_opaque_ref,
    validate_sha256,
)


CONTRACT_SCHEMA_VERSION = "adk-agent-value-contracts/v1"
RECEIPT_SCHEMA_VERSION = "adk-asset-invocation-receipt/v1"
MEASUREMENT_SCHEMA_VERSION = "adk-asset-value-measurement/v1"
EvidenceVerifier = Callable[[Mapping[str, Any], Mapping[str, Any]], bool]
REQUIRED_EVAL_CASE_TYPES = (
    "role-positive",
    "authority-negative",
    "permission-negative",
    "handoff",
    "evidence-gap",
)
PERMISSION_PROFILES: Dict[str, Dict[str, Any]] = {
    "read-only": {
        "rank": 0,
        "allowed_effects": ["read-only"],
        "allowed_tool_capabilities": ["repository-read", "static-analysis"],
    },
    "diagnostic": {
        "rank": 1,
        "allowed_effects": ["read-only", "diagnostic-execution"],
        "allowed_tool_capabilities": [
            "repository-read",
            "static-analysis",
            "diagnostic-command",
            "runtime-observation",
        ],
    },
    "code-write": {
        "rank": 2,
        "allowed_effects": ["read-only", "diagnostic-execution", "workspace-write"],
        "allowed_tool_capabilities": [
            "repository-read",
            "static-analysis",
            "diagnostic-command",
            "runtime-observation",
            "workspace-edit",
            "test-execution",
        ],
    },
    "build-release": {
        "rank": 3,
        "allowed_effects": [
            "read-only",
            "diagnostic-execution",
            "workspace-write",
            "build-artifact-write",
            "release-preparation",
        ],
        "allowed_tool_capabilities": [
            "repository-read",
            "static-analysis",
            "diagnostic-command",
            "runtime-observation",
            "workspace-edit",
            "test-execution",
            "build-execution",
            "artifact-packaging",
            "rollback-preparation",
        ],
    },
}
DIAGNOSTIC_ONLY_METRICS = {
    "agent-count",
    "skill-count",
    "profile-count",
    "invocation-count",
    "pr-count",
    "report-count",
    "input-tokens",
    "output-tokens",
    "total-tokens",
}


def _load_json(path: Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid: {}".format(label, exc)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} must be an object".format(label))
    return dict(value)


def _schema(path: Path, label: str) -> Draft202012Validator:
    value = _load_json(path, "{} schema".format(label))
    try:
        Draft202012Validator.check_schema(value)
    except SchemaError as exc:
        raise ManifestError("{} schema is invalid: {}".format(label, exc.message)) from exc
    return Draft202012Validator(value, format_checker=FormatChecker())


def _validate_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    errors = sorted(
        _schema(schema_path, label).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise ManifestError("{} schema validation failed at {}: {}".format(label, location, error.message))


def load_contract(path: Path, schema_path: Optional[Path] = None) -> Dict[str, Any]:
    value = _load_json(path, "agent value contract")
    schema_path = schema_path or path.parent.parent / "schemas" / "agent-value-contracts-v1.schema.json"
    _validate_schema(value, schema_path, "agent value contract")
    return value


def _manifest_identity_index(manifest: Manifest) -> Dict[str, set[str]]:
    agents = manifest.data.get("agents")
    core_skills = manifest.data.get("skills")
    optional_skills = manifest.data.get("optional_skills")
    profiles = manifest.data.get("profiles")
    if not isinstance(agents, list) or not isinstance(core_skills, list) or not isinstance(optional_skills, list):
        raise ManifestError("manifest Agent/Skill identities must be arrays")
    if not isinstance(profiles, dict):
        raise ManifestError("manifest Profile identities must be an object")

    agent_ids = {item.get("name") for item in agents if isinstance(item, dict)}
    skill_ids = {
        item.get("name")
        for item in core_skills + optional_skills
        if isinstance(item, dict)
    }
    profile_ids = set(profiles)
    for label, identities in (
        ("Agent", agent_ids),
        ("Skill", skill_ids),
        ("Profile", profile_ids),
    ):
        if None in identities or "" in identities:
            raise ManifestError("manifest contains an invalid {} identity".format(label))
    if len(agent_ids) != len(agents):
        raise ManifestError("manifest Agent identities must be unique")
    if len(skill_ids) != len(core_skills) + len(optional_skills):
        raise ManifestError("manifest Skill identities must be unique across core and optional assets")
    return {
        "agent": {str(item) for item in agent_ids},
        "skill": {str(item) for item in skill_ids},
        "profile": {str(item) for item in profile_ids},
    }


def _is_volume_or_token_proxy(metric: str) -> bool:
    lowered = metric.casefold().replace("_", "-")
    return (
        lowered in DIAGNOSTIC_ONLY_METRICS
        or lowered.endswith("-count")
        or "token" in lowered
        or lowered.startswith("pr-")
        or lowered.startswith("report-")
        or lowered.startswith("asset-count")
        or lowered.startswith("invocation-count")
    )


def validate_contract(contract: Mapping[str, Any], manifest: Manifest) -> Dict[str, Any]:
    if contract.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ManifestError("unsupported agent value contract schema")
    if contract.get("identity_source") != "manifest.json":
        raise ManifestError("agent value contract identity source must remain manifest.json")
    if contract.get("permission_profiles") != PERMISSION_PROFILES:
        raise ManifestError("permission profile semantics differ from the fail-closed typed policy")

    emitter = contract.get("emitter")
    if not isinstance(emitter, dict) or emitter.get("status") != "not-measured":
        raise ManifestError("agent value emitter must remain explicitly not-measured")
    if emitter.get("runtime_enabled") is not False or emitter.get("usage_evidence") != "none-claimed":
        raise ManifestError("agent value emitter must not claim runtime usage evidence")
    expected_emitter_policy = {
        "input_mode": "explicit-validated-receipts-only",
        "measured_transition": "at-least-one-valid-receipt",
        "missing_metric_policy": "explicit-not-measured-never-zero",
        "evidence_layer_policy": "never-mix-test-runtime-field",
        "api_status": "available",
        "api": "emit_measurements",
        "automatic_runtime_integration": False,
    }
    for key, expected in expected_emitter_policy.items():
        if emitter.get(key) != expected:
            raise ManifestError("agent value emitter {} policy differs from typed core".format(key))

    receipt_contract = contract.get("receipt_contract")
    if not isinstance(receipt_contract, dict):
        raise ManifestError("agent value receipt contract is invalid")
    if receipt_contract.get("measurement_schema_version") != MEASUREMENT_SCHEMA_VERSION:
        raise ManifestError("agent value measurement schema version differs from typed core")
    if receipt_contract.get("opaque_ref_fields") != [
        "receipt_id",
        "invocation_ref",
        "source_trace_ref",
        "manifest_ref",
        "evidence_refs[]",
    ]:
        raise ManifestError("agent value receipt opaque reference fields differ from typed core")
    max_age_days = receipt_contract.get("max_age_days")
    if not isinstance(max_age_days, int) or isinstance(max_age_days, bool) or not 1 <= max_age_days <= 365:
        raise ManifestError("agent value receipt max_age_days is invalid")

    authority_policy = contract.get("evidence_authority_policy")
    if not isinstance(authority_policy, dict) or authority_policy.get("managed") is not True:
        raise ManifestError("agent value evidence authority policy must be managed")
    policy_status = authority_policy.get("status")
    authorities = authority_policy.get("authorities")
    if policy_status not in ("disabled", "enabled") or not isinstance(authorities, list):
        raise ManifestError("agent value evidence authority policy is invalid")
    if policy_status == "disabled":
        if authority_policy.get("backend") != "not-configured" or authorities:
            raise ManifestError("disabled evidence authority policy must have no backend or authorities")
    else:
        if authority_policy.get("backend") == "not-configured" or not authorities:
            raise ManifestError("enabled evidence authority policy requires a managed backend and authorities")
    authority_ids = set()
    for authority in authorities:
        if not isinstance(authority, dict):
            raise ManifestError("evidence authority registry entries must be objects")
        authority_id = validate_identifier(authority.get("authority_id"), "evidence authority_id")
        if authority_id in authority_ids:
            raise ManifestError("evidence authority IDs must be unique")
        authority_ids.add(authority_id)
        layers = authority.get("allowed_layers")
        targets = authority.get("runtime_targets")
        if (
            authority.get("backend") != authority_policy.get("backend")
            or authority.get("production") is not False
            or not isinstance(layers, list)
            or not layers
            or len(layers) != len(set(layers))
            or any(layer not in ("runtime", "field") for layer in layers)
            or not isinstance(targets, list)
            or not targets
            or len(targets) != len(set(targets))
        ):
            raise ManifestError("evidence authority scope is invalid")
        for target in targets:
            validate_identifier(target, "evidence authority runtime_target")

    identities = _manifest_identity_index(manifest)
    manifest_agents = {
        str(item["name"]): item
        for item in manifest.data["agents"]
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    raw_contracts = contract.get("agent_contracts")
    if not isinstance(raw_contracts, list):
        raise ManifestError("agent_contracts must be an array")
    contract_ids = [item.get("agent_id") for item in raw_contracts if isinstance(item, dict)]
    if len(contract_ids) != len(raw_contracts) or len(contract_ids) != len(set(contract_ids)):
        raise ManifestError("agent contract IDs must be present and unique")
    if set(contract_ids) != identities["agent"]:
        missing = sorted(identities["agent"] - set(contract_ids))
        unknown = sorted(set(contract_ids) - identities["agent"])
        raise ManifestError(
            "agent contract coverage differs from manifest: missing={} unknown={}".format(missing, unknown)
        )

    suite_ids: set[str] = set()
    known_agents = identities["agent"]
    for item in raw_contracts:
        agent_id = str(item["agent_id"])
        manifest_agent = manifest_agents[agent_id]
        ceiling_name = manifest_agent.get("permission_profile")
        if ceiling_name not in PERMISSION_PROFILES:
            raise ManifestError("manifest Agent {} has an unknown permission profile".format(agent_id))
        envelope = item["permission_envelope"]
        declared_name = envelope["permission_profile"]
        if PERMISSION_PROFILES[declared_name]["rank"] > PERMISSION_PROFILES[str(ceiling_name)]["rank"]:
            raise ManifestError("Agent {} permission profile exceeds manifest ceiling".format(agent_id))
        declared_policy = PERMISSION_PROFILES[declared_name]
        ceiling_policy = PERMISSION_PROFILES[str(ceiling_name)]
        effects = set(envelope["allowed_effects"])
        tools = set(envelope["tool_capabilities"])
        if not effects.issubset(set(declared_policy["allowed_effects"])):
            raise ManifestError("Agent {} effects exceed its declared permission profile".format(agent_id))
        if not effects.issubset(set(ceiling_policy["allowed_effects"])):
            raise ManifestError("Agent {} effects exceed manifest permission ceiling".format(agent_id))
        if not tools.issubset(set(declared_policy["allowed_tool_capabilities"])):
            raise ManifestError("Agent {} tool capabilities exceed its declared permission profile".format(agent_id))
        if not tools.issubset(set(ceiling_policy["allowed_tool_capabilities"])):
            raise ManifestError("Agent {} tool capabilities exceed manifest permission ceiling".format(agent_id))

        manifest_handoffs = manifest_agent.get("handoff_to")
        if not isinstance(manifest_handoffs, list) or any(target not in known_agents for target in manifest_handoffs):
            raise ManifestError("manifest Agent {} has an invalid handoff reference".format(agent_id))
        contract_handoffs = item["handoff"]["allowed_targets"]
        if any(target not in known_agents for target in contract_handoffs):
            raise ManifestError("Agent {} contract has an invalid handoff reference".format(agent_id))
        if set(contract_handoffs) != set(manifest_handoffs):
            raise ManifestError("Agent {} handoff contract differs from manifest".format(agent_id))

        suite = item["eval_suite"]
        suite_id = suite["suite_id"]
        if suite_id in suite_ids or suite_id != "{}-value-v1".format(agent_id):
            raise ManifestError("Agent {} eval suite ID is invalid or duplicated".format(agent_id))
        suite_ids.add(suite_id)
        if tuple(suite["required_case_types"]) != REQUIRED_EVAL_CASE_TYPES:
            raise ManifestError("Agent {} eval suite does not cover all required boundaries".format(agent_id))

    lifecycle = contract.get("asset_lifecycle")
    if not isinstance(lifecycle, dict) or lifecycle.get("applies_to") != ["agent", "skill", "profile"]:
        raise ManifestError("asset lifecycle must resolve Agent, Skill and Profile identities")
    if lifecycle.get("identity_resolution") != "resolve-current-manifest-at-validation-time":
        raise ManifestError("asset lifecycle must resolve identities from the current manifest")
    if lifecycle.get("retirement_authority") != "signal-only-owner-decision-required":
        raise ManifestError("retirement signals must not authorize lifecycle mutation")

    quality = contract.get("quality_kpi_policy")
    if not isinstance(quality, dict):
        raise ManifestError("quality_kpi_policy must be an object")
    quality_kpis = quality.get("quality_kpis", [])
    diagnostics = quality.get("diagnostic_only", [])
    if any(not isinstance(item, str) for item in quality_kpis + diagnostics):
        raise ManifestError("quality and diagnostic metrics must be strings")
    if any(_is_volume_or_token_proxy(item) for item in quality_kpis):
        raise ManifestError("asset quantity, report/PR count and Token volume must not be quality KPIs")
    if set(diagnostics) != DIAGNOSTIC_ONLY_METRICS:
        raise ManifestError("diagnostic-only volume and Token metrics are incomplete")
    if set(quality_kpis).intersection(diagnostics):
        raise ManifestError("quality KPIs and diagnostic-only metrics must not overlap")

    return {
        "status": "pass",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "identity_source": "manifest.json",
        "manifest_sha256": manifest.digest,
        "agent_count": len(identities["agent"]),
        "skill_count": len(identities["skill"]),
        "profile_count": len(identities["profile"]),
        "emitter_status": "not-measured",
        "runtime_enabled": False,
        "usage_evidence": "none-claimed",
    }


def validate_receipt(
    receipt: Mapping[str, Any],
    manifest: Manifest,
    contract: Mapping[str, Any],
    schema_path: Optional[Path] = None,
    evidence_verifier: Optional[EvidenceVerifier] = None,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    validate_contract(contract, manifest)
    validate_no_secrets(receipt, "invocation receipt")
    receipt_contract = contract.get("receipt_contract")
    if not isinstance(receipt_contract, dict):
        raise ManifestError("agent value contract receipt_contract is invalid")
    if receipt_contract.get("evidence_ref_format") != "ref:<sha256>":
        raise ManifestError("agent value contract must require opaque evidence refs")
    schema_path = schema_path or manifest.root / str(receipt_contract.get("schema_path", ""))
    _validate_schema(receipt, schema_path, "asset invocation receipt")
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

    identities = _manifest_identity_index(manifest)
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


def _measured_metric(value: float, sample_size: int, unit: str) -> Dict[str, Any]:
    return {
        "status": "measured",
        "value": round(value, 6),
        "sample_size": sample_size,
        "applicable_sample_size": sample_size,
        "observed_sample_size": sample_size,
        "coverage": 1.0,
        "unit": unit,
    }


def _not_measured_metric(
    reason: str,
    applicable_sample_size: int,
    observed_sample_size: int,
) -> Dict[str, Any]:
    return {
        "status": "not-measured",
        "reason": reason,
        "applicable_sample_size": applicable_sample_size,
        "observed_sample_size": observed_sample_size,
        "coverage": (
            None
            if applicable_sample_size == 0
            else round(observed_sample_size / applicable_sample_size, 6)
        ),
    }


def _ratio_metric(
    receipts: Sequence[Mapping[str, Any]],
    predicate,
    *,
    applicable=None,
) -> Dict[str, Any]:
    selected = [item for item in receipts if applicable is None or applicable(item)]
    if not selected:
        return _not_measured_metric("no-applicable-receipts", 0, 0)
    return _measured_metric(
        sum(1 for item in selected if predicate(item)) / len(selected),
        len(selected),
        "ratio",
    )


def _optional_metric(
    receipts: Sequence[Mapping[str, Any]],
    field: str,
    unit: str,
    transform,
    *,
    applicable=None,
) -> Dict[str, Any]:
    applicable_receipts = [item for item in receipts if applicable is None or applicable(item)]
    if not applicable_receipts:
        return _not_measured_metric("no-applicable-receipts", 0, 0)
    selected = [item for item in applicable_receipts if field in item]
    if not selected:
        return _not_measured_metric("field-not-observed", len(applicable_receipts), 0)
    if len(selected) != len(applicable_receipts):
        return _not_measured_metric(
            "incomplete-coverage",
            len(applicable_receipts),
            len(selected),
        )
    return _measured_metric(
        sum(transform(item[field]) for item in selected) / len(selected),
        len(selected),
        unit,
    )


def emit_measurements(
    receipts: Sequence[Mapping[str, Any]],
    manifest: Manifest,
    contract: Mapping[str, Any],
    schema_path: Optional[Path] = None,
    evidence_verifier: Optional[EvidenceVerifier] = None,
    aggregation_window: Optional[Mapping[str, datetime]] = None,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Emit deterministic value measurements from validated receipt inputs only."""

    validate_contract(contract, manifest)
    schema_path = schema_path or manifest.root / str(
        contract["receipt_contract"]["measurement_schema_path"]
    )
    base: Dict[str, Any] = {
        "schema_version": MEASUREMENT_SCHEMA_VERSION,
        "measurement_status": "not-measured",
        "reason": "no-valid-receipts",
        "manifest_ref": opaque_ref_for_sha256(manifest.digest),
        "privacy_status": "opaque-refs-only",
        "raw_content_stored": False,
        "asset_measurements": [],
    }
    if not receipts:
        _validate_schema(base, schema_path, "asset value measurement")
        return base

    if not isinstance(aggregation_window, Mapping) or set(aggregation_window) != {"from", "through"}:
        raise ManifestError("measured aggregation requires a fixed from/through window")
    window_from = aggregation_window["from"]
    window_through = aggregation_window["through"]
    if not isinstance(window_from, datetime) or not isinstance(window_through, datetime) or not isinstance(as_of, datetime):
        raise ManifestError("aggregation window and as_of must be datetime values")
    if window_from.tzinfo is None or window_through.tzinfo is None or as_of.tzinfo is None:
        raise ManifestError("aggregation window and as_of must include timezones")
    window_from = window_from.astimezone(timezone.utc)
    window_through = window_through.astimezone(timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    if not window_from <= window_through <= as_of:
        raise ManifestError("aggregation window must satisfy from <= through <= as_of")
    if as_of > datetime.now(timezone.utc):
        raise ManifestError("aggregation as_of must not be in the future")

    seen_receipts = set()
    seen_asset_invocations = set()
    groups: Dict[Tuple[str, str, str], List[Mapping[str, Any]]] = defaultdict(list)
    validation_reports: Dict[str, Mapping[str, Any]] = {}
    for item in receipts:
        validation_report = validate_receipt(
            item,
            manifest,
            contract,
            evidence_verifier=evidence_verifier,
            as_of=as_of,
        )
        observed_at = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")).astimezone(timezone.utc)
        if observed_at < window_from or observed_at > window_through:
            raise ManifestError("receipt observed_at is outside the fixed aggregation window")
        receipt_ref = str(item["receipt_id"])
        if receipt_ref in seen_receipts:
            raise ManifestError("duplicate invocation receipt_id: {}".format(receipt_ref))
        seen_receipts.add(receipt_ref)
        validation_reports[receipt_ref] = validation_report
        observation_key = (
            str(item["asset_kind"]),
            str(item["asset_id"]),
            str(item["invocation_ref"]),
        )
        if observation_key in seen_asset_invocations:
            raise ManifestError("duplicate asset invocation observation")
        seen_asset_invocations.add(observation_key)
        groups[(str(item["asset_kind"]), str(item["asset_id"]), str(item["evidence_layer"]))].append(item)

    measurements = []
    for (asset_kind, asset_id, evidence_layer), group in sorted(groups.items()):
        metrics = {
            "task-success-rate": _ratio_metric(
                group,
                lambda item: item["outcome"] == "succeeded",
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
            "first-pass-success-rate": _optional_metric(
                group,
                "first_pass",
                "ratio",
                lambda value: 1 if value else 0,
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
            "wrong-route-rate": _ratio_metric(
                group,
                lambda item: bool(item["routing"]["wrong_route"]),
                applicable=lambda item: bool(item["routing"]["routed"]),
            ),
            "abstain-precision": _ratio_metric(
                group,
                lambda item: bool(item["abstain_correct"]),
                applicable=lambda item: bool(item["routing"]["abstained"]),
            ),
            "human-interventions-per-task": _optional_metric(
                group,
                "human_interventions",
                "count-per-task",
                lambda value: int(value),
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
            "time-to-trustworthy-change": _optional_metric(
                group,
                "time_to_trustworthy_change_ms",
                "milliseconds",
                lambda value: int(value),
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
            "escaped-defect-rate": _optional_metric(
                group,
                "escaped_defect",
                "ratio",
                lambda value: 1 if value else 0,
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
            "rollback-rate": _optional_metric(
                group,
                "rollback",
                "ratio",
                lambda value: 1 if value else 0,
                applicable=lambda item: not bool(item["routing"]["abstained"]),
            ),
        }
        measurements.append(
            {
                "asset_id": asset_id,
                "asset_kind": asset_kind,
                "evidence_layer": evidence_layer,
                "source_verification": "managed-authority-verified" if evidence_layer in ("runtime", "field") else "structural-only",
                "measurement_status": "measured",
                "receipt_refs": sorted(str(item["receipt_id"]) for item in group),
                "invocation_refs": sorted({str(item["invocation_ref"]) for item in group}),
                "source_trace_refs": sorted({str(item["source_trace_ref"]) for item in group}),
                "asset_bundle_sha256s": sorted({str(item["asset_bundle_sha256"]) for item in group}),
                "runtime_targets": sorted({str(item["runtime_target"]) for item in group}),
                "authority_ids": sorted(
                    {
                        str(item["authority_attestation"]["authority_id"])
                        for item in group
                        if isinstance(item.get("authority_attestation"), dict)
                    }
                ),
                "production_authority": all(
                    bool(validation_reports[str(item["receipt_id"])]["authority_production"])
                    for item in group
                ) if evidence_layer in ("runtime", "field") else False,
                "evidence_refs": sorted(
                    {str(ref) for item in group for ref in item["evidence_refs"]}
                ),
                "metrics": metrics,
                "retirement_signals": sorted({str(item["retirement_signal"]) for item in group}),
                "retirement_authority": "signal-only-owner-decision-required",
                "observation_window": {
                    "from": min(
                        datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")).astimezone(timezone.utc)
                        for item in group
                    ).isoformat().replace("+00:00", "Z"),
                    "through": max(
                        datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")).astimezone(timezone.utc)
                        for item in group
                    ).isoformat().replace("+00:00", "Z"),
                },
            }
        )

    report = dict(base)
    report.pop("reason")
    report["measurement_status"] = "measured"
    report["source_receipt_count"] = len(receipts)
    report["asset_measurements"] = measurements
    report["aggregation_window"] = {
        "from": window_from.isoformat().replace("+00:00", "Z"),
        "through": window_through.isoformat().replace("+00:00", "Z"),
    }
    report["as_of"] = as_of.isoformat().replace("+00:00", "Z")
    layers = {str(item["evidence_layer"]) for item in receipts}
    if len(layers) > 1:
        evidence_scope = "mixed"
    elif layers == {"test"}:
        evidence_scope = "test-only"
    elif layers == {"runtime"}:
        evidence_scope = "runtime-verified"
    else:
        evidence_scope = "field-verified"
    report["evidence_scope"] = evidence_scope
    report["quality_evidence_eligible"] = False
    report["owner_review_required"] = True
    report["lifecycle_authority"] = "none-evidence-only"
    if evidence_scope == "test-only":
        report["quality_ineligibility_reason"] = "test-only-evidence"
    elif evidence_scope == "mixed":
        report["quality_ineligibility_reason"] = "mixed-evidence-scope"
    else:
        report["quality_ineligibility_reason"] = "non-production-authority"
    validate_no_secrets(report, "asset value measurement")
    _validate_schema(report, schema_path, "asset value measurement")
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ADK Agent value contracts and invocation receipts")
    parser.add_argument("--manifest-root", type=Path, default=Path("."), help="ADK root containing manifest.json")
    parser.add_argument("--contract", type=Path, help="Agent value contract path")
    parser.add_argument("--receipt", type=Path, action="append", default=[], help="Measured invocation receipt; repeatable")
    parser.add_argument("--emit-measurements", action="store_true", help="Emit measured/not-measured aggregate")
    parser.add_argument("--summary-json", action="store_true", help="Emit compact JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    root = args.manifest_root.resolve()
    contract_path = args.contract or root / "manifests" / "agent_value_contracts.json"
    try:
        manifest = Manifest.load(root)
        contract = load_contract(contract_path)
        contract_report = validate_contract(contract, manifest)
        report: Dict[str, Any] = {"contract": contract_report}
        receipts = [
            _load_json(path, "asset invocation receipt")
            for path in args.receipt
        ]
        if receipts:
            report["receipts"] = [validate_receipt(item, manifest, contract) for item in receipts]
        if args.emit_measurements:
            if receipts:
                raise ManifestError(
                    "CLI measurement aggregation is unavailable; use a Python composition root with a fixed window/as_of"
                )
            report["measurement"] = emit_measurements(receipts, manifest, contract)
        if args.summary_json:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        else:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except ManifestError as exc:
        if args.summary_json:
            print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        else:
            print("[FAIL] {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
