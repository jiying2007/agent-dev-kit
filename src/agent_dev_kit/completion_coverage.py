"""Static command-check coverage audit without completion authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

INPUT_SCHEMA = "adk-completion-coverage-input/v1"
RESULT_SCHEMA = "adk-completion-coverage-result/v1"
MAX_INPUT_BYTES = 1024 * 1024
MAX_CHECKS = 100
MAX_FRESHNESS_SECONDS = 365 * 24 * 60 * 60
_ID = re.compile(r"[a-z][a-z0-9-]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EVIDENCE = re.compile(r"ref:[0-9a-f]{64}\Z")
_TOP_KEYS = {
    "schema", "source_snapshot_sha256", "required_checks", "observations",
    "as_of", "freshness_seconds",
}
_EXECUTED_KEYS = {
    "id", "status", "command", "exit_code", "evidence_ref", "verified_at",
    "verifier", "source_snapshot_sha256",
}
_SKIPPED_KEYS = {"id", "status", "reason"}


class CoverageError(ValueError):
    """A coverage payload violates the closed structural contract."""


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise CoverageError(f"{label} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CoverageError(f"{label} must be a timezone-aware timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CoverageError(f"{label} must be a timezone-aware timestamp")
    return parsed.astimezone(timezone.utc)


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise CoverageError(f"{label} must be a kebab-case identifier")
    return value


def _closed(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise CoverageError(f"{label} must contain exactly the declared fields")
    return value


def _normalized_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_coverage(value: Any) -> dict[str, Any]:
    """Check structural coverage of caller-reported commands and receipts."""
    payload = _closed(value, _TOP_KEYS, "completion coverage input")
    if payload["schema"] != INPUT_SCHEMA:
        raise CoverageError("unsupported completion coverage schema")
    source = payload["source_snapshot_sha256"]
    if not isinstance(source, str) or not _SHA256.fullmatch(source):
        raise CoverageError("source_snapshot_sha256 must be exact SHA256")
    as_of = _timestamp(payload["as_of"], "as_of")
    freshness = payload["freshness_seconds"]
    if isinstance(freshness, bool) or not isinstance(freshness, int) or not 0 < freshness <= MAX_FRESHNESS_SECONDS:
        raise CoverageError("freshness_seconds is outside the supported budget")

    required_raw = payload["required_checks"]
    observed_raw = payload["observations"]
    if not isinstance(required_raw, list) or not 0 < len(required_raw) <= MAX_CHECKS:
        raise CoverageError("required_checks must contain 1-100 check IDs")
    if not isinstance(observed_raw, list) or len(observed_raw) > MAX_CHECKS:
        raise CoverageError("observations must contain at most 100 checks")
    required = [_identifier(item, "required check") for item in required_raw]
    if len(set(required)) != len(required):
        raise CoverageError("required_checks contains duplicate IDs")

    observed: dict[str, str] = {}
    stale: set[str] = set()
    failed: set[str] = set()
    skipped: set[str] = set()
    for index, raw in enumerate(observed_raw):
        if not isinstance(raw, Mapping):
            raise CoverageError(f"observation[{index}] must be an object")
        check_id = _identifier(raw.get("id"), f"observation[{index}].id")
        if check_id in observed:
            raise CoverageError(f"duplicate observation ID: {check_id}")
        status = raw.get("status")
        if status == "skipped":
            item = _closed(raw, _SKIPPED_KEYS, f"observation[{index}]")
            if not isinstance(item["reason"], str) or not item["reason"].strip():
                raise CoverageError(f"observation[{index}] skipped reason is empty")
            skipped.add(check_id)
        elif status in ("passed", "failed"):
            item = _closed(raw, _EXECUTED_KEYS, f"observation[{index}]")
            command = item["command"]
            if not isinstance(command, str) or not command.strip() or len(command) > 4096:
                raise CoverageError(f"observation[{index}] command is missing or oversized")
            exit_code = item["exit_code"]
            if isinstance(exit_code, bool) or not isinstance(exit_code, int):
                raise CoverageError(f"observation[{index}] exit_code must be an integer")
            if (status == "passed" and exit_code != 0) or (status == "failed" and exit_code == 0):
                raise CoverageError(f"observation[{index}] status and exit_code disagree")
            evidence_ref = item["evidence_ref"]
            if not isinstance(evidence_ref, str) or not _EVIDENCE.fullmatch(evidence_ref):
                raise CoverageError(f"observation[{index}] evidence_ref must be ref:<sha256>")
            if not isinstance(item["verifier"], str) or not item["verifier"].strip():
                raise CoverageError(f"observation[{index}] verifier declaration is empty")
            if item["source_snapshot_sha256"] != source:
                raise CoverageError(f"observation[{index}] source snapshot differs")
            verified_at = _timestamp(item["verified_at"], f"observation[{index}].verified_at")
            age = (as_of - verified_at).total_seconds()
            if age < 0:
                raise CoverageError(f"observation[{index}] verified_at is after as_of")
            if age > freshness:
                stale.add(check_id)
            if status == "failed":
                failed.add(check_id)
        else:
            raise CoverageError(f"observation[{index}] has unsupported status")
        observed[check_id] = str(status)

    required_set = set(required)
    missing = required_set - set(observed)
    skipped_required = skipped & required_set
    covered = {
        check_id for check_id in required_set
        if observed.get(check_id) == "passed" and check_id not in stale
    }
    needs_fix = bool(missing or failed or stale or skipped_required)
    return {
        "schema": RESULT_SCHEMA,
        "status": "needs-fix" if needs_fix else "pass",
        "source_snapshot_sha256": source,
        "normalized_input_sha256": _normalized_digest(payload),
        "as_of_utc": as_of.isoformat().replace("+00:00", "Z"),
        "required_checks": sorted(required_set),
        "observed_checks": sorted(observed),
        "covered_required": sorted(covered),
        "missing_required": sorted(missing),
        "failed_checks": sorted(failed),
        "skipped_required": sorted(skipped_required),
        "skipped_additional": sorted(skipped - required_set),
        "stale_checks": sorted(stale),
        "additional_checks": sorted(set(observed) - required_set),
        "counts": {
            "required": len(required_set),
            "covered_required": len(covered),
            "missing_required": len(missing),
            "failed": len(failed),
            "skipped_required": len(skipped_required),
            "stale": len(stale),
        },
        "evidence_authenticated": False,
        "verifier_authenticated": False,
        "command_executed_by_auditor": False,
        "completion_allowed": False,
        "release_authorized": False,
    }


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise CoverageError("JSON object contains duplicate fields")
        result[key] = item
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit command-check coverage without completion authority")
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        path = Path(args.input)
        if path.is_symlink() or not path.is_file():
            raise CoverageError("input must be a regular non-symlink file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise CoverageError("input exceeds byte budget")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
        result = audit_coverage(value)
    except (OSError, UnicodeError, json.JSONDecodeError, CoverageError) as exc:
        result = {"schema": RESULT_SCHEMA, "status": "invalid", "error": str(exc), "completion_allowed": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=args.summary_json, indent=None if args.summary_json else 2))
    return 0 if result["status"] == "pass" else 1 if result["status"] == "needs-fix" else 2


if __name__ == "__main__":
    raise SystemExit(main())
