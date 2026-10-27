"""Bounded, read-only hygiene checks for a single current planning state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .strict_json import StrictJSONError, read_bytes as read_bounded_bytes
from .strict_json import loads as load_strict_json


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
        if not isinstance(value, dict) or value.get("schema_version") != "adk.current-state/v1":
            reasons.append("current-state-schema-invalid")
        else:
            required = {"schema_version", "goal_ref", "milestone", "evidence_refs", "blockers", "next_actions", "history_refs"}
            if set(value) != required:
                reasons.append("current-state-fields-invalid")
            for key in ("goal_ref", "milestone"):
                if not isinstance(value.get(key), str) or not value[key].strip():
                    reasons.append("current-state-" + key.replace("_", "-") + "-missing")
            for key in ("evidence_refs", "blockers", "next_actions", "history_refs"):
                items = value.get(key)
                if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
                    reasons.append("current-state-" + key.replace("_", "-") + "-invalid")
            actions = value.get("next_actions")
            if isinstance(actions, list) and not 1 <= len(actions) <= 3:
                reasons.append("current-state-next-actions-limit")
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
