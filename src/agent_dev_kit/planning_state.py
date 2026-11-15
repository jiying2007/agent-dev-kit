"""Bounded, read-only hygiene checks for a single current planning state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .strict_json import StrictJSONError, read_bytes as read_bounded_bytes
from .strict_json import loads as load_strict_json


def valid_work_in_progress(work: Any) -> bool:
    """Validate the optional frontier extension without granting completion."""
    allowed = {"ref", "status", "prior_verified_checkpoint", "replan", "qualification"}
    return (isinstance(work, dict) and bool(work) and not set(work) - allowed
            and all(isinstance(v, str) and bool(v.strip())
                    for k, v in work.items() if k != "prior_verified_checkpoint")
            and ("prior_verified_checkpoint" not in work
                 or (type(work["prior_verified_checkpoint"]) is int
                     and work["prior_verified_checkpoint"] >= 0)))


def current_state_field_issues(value: Any) -> list[tuple[str, str]]:
    """Share field constraints; callers retain their public diagnostic formats."""
    if not isinstance(value, dict):
        return [("schema", "invalid")]
    issues = []
    if value.get("schema_version") != "adk.current-state/v1":
        issues.append(("schema", "invalid"))
    required = {"schema_version", "goal_ref", "milestone", "evidence_refs", "blockers", "next_actions", "history_refs"}
    if not required <= set(value) or set(value) - required - {"work_in_progress"}:
        issues.append(("fields", "invalid"))
    if "work_in_progress" in value and not valid_work_in_progress(value["work_in_progress"]):
        issues.append(("work_in_progress", "invalid"))
    for key in ("goal_ref", "milestone"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            issues.append((key, "missing"))
    limits = (("evidence_refs", 0, 8), ("blockers", 0, 8),
              ("next_actions", 1, 3), ("history_refs", 0, 3))
    for key, _, _ in limits:
        items = value.get(key)
        if (not isinstance(items, list)
                or any(not isinstance(item, str) or not item.strip() for item in items)
                or len(set(items)) != len(items)):
            issues.append((key, "invalid"))
    for key, minimum, maximum in limits:
        items = value.get(key)
        if isinstance(items, list) and not minimum <= len(items) <= maximum:
            issues.append((key, "limit"))
    return issues


def _reject_symlink_path(path: Path) -> None:
    """Fail closed on symlinked components, including parents (preflight only)."""
    current = path
    while True:
        if current.is_symlink():
            raise StrictJSONError("current-state path contains symlink")
        if current.parent == current:
            return
        current = current.parent


def check_current_state(path: Path, *, max_bytes: int = 8192) -> dict[str, Any]:
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= 1024 * 1024:
        raise ValueError("max_bytes must be between 1 and 1048576")
    reasons: list[str] = []
    raw: bytes | None
    try:
        _reject_symlink_path(path)
        raw = read_bounded_bytes(path, max_bytes=max_bytes, regular_only=True)
    except StrictJSONError as exc:
        raw = None
        reasons.append(
            "current-state-byte-limit" if str(exc) == "JSON exceeds byte budget"
            else "current-state-input-invalid"
        )
    if raw is not None:
        try:
            value = load_strict_json(raw, max_bytes=max_bytes)
        except (ValueError, UnicodeError):
            value = None
        issues = current_state_field_issues(value)
        if ("schema", "invalid") in issues:
            reasons.append("current-state-schema-invalid")
        else:
            for key, kind in issues:
                if kind == "limit" and key != "next_actions":
                    kind = "invalid"
                reason = "current-state-" + key.replace("_", "-") + "-" + kind
                if reason not in reasons:
                    reasons.append(reason)
    return {
        "schema_version": "adk.current-state-check/v1",
        "status": "fail" if reasons else "pass",
        "read_only": True,
        "completion_allowed": False,
        "evidence_contents_verified": False,
        "max_bytes": max_bytes,
        "state_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
        "reasons": reasons,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh goal state-check")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=8192)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check_current_state(args.state, max_bytes=args.max_bytes)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "pass" else 1
