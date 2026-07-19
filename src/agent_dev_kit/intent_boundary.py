"""Deterministic validators for invocation-era work-item and prototype contracts."""

from __future__ import annotations

import re
from datetime import date
from pathlib import PurePosixPath
from typing import Any, List, Mapping, Optional, Tuple


TASK_PACKAGE_SCHEMA = "adk-task-package-schema-v2"
PROTOTYPE_EVIDENCE_SCHEMA = "adk-prototype-evidence-schema-v1"

TASK_REQUIRED_FIELDS: Tuple[str, ...] = (
    "structured_output_schema",
    "strict_schema_decision",
    "refusal_handling",
    "goal",
    "context",
    "constraints",
    "done_when",
    "primary_action",
    "action_mode",
    "verification",
    "artifacts",
    "blockers",
    "work_item_kind",
    "question_to_resolve",
    "evidence_required",
    "implementation_permission",
    "exit_gate",
    "handoff_target",
    "retention_decision",
)

WORK_ITEM_RULES = {
    "decision": ("forbidden", "owner-decision"),
    "research": ("forbidden", "evidence-reviewed"),
    "prototype": ("forbidden", "prototype-reviewed"),
    "implementation": ("approved", "implementation-verified"),
}

RETENTION_DECISIONS = {
    "keep-final",
    "archive-negative-result",
    "delete-orphan",
    "expire",
}

PROTOTYPE_REQUIRED_FIELDS: Tuple[str, ...] = (
    "structured_output_schema",
    "question",
    "base_commit",
    "scope",
    "artifact_path",
    "artifact_sha256",
    "runtime_assumptions",
    "observed_result",
    "decision_supported",
    "verification_command",
    "verification_exit_code",
    "retention_decision",
    "expires_at",
    "cleanup_owner",
    "rollback_anchor",
    "active_references_absent",
)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_non_empty_string(item) for item in value)


def _non_empty_string_list(value: Any) -> bool:
    return _string_list(value) and bool(value)


def _shape_errors(value: Mapping[str, Any], required: Tuple[str, ...]) -> List[str]:
    errors: List[str] = []
    missing = [field for field in required if field not in value]
    unexpected = sorted(set(value).difference(required))
    if missing:
        errors.append("missing fields: {}".format(",".join(missing)))
    if unexpected:
        errors.append("unexpected fields: {}".format(",".join(unexpected)))
    return errors


def validate_task_package(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, dict):
        return ("task package must be an object",)
    errors = _shape_errors(value, TASK_REQUIRED_FIELDS)
    if errors:
        return tuple(errors)
    if value["structured_output_schema"] != TASK_PACKAGE_SCHEMA:
        errors.append("structured_output_schema must be {}".format(TASK_PACKAGE_SCHEMA))
    if value["strict_schema_decision"] is not True:
        errors.append("strict_schema_decision must be true")
    for field in ("goal", "context", "primary_action", "action_mode", "question_to_resolve", "handoff_target", "refusal_handling"):
        if not _non_empty_string(value[field]):
            errors.append("{} must be a non-empty string".format(field))
    for field in ("constraints", "blockers"):
        if not _string_list(value[field]):
            errors.append("{} must be an array of non-empty strings".format(field))
    for field in ("done_when", "verification", "artifacts", "evidence_required"):
        if not _non_empty_string_list(value[field]):
            errors.append("{} must be a non-empty array of non-empty strings".format(field))
    kind = value["work_item_kind"]
    if kind not in WORK_ITEM_RULES:
        errors.append("work_item_kind is invalid")
    else:
        expected_permission, expected_gate = WORK_ITEM_RULES[kind]
        if value["implementation_permission"] != expected_permission:
            errors.append("{} requires implementation_permission={}".format(kind, expected_permission))
        if value["exit_gate"] != expected_gate:
            errors.append("{} requires exit_gate={}".format(kind, expected_gate))
        prototype_refs = [
            item.partition(":")[2]
            for item in value["artifacts"]
            if item.startswith("prototype_evidence:")
        ]
        if kind == "prototype" and not any(_non_empty_string(item) for item in prototype_refs):
            errors.append("prototype requires a prototype_evidence artifact")
    if value["retention_decision"] not in RETENTION_DECISIONS:
        errors.append("retention_decision is invalid")
    return tuple(errors)


def validate_prototype_evidence(value: Any, as_of: Optional[date] = None) -> Tuple[str, ...]:
    if not isinstance(value, dict):
        return ("prototype evidence must be an object",)
    errors = _shape_errors(value, PROTOTYPE_REQUIRED_FIELDS)
    if errors:
        return tuple(errors)
    if value["structured_output_schema"] != PROTOTYPE_EVIDENCE_SCHEMA:
        errors.append("structured_output_schema must be {}".format(PROTOTYPE_EVIDENCE_SCHEMA))
    for field in (
        "question",
        "base_commit",
        "scope",
        "artifact_path",
        "runtime_assumptions",
        "observed_result",
        "cleanup_owner",
        "verification_command",
        "rollback_anchor",
    ):
        if not _non_empty_string(value[field]):
            errors.append("{} must be a non-empty string".format(field))
    base_commit = value["base_commit"]
    if not isinstance(base_commit, str) or re.fullmatch(r"[0-9a-f]{7,64}", base_commit) is None:
        errors.append("base_commit must be a 7-64 character lowercase hex revision")
    artifact_path = value["artifact_path"]
    if _non_empty_string(artifact_path):
        path = PurePosixPath(artifact_path)
        if (
            path.is_absolute()
            or "\\" in artifact_path
            or ":" in artifact_path
            or any(part in ("..", ".git") for part in path.parts)
        ):
            errors.append("artifact_path must be a repository-relative path outside .git")
    if not isinstance(value["decision_supported"], bool):
        errors.append("decision_supported must be boolean")
    verification_exit_code = value["verification_exit_code"]
    if (
        not isinstance(verification_exit_code, int)
        or isinstance(verification_exit_code, bool)
        or not 0 <= verification_exit_code <= 255
    ):
        errors.append("verification_exit_code must be an integer from 0 to 255")
    if not isinstance(value["active_references_absent"], bool):
        errors.append("active_references_absent must be boolean")
    digest = value["artifact_sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("artifact_sha256 must be 64 lowercase hex characters")
    retention = value["retention_decision"]
    if retention not in RETENTION_DECISIONS:
        errors.append("retention_decision is invalid")
    elif retention == "delete-orphan" and value["active_references_absent"] is not True:
        errors.append("delete-orphan requires active_references_absent=true")
    try:
        expires_at = date.fromisoformat(str(value["expires_at"]))
    except ValueError:
        errors.append("expires_at must be an ISO date")
    else:
        if retention == "expire" and as_of is not None and expires_at <= as_of:
            errors.append("expire requires a future expires_at")
    return tuple(errors)
