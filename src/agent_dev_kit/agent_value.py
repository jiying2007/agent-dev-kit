"""Emit Agent Value measurements from validated contract and receipt inputs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import agent_value_contracts as value_contracts
from . import agent_value_receipts as value_receipts
from .model import Manifest, ManifestError
from .privacy_ref import opaque_ref_for_sha256, validate_no_secrets


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
    evidence_verifier: Optional[value_contracts.EvidenceVerifier] = None,
    aggregation_window: Optional[Mapping[str, datetime]] = None,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Emit deterministic value measurements from validated receipt inputs only."""

    value_contracts.validate_contract(contract, manifest)
    schema_path = schema_path or manifest.root / str(
        contract["receipt_contract"]["measurement_schema_path"]
    )
    base: Dict[str, Any] = {
        "schema_version": value_contracts.MEASUREMENT_SCHEMA_VERSION,
        "measurement_status": "not-measured",
        "reason": "no-valid-receipts",
        "manifest_ref": opaque_ref_for_sha256(manifest.digest),
        "privacy_status": "opaque-refs-only",
        "raw_content_stored": False,
        "asset_measurements": [],
    }
    if not receipts:
        value_contracts._validate_schema(base, schema_path, "asset value measurement")
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
        validation_report = value_receipts.validate_receipt(
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
    value_contracts._validate_schema(report, schema_path, "asset value measurement")
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
        contract = value_contracts.load_contract(contract_path)
        contract_report = value_contracts.validate_contract(contract, manifest)
        report: Dict[str, Any] = {"contract": contract_report}
        receipts = [
            value_contracts._load_json(path, "asset invocation receipt")
            for path in args.receipt
        ]
        if receipts:
            report["receipts"] = [value_receipts.validate_receipt(item, manifest, contract) for item in receipts]
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
