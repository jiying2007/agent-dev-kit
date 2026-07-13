"""Portable single-writer locks for export and installation targets."""

from __future__ import annotations

import json
import os
import shutil
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .model import ManifestError


LOCK_SCHEMA = "adk-target-lock/v1"
LOCK_METADATA = "owner.json"
DEFAULT_STALE_SECONDS = 3600


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ManifestError("target lock has an invalid created_at") from exc
    return parsed.timestamp()


def lock_path_for(target: Path) -> Path:
    target = target.expanduser().resolve()
    name = target.name or "root"
    return target.parent / (".{}.adk-writer-lock".format(name))


def _read_metadata(lock_path: Path) -> Dict[str, Any]:
    if lock_path.is_symlink():
        raise ManifestError("target lock path must not be a symlink: {}".format(lock_path))
    metadata_path = lock_path / LOCK_METADATA
    if not metadata_path.is_file() or metadata_path.is_symlink():
        raise ManifestError("target lock metadata is missing or unsafe: {}".format(metadata_path))
    try:
        value = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("target lock metadata is invalid: {}".format(metadata_path)) from exc
    if not isinstance(value, dict) or value.get("schema") != LOCK_SCHEMA:
        raise ManifestError("unsupported target lock metadata")
    for field in ("lock_id", "target", "operation", "host", "pid", "created_at"):
        if field not in value:
            raise ManifestError("target lock metadata is missing {}".format(field))
    return value


def target_lock_status(target: Path, stale_seconds: int = DEFAULT_STALE_SECONDS) -> Dict[str, Any]:
    target = target.expanduser().resolve()
    lock_path = lock_path_for(target)
    if not lock_path.exists() and not lock_path.is_symlink():
        return {
            "schema_version": 1,
            "status": "unlocked",
            "target": str(target),
            "lock_path": str(lock_path),
        }
    metadata = _read_metadata(lock_path)
    if metadata.get("target") != str(target):
        raise ManifestError("target lock metadata does not match requested target")
    age_seconds = max(0, int(time.time() - _parse_time(str(metadata["created_at"]))))
    owner_alive: Optional[bool] = None
    if metadata.get("host") == socket.gethostname():
        try:
            os.kill(int(metadata["pid"]), 0)
        except (OSError, ValueError):
            owner_alive = False
        else:
            owner_alive = True
    return {
        "schema_version": 1,
        "status": "locked",
        "target": str(target),
        "lock_path": str(lock_path),
        "lock_id": metadata["lock_id"],
        "operation": metadata["operation"],
        "host": metadata["host"],
        "pid": metadata["pid"],
        "created_at": metadata["created_at"],
        "age_seconds": age_seconds,
        "owner_alive": owner_alive,
        "stale": age_seconds >= stale_seconds and owner_alive is not True,
    }


def clear_target_lock(target: Path, expected_lock_id: str) -> Dict[str, Any]:
    if not expected_lock_id:
        raise ManifestError("--expected-lock-id is required")
    target = target.expanduser().resolve()
    lock_path = lock_path_for(target)
    status = target_lock_status(target)
    if status.get("status") != "locked":
        raise ManifestError("target is not locked")
    if status.get("lock_id") != expected_lock_id:
        raise ManifestError("target lock ID does not match; refusing clear")
    if status.get("owner_alive") is True:
        raise ManifestError("target lock owner is still active; refusing clear")
    if status.get("owner_alive") is None and status.get("stale") is not True:
        raise ManifestError("remote target lock is not stale; refusing clear")
    metadata = _read_metadata(lock_path)
    if metadata.get("lock_id") != expected_lock_id:
        raise ManifestError("target lock changed while clearing; refusing clear")
    shutil.rmtree(str(lock_path))
    return {
        "schema_version": 1,
        "status": "cleared",
        "target": str(target),
        "lock_id": expected_lock_id,
    }


class TargetLock:
    """Fail-closed target lock with optional bounded waiting."""

    def __init__(self, target: Path, operation: str, timeout_seconds: float = 0.0) -> None:
        if not operation or len(operation) > 80:
            raise ManifestError("target lock operation must be 1-80 characters")
        if timeout_seconds < 0 or timeout_seconds > 300:
            raise ManifestError("target lock timeout must be between 0 and 300 seconds")
        self.target = target.expanduser().resolve()
        self.operation = operation
        self.timeout_seconds = float(timeout_seconds)
        self.path = lock_path_for(self.target)
        self.lock_id = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> Dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                self.path.mkdir(mode=0o700)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    try:
                        status = target_lock_status(self.target)
                        detail = "{} operation={} lock_id={}".format(
                            status["status"], status.get("operation", "unknown"), status.get("lock_id", "unknown")
                        )
                    except ManifestError as exc:
                        detail = str(exc)
                    raise ManifestError("target is locked; {}".format(detail))
                time.sleep(0.05)

        metadata = {
            "schema": LOCK_SCHEMA,
            "lock_id": self.lock_id,
            "target": str(self.target),
            "operation": self.operation,
            "host": socket.gethostname(),
            "pid": os.getpid(),
            "created_at": _utc_now(),
        }
        metadata_path = self.path / LOCK_METADATA
        temp_path = self.path / (LOCK_METADATA + ".tmp")
        try:
            temp_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(str(temp_path), str(metadata_path))
        except Exception:
            shutil.rmtree(str(self.path), ignore_errors=True)
            raise
        self.acquired = True
        return metadata

    def release(self) -> None:
        if not self.acquired:
            return
        metadata = _read_metadata(self.path)
        if metadata.get("lock_id") != self.lock_id:
            raise ManifestError("target lock ownership changed; refusing release")
        shutil.rmtree(str(self.path))
        self.acquired = False

    def __enter__(self) -> "TargetLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.release()
