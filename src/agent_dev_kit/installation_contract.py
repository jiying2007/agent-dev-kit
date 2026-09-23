"""Shared installation plan and receipt contract primitives."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from .model import ManifestError, canonical_json_bytes, sha256_bytes

PLAN_SCHEMA = "adk-install-plan/v2"
RECEIPT_SCHEMA = "adk-install-receipt/v3"
RECEIPT_NAME = ".adk-install-receipt.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _expand_target(value: str) -> Path:
    if not value.strip():
        raise ManifestError("target path must be a non-empty string")
    expanded = os.path.expanduser(value)
    if "$" in expanded or "`" in expanded or "\x00" in expanded:
        raise ManifestError("dynamic target paths are forbidden: {}".format(value))
    return Path(expanded).resolve()


def _receipt_digest(data: Mapping[str, Any]) -> str:
    content = dict(data)
    content.pop("receipt_sha256", None)
    return sha256_bytes(canonical_json_bytes(content))


def _read_receipt(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink():
        raise ManifestError("{} must not be a symlink: {}".format(label, path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid JSON: {}".format(label, path)) from exc
    if not isinstance(data, dict):
        raise ManifestError("{} must be a JSON object".format(label))
    if data.get("schema") != RECEIPT_SCHEMA:
        raise ManifestError(
            "unsupported {} schema: expected {}".format(label, RECEIPT_SCHEMA)
        )
    stored_digest = data.get("receipt_sha256")
    if not isinstance(stored_digest, str) or stored_digest != _receipt_digest(data):
        raise ManifestError("{} digest does not match content".format(label))
    return data


def _load_receipt(target: Path) -> Optional[Mapping[str, Any]]:
    path = target / RECEIPT_NAME
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise ManifestError("existing install receipt must be a regular file: {}".format(path))
    return _read_receipt(path, "existing install receipt")
