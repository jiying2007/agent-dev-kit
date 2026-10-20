"""Bounded metadata for failed hosted campaigns; never qualification evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import ManifestError
from .native_campaign_contract import (
    EVIDENCE_SCHEMA,
    FINALIZE_SCHEMA,
    MAX_JSON_BYTES,
    STAGES,
    _validate_schema,
)
from .strict_json import StrictJSONError, loads, read_bytes

SCHEMA = "adk-native-hosted-campaign-diagnostics/v1"
MAX_DIAGNOSTIC_BYTES = 64 * 1024
PHASES = (
    "source", "python", "node", "cosign", "runtime", "credentials",
    "authenticate", "inputs", "prepare", "run", "finalize", "sign",
    "loader", "package", "upload",
)
# No directory enumeration: private inputs, receipts and signatures are excluded.
INPUTS = (
    ("plan.json", "plan", "prepare"),
    ("prepare-summary.json", "prepare", "prepare"),
    ("evidence.json", "evidence", "run"),
    ("run-summary.json", "run", "run"),
    ("finalize-summary.json", "finalize", "finalize"),
    ("production-loader.json", "loader", "loader"),
)
SAFE_REASONS = frozenset({
    "runtime-version-probe-failed", "previous-stage-failed",
    "runtime-exit-nonzero", "semantic-assertion-failed",
    "native_campaign_output_budget_exceeded",
})
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_NUMERIC_FIELDS = ("exit_code", "duration_ms", "stdout_bytes", "stderr_bytes")
_HASH_FIELDS = (
    "command_sha256", "result_sha256", "stdout_sha256", "stderr_sha256",
    "assertion_sha256", "assertion_result_sha256", "bundle_sha256",
    "candidate_contract_normalized_sha256", "binary_sha256",
    "cwd_sha256", "environment_sha256", "runtime_binary_sha256",
    "receipt_sha256", "contract_sha256",
)


class DiagnosticsError(ValueError):
    """A fixed, non-sensitive diagnostic rejection code."""


def _directory(path: Path, *, missing_leaf: bool = False) -> Path:
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise DiagnosticsError("unsafe-directory")
    for component in (*reversed(absolute.parents), absolute):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            if component == absolute and missing_leaf:
                continue
            raise DiagnosticsError("directory-unavailable") from None
        if not stat.S_ISDIR(mode):
            raise DiagnosticsError("unsafe-directory")
    return absolute


def _workflow_phases(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(PHASES):
        raise DiagnosticsError("invalid-workflow-phases")
    normalized: dict[str, str] = {}
    for phase in PHASES:
        outcome = value[phase]
        if not isinstance(outcome, str) or outcome not in {
            "success", "failure", "cancelled", "skipped", "",
        }:
            raise DiagnosticsError("invalid-workflow-outcome")
        normalized[phase] = "not-run" if outcome in {"skipped", ""} else outcome
    if any(normalized[key] != "success" for key in ("source", "python", "runtime")):
        raise DiagnosticsError("trusted-prerequisites-not-complete")
    if "failure" not in normalized.values():
        raise DiagnosticsError("no-failed-workflow-phase")
    return normalized


def _projection(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in _HASH_FIELDS:
        if key in value:
            item = value[key]
            if not isinstance(item, str) or _HASH.fullmatch(item) is None:
                raise DiagnosticsError("invalid-observation-digest")
            result[key] = item
    for key in _NUMERIC_FIELDS:
        if key in value:
            item = value[key]
            lower = -(2 ** 31) if key == "exit_code" else 0
            if type(item) is not int or not lower <= item <= 2 ** 63 - 1:
                raise DiagnosticsError("invalid-observation-number")
            result[key] = item
    return result


def _reason(value: Mapping[str, Any]) -> str:
    candidate = value.get("reason")
    if isinstance(candidate, str) and candidate in SAFE_REASONS:
        return candidate
    return "detail-withheld"


def _campaign_projection(root: Path, value: Mapping[str, Any], kind: str) -> dict[str, Any]:
    schema = "plan" if kind == "plan" else "evidence"
    _validate_schema(
        value, root / "schemas" / f"native-target-campaign-{schema}-v2.schema.json",
        "diagnostic input",
    )
    # Plan command/assertion digests are maps, while evidence stage digests
    # are scalars. Only the fixed root-level scalar identities belong here.
    result = _projection({
        key: value[key] for key in ("bundle_sha256", "candidate_contract_normalized_sha256")
    })
    result["runtime"] = _projection(value["runtime"])
    result["operation_status"] = value["status"]
    if kind == "plan":
        return result
    result["version_probe"] = _projection(value["version_probe"])
    if "reason" in value:
        result["reason_code"] = _reason(value)
    stages: list[dict[str, Any]] = []
    for index, stage in enumerate(value["stages"]):
        if stage["stage"] != STAGES[index]:
            raise DiagnosticsError("ambiguous-native-stage-order")
        projected = _projection(stage)
        projected.update({
            "stage": stage["stage"], "status": stage["status"],
            "semantic_assertion_status": stage["semantic_assertion_status"],
        })
        if "reason" in stage:
            projected["reason_code"] = _reason(stage)
        if "environment" in stage:
            projected["environment"] = _projection(stage["environment"])
        stages.append(projected)
    result["stages"] = stages
    return result


def _summary_projection(value: Mapping[str, Any], kind: str) -> dict[str, Any]:
    error_keys = {"schema", "status", "error", "release_authorized"}
    if kind in {"prepare", "run", "finalize"} and value.get("schema") == (
        "adk-native-target-campaign-error/v1"
    ):
        if (set(value) != error_keys or value["status"] != "fail"
                or value["release_authorized"] is not False
                or not isinstance(value["error"], str)):
            raise DiagnosticsError("invalid-operation-summary")
        return {"operation_status": "fail", "reason_code": "operation-error-detail-withheld"}
    if kind == "loader":
        if (set(value) != {"status", "target", "digest"}
                or value["status"] != "pass" or value["target"] != "claude-code"
                or not isinstance(value["digest"], str)
                or _HASH.fullmatch(value["digest"]) is None):
            raise DiagnosticsError("invalid-loader-summary")
        return {"operation_status": "pass", "contract_sha256": value["digest"]}
    if kind == "prepare":
        keys = {
            "schema", "status", "campaign_id", "plan", "candidate_contract",
            "candidate_contract_normalized_sha256", "release_authorized",
        }
        expected_schema = "adk-native-target-campaign-operation/v1"
        expected_status = "ready"
    elif kind == "finalize":
        keys = {
            "schema", "status", "campaign_id", "target", "receipt_id", "receipt_path",
            "receipt_sha256", "contract_sha256", "bundle_sha256", "next_required_evidence",
            "lifecycle_authority", "release_authorized",
        }
        expected_schema = FINALIZE_SCHEMA
        expected_status = "ready-for-signature-and-registry"
        if (value.get("lifecycle_authority") != "none-candidate-only"
                or value.get("next_required_evidence") != [
                    "sigstore-or-reviewed-external-signature-bundle",
                    "managed-trust-registry-receipt-binding",
                    "production-loader-verification",
                    "owner-reviewed-target-contract-promotion",
                ]):
            raise DiagnosticsError("invalid-operation-summary")
    else:
        raise DiagnosticsError("invalid-operation-summary")
    if (set(value) != keys or value.get("schema") != expected_schema
            or value.get("status") != expected_status
            or value.get("release_authorized") is not False):
        raise DiagnosticsError("invalid-operation-summary")
    for key in keys - {"release_authorized", "next_required_evidence"}:
        if not isinstance(value[key], str):
            raise DiagnosticsError("invalid-operation-summary")
    result = _projection(value)
    result["operation_status"] = expected_status
    return result


def _inspect(root: Path, path: Path, kind: str, outcome: str) -> dict[str, Any]:
    record: dict[str, Any] = {"status": "missing"}
    try:
        info = path.lstat()
    except FileNotFoundError:
        return record
    record["status"] = "rejected"
    if not stat.S_ISREG(info.st_mode):
        record["reason_code"] = "unsafe-input-file"
        return record
    if outcome == "not-run":
        record["reason_code"] = "unexpected-file-for-not-run-phase"
        return record
    if info.st_size > MAX_JSON_BYTES:
        record["reason_code"] = "input-over-byte-budget"
        return record
    try:
        raw = read_bytes(path, max_bytes=MAX_JSON_BYTES, regular_only=True)
        record.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        value = loads(raw, max_bytes=MAX_JSON_BYTES)
    except StrictJSONError:
        record["reason_code"] = "unsafe-or-invalid-json"
        return record
    if not isinstance(value, dict):
        record["reason_code"] = "invalid-json-object"
        return record
    try:
        if kind in {"plan", "evidence"} or (
            kind == "run" and value.get("schema") == EVIDENCE_SCHEMA
        ):
            projected = _campaign_projection(root, value, kind)
        else:
            projected = _summary_projection(value, kind)
    except ManifestError:
        record["reason_code"] = "schema-rejected"
        return record
    except DiagnosticsError as exc:
        record["reason_code"] = str(exc)
        return record
    record.update({"status": "accepted-metadata-only", "observation": projected})
    return record


def collect_diagnostics(
    root: Path, campaign_dir: Path, output_dir: Path, *, source_sha: str,
    run_id: str, run_attempt: str, phases: Mapping[str, Any],
) -> dict[str, Any]:
    """Retain only validated projections; do not invoke or qualify a campaign."""
    if re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise DiagnosticsError("invalid-source-sha")
    if any(re.fullmatch(r"[1-9][0-9]{0,19}", item) is None for item in (run_id, run_attempt)):
        raise DiagnosticsError("invalid-run-identity")
    outcomes = _workflow_phases(phases)
    root = _directory(root)
    campaign_dir = _directory(campaign_dir, missing_leaf=True)
    output_dir = _directory(output_dir, missing_leaf=True)
    if output_dir.exists():
        raise DiagnosticsError("output-directory-must-be-new")
    records = {
        name: _inspect(root, campaign_dir / name, kind, outcomes[phase])
        for name, kind, phase in INPUTS
    }
    missing_status = "not-run" if outcomes["run"] == "not-run" else "evidence-unavailable"
    native_stages = [{"stage": stage, "status": missing_status} for stage in STAGES]
    # evidence.json is the canonical observation file, not a redirected summary.
    evidence = records["evidence.json"].get("observation")
    if isinstance(evidence, dict):
        observed = {item["stage"]: item for item in evidence.get("stages", [])}
        native_stages = [
            observed.get(stage, {"stage": stage, "status": missing_status}) for stage in STAGES
        ]
    successful = [phase for phase in PHASES if outcomes[phase] == "success"]
    result: dict[str, Any] = {
        "schema": SCHEMA, "status": "failed-campaign-diagnostics",
        "source_sha": source_sha, "run_id": run_id, "run_attempt": run_attempt,
        "workflow_conclusion": "failure",
        "workflow_phases": [{"phase": phase, "outcome": outcomes[phase]} for phase in PHASES],
        "last_successful_phase": successful[-1] if successful else None,
        "failed_phases": [phase for phase in PHASES if outcomes[phase] == "failure"],
        "native_stages": native_stages, "files": records,
        "contains_raw_commands": False, "contains_raw_assertion_text": False,
        "contains_raw_output": False, "contains_provider_secret": False,
        "target_promotion_performed": False, "registry_promotion_performed": False,
        "lifecycle_authority": "none-diagnostics-only", "release_authorized": False,
    }
    payload = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(payload) > MAX_DIAGNOSTIC_BYTES:
        raise DiagnosticsError("diagnostic-over-byte-budget")
    output_dir.mkdir(mode=0o700)
    descriptor = os.open(output_dir / "diagnostics.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    for name in ("campaign-dir", "output-dir", "source-sha", "run-id", "run-attempt", "phases-json"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        phases = loads(args.phases_json, max_bytes=4096, max_depth=4)
        result = collect_diagnostics(
            Path(args.root), Path(args.campaign_dir), Path(args.output_dir),
            source_sha=args.source_sha, run_id=args.run_id, run_attempt=args.run_attempt,
            phases=phases,
        )
    except (DiagnosticsError, StrictJSONError, OSError) as exc:
        reason = str(exc) if isinstance(exc, DiagnosticsError) else "diagnostic-input-or-io-error"
        print(json.dumps({"schema": SCHEMA, "status": "not-collected", "reason_code": reason,
                          "release_authorized": False}, sort_keys=True))
        return 2
    print(json.dumps({"schema": SCHEMA, "status": result["status"],
                      "release_authorized": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
