from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from jsonschema import Draft202012Validator

from agent_dev_kit.contracts.schema_loader import packaged_schema_bytes

SCHEMA_VERSION = "adk-evidence-envelope/v1"
_SCHEMA_NAME = "evidence-envelope-v1.schema.json"
_FORBIDDEN_KEYS = {"prompt", "prompts", "messages", "raw_log", "raw-log", "raw_logs", "tool_payload", "tool-payload"}


def _schema() -> dict[str, Any]:
    value = json.loads(packaged_schema_bytes(_SCHEMA_NAME).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evidence envelope schema root must be an object")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _privacy_failures(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_KEYS:
                failures.append("forbidden raw payload key: " + "/".join((*path, key_text)))
            failures.extend(_privacy_failures(child, (*path, key_text)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_privacy_failures(child, (*path, str(index))))
    return failures


def envelope_digest(payload: dict[str, Any]) -> str:
    canonical = copy.deepcopy(payload)
    provenance = canonical.setdefault("provenance", {})
    provenance["content_sha256"] = None
    return hashlib.sha256(_canonical_bytes(canonical)).hexdigest()


def bind_evidence_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(payload)
    result.setdefault("provenance", {})["content_sha256"] = None
    result["provenance"]["content_sha256"] = envelope_digest(result)
    validation = validate_evidence_envelope(result)
    if validation["status"] != "pass":
        raise ValueError("invalid evidence envelope: " + "; ".join(validation["failures"]))
    return result


def validate_evidence_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for error in sorted(Draft202012Validator(_schema()).iter_errors(payload), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        failures.append(f"schema {location}: {error.message}")
    failures.extend(_privacy_failures(payload))
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    digest = provenance.get("content_sha256") if isinstance(provenance, dict) else None
    if isinstance(digest, str) and len(digest) == 64:
        expected = envelope_digest(payload)
        if digest != expected:
            failures.append("provenance content_sha256 does not match canonical envelope content")
    return {
        "schema": SCHEMA_VERSION,
        "status": "pass" if not failures else "fail",
        "failures": failures,
    }
