"""Compose one privacy-bounded test run into linked Trace and value evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from jsonschema import Draft202012Validator, FormatChecker

from .agent_value import emit_measurements, validate_receipt
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import opaque_ref_for_sha256, validate_no_secrets, validate_opaque_ref
from .trace_summary import (
    OutcomeFact,
    TraceRunFacts,
    emit_trace_summary_v2,
    validate_trace_summary,
)


COMPOSITION_SCHEMA = "adk-run-evidence-composition/v1"
DEFAULT_SCHEMA_PACKAGE = "agent_dev_kit.schema_resources"
DEFAULT_SCHEMA_NAME = "run-evidence-composition-v1.schema.json"


@dataclass(frozen=True)
class TestAssetObservation:
    asset_kind: str
    asset_id: str


@dataclass(frozen=True)
class RunEvidenceObservation:
    trace_facts: TraceRunFacts
    observed_at: datetime
    assets: Tuple[TestAssetObservation, ...] = ()
    aggregation_from: Optional[datetime] = None
    aggregation_through: Optional[datetime] = None
    as_of: Optional[datetime] = None


def load_run_evidence_schema(path: Optional[Path] = None) -> Mapping[str, Any]:
    try:
        raw = (
            path.read_text(encoding="utf-8")
            if path is not None
            else resources.read_text(DEFAULT_SCHEMA_PACKAGE, DEFAULT_SCHEMA_NAME, encoding="utf-8")
        )
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("run evidence composition schema is invalid") from exc
    if not isinstance(value, dict):
        raise ManifestError("run evidence composition schema must be an object")
    Draft202012Validator.check_schema(value)
    return value


def _iso(value: datetime, label: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ManifestError("{} must be a timezone-aware datetime".format(label))
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ManifestError("{} must be an RFC3339 timestamp".format(label))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("{} must be an RFC3339 timestamp".format(label)) from exc
    if parsed.tzinfo is None:
        raise ManifestError("{} must include a timezone".format(label))
    return parsed.astimezone(timezone.utc)


def _trace_ref(summary: Mapping[str, Any]) -> str:
    return opaque_ref_for_sha256(sha256_bytes(canonical_json_bytes(summary)))


def _invocation_ref(trace_ref: str, asset: TestAssetObservation) -> str:
    digest = sha256_bytes(canonical_json_bytes({
        "trace_ref": trace_ref,
        "asset_kind": asset.asset_kind,
        "asset_id": asset.asset_id,
    }))
    return opaque_ref_for_sha256(digest)


def _receipt(
    summary: Mapping[str, Any],
    trace_ref: str,
    asset: TestAssetObservation,
    manifest: Manifest,
    observed_at: datetime,
) -> Mapping[str, Any]:
    outcome = summary["outcome"]
    if outcome.get("status") == "not-available":
        raise ManifestError("asset receipt requires an observed trace outcome")
    abstained = bool(summary["abstained"])
    if abstained:
        raise ManifestError("test composition cannot infer whether an abstention was correct")
    body = {
        "schema_version": "adk-asset-invocation-receipt/v1",
        "invocation_ref": _invocation_ref(trace_ref, asset),
        "source_trace_ref": trace_ref,
        "manifest_ref": opaque_ref_for_sha256(manifest.digest),
        "asset_bundle_sha256": summary["asset_bundle_sha256"],
        "runtime_target": summary["runtime_target"],
        "evidence_layer": "test",
        "observed_at": _iso(observed_at, "observed_at"),
        "measurement_status": "measured",
        "asset_id": asset.asset_id,
        "asset_kind": asset.asset_kind,
        "routing": {
            "routed": not abstained,
            "abstained": abstained,
            "wrong_route": bool(summary["wrong_skill"]),
        },
        "outcome": outcome["status"],
        "human_interventions": summary["human_interventions"],
        "retirement_signal": "insufficient-evidence",
        "evidence_refs": sorted({
            trace_ref,
            *(
                item["evidence_ref"]
                for item in summary["verification"]
                if item["evidence_ref"] is not None
            ),
        }),
        "privacy_status": summary["privacy_status"],
        "raw_content_stored": False,
    }
    body["first_pass"] = bool(summary["first_pass_success"])
    receipt = dict(body)
    receipt["receipt_id"] = opaque_ref_for_sha256(sha256_bytes(canonical_json_bytes(body)))
    return receipt


def _validate_wrapper_schema(value: Mapping[str, Any], schema_path: Optional[Path]) -> None:
    errors = sorted(
        Draft202012Validator(
            load_run_evidence_schema(schema_path), format_checker=FormatChecker()
        ).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ManifestError(
            "run_evidence_invalid: {}: {}".format(location, errors[0].message)
        )


def validate_run_evidence(
    value: Mapping[str, Any],
    manifest: Manifest,
    agent_value_contract: Mapping[str, Any],
    schema_path: Optional[Path] = None,
) -> Mapping[str, Any]:
    validate_no_secrets(value, "run evidence composition")
    _validate_wrapper_schema(value, schema_path)
    summary = validate_trace_summary(value["trace_summary"])
    expected_trace_ref = _trace_ref(summary)
    validate_opaque_ref(value["trace_ref"], "run evidence trace_ref")
    if value["trace_ref"] != expected_trace_ref:
        raise ManifestError("run evidence trace_ref does not bind trace_summary")
    receipts = value["receipts"]
    observed_at = _datetime(value["observed_at"], "run evidence observed_at")
    if observed_at > datetime.now(timezone.utc):
        raise ManifestError("run evidence observed_at must not be in the future")
    as_of = _datetime(value["as_of"], "run evidence as_of") if receipts else None
    seen_assets = set()
    for receipt in receipts:
        validate_receipt(receipt, manifest, agent_value_contract, as_of=as_of)
        identity = (receipt["asset_kind"], receipt["asset_id"])
        if identity in seen_assets:
            raise ManifestError("run evidence contains a duplicate asset observation")
        seen_assets.add(identity)
        if (
            receipt["evidence_layer"] != "test"
            or receipt["source_trace_ref"] != expected_trace_ref
            or receipt["asset_bundle_sha256"] != summary["asset_bundle_sha256"]
            or receipt["runtime_target"] != summary["runtime_target"]
        ):
            raise ManifestError("run evidence receipt binding differs from trace_summary")
        expected_asset = TestAssetObservation(receipt["asset_kind"], receipt["asset_id"])
        if receipt["invocation_ref"] != _invocation_ref(expected_trace_ref, expected_asset):
            raise ManifestError("run evidence invocation_ref differs from trace and asset identity")
        expected_evidence_refs = sorted({
            expected_trace_ref,
            *(
                item["evidence_ref"]
                for item in summary["verification"]
                if item["evidence_ref"] is not None
            ),
        })
        if receipt["evidence_refs"] != expected_evidence_refs:
            raise ManifestError("run evidence receipt evidence_refs differ from trace evidence")
        if (
            receipt["observed_at"] != _iso(observed_at, "observed_at")
            or receipt["routing"] != {
                "routed": True,
                "abstained": False,
                "wrong_route": bool(summary["wrong_skill"]),
            }
            or receipt["outcome"] != summary["outcome"]["status"]
            or receipt["human_interventions"] != summary["human_interventions"]
            or receipt.get("first_pass") != bool(summary["first_pass_success"])
            or receipt["retirement_signal"] != "insufficient-evidence"
            or receipt["privacy_status"] != summary["privacy_status"]
            or any(field in receipt for field in (
                "abstain_correct", "time_to_trustworthy_change_ms", "escaped_defect",
                "rollback", "authority_attestation",
            ))
        ):
            raise ManifestError("run evidence receipt semantics differ from trace projection")
    if not receipts:
        if value["measurement"] is not None or any(
            value[field] is not None for field in ("aggregation_window", "as_of")
        ):
            raise ManifestError("trace-only composition must not contain measurement state")
        return value
    if summary["outcome"]["status"] == "not-available":
        raise ManifestError("unavailable trace outcome cannot produce asset receipts")
    window = value["aggregation_window"]
    expected_measurement = emit_measurements(
        receipts,
        manifest,
        agent_value_contract,
        aggregation_window={
            "from": _datetime(window["from"], "aggregation_window.from"),
            "through": _datetime(window["through"], "aggregation_window.through"),
        },
        as_of=as_of,
    )
    if value["measurement"] != expected_measurement:
        raise ManifestError("run evidence measurement differs from receipt recomputation")
    if (
        expected_measurement["evidence_scope"] != "test-only"
        or expected_measurement["quality_evidence_eligible"] is not False
        or expected_measurement["owner_review_required"] is not True
        or expected_measurement["lifecycle_authority"] != "none-evidence-only"
    ):
        raise ManifestError("run evidence measurement exceeds test-only authority")
    return value


def emit_run_evidence(
    observation: RunEvidenceObservation,
    manifest: Manifest,
    agent_value_contract: Mapping[str, Any],
    schema_path: Optional[Path] = None,
) -> Mapping[str, Any]:
    if not isinstance(observation, RunEvidenceObservation):
        raise ManifestError("run evidence observation must be typed")
    if not isinstance(observation.trace_facts, TraceRunFacts):
        raise ManifestError("run evidence trace_facts must be TraceRunFacts")
    if not isinstance(observation.assets, tuple) or any(
        not isinstance(item, TestAssetObservation) for item in observation.assets
    ):
        raise ManifestError("run evidence assets must be typed observations")
    summary = emit_trace_summary_v2(observation.trace_facts)
    trace_ref = _trace_ref(summary)
    assets = observation.assets
    identities = [(item.asset_kind, item.asset_id) for item in assets]
    if len(identities) != len(set(identities)):
        raise ManifestError("run evidence contains duplicate asset observations")
    if assets and not isinstance(observation.trace_facts.outcome, OutcomeFact):
        raise ManifestError("asset observations require an explicitly observed outcome")
    receipts = [
        _receipt(summary, trace_ref, item, manifest, observation.observed_at)
        for item in assets
    ]
    if receipts:
        if any(
            value is None
            for value in (
                observation.aggregation_from,
                observation.aggregation_through,
                observation.as_of,
            )
        ):
            raise ManifestError("asset observations require aggregation window and as_of")
        window = {
            "from": observation.aggregation_from,
            "through": observation.aggregation_through,
        }
        measurement = emit_measurements(
            receipts,
            manifest,
            agent_value_contract,
            aggregation_window=window,
            as_of=observation.as_of,
        )
        aggregation_window = {
            "from": _iso(observation.aggregation_from, "aggregation_from"),
            "through": _iso(observation.aggregation_through, "aggregation_through"),
        }
        as_of_value = _iso(observation.as_of, "as_of")
    else:
        measurement = None
        aggregation_window = None
        as_of_value = None
    value = {
        "schema_version": COMPOSITION_SCHEMA,
        "trace_ref": trace_ref,
        "trace_summary": summary,
        "observed_at": _iso(observation.observed_at, "observed_at"),
        "receipts": receipts,
        "measurement": measurement,
        "aggregation_window": aggregation_window,
        "as_of": as_of_value,
        "raw_content_stored": False,
    }
    return validate_run_evidence(value, manifest, agent_value_contract, schema_path)
