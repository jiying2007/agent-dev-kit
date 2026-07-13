"""Read-only environment readiness diagnostics."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .evaluation import runtime_plan, runtime_version
from .locking import target_lock_status
from .model import Manifest


def _command_version(command: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        return "missing"
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    value = completed.stdout.strip() or completed.stderr.strip()
    return value.splitlines()[0][:200] if completed.returncode == 0 and value else "unavailable"


def run_doctor(
    manifest: Manifest,
    required_runtimes: Sequence[str] = (),
    target: Optional[Path] = None,
) -> Dict[str, Any]:
    failures = list(manifest.validate(strict=True))
    warnings = []
    if sys.version_info < (3, 8):
        failures.append("Python 3.8 or newer is required")
    if importlib.util.find_spec("yaml") is None:
        failures.append("PyYAML is required while manifest.yaml compatibility exists")

    runtimes: Dict[str, Any] = {}
    for runtime in ("codex", "claude"):
        readiness = runtime_plan(runtime, "adk", 0)
        runtimes[runtime] = readiness
        if runtime in required_runtimes and readiness.get("status") != "planned":
            failures.append("required runtime is not ready: {}".format(runtime))
        elif readiness.get("status") != "planned":
            warnings.append("optional runtime is not ready: {}".format(runtime))
    tools = {
        "python": sys.version.split()[0],
        "codex": runtime_version("codex") or "missing",
        "claude": runtime_version("claude") or "missing",
        "hermes": _command_version("hermes"),
        "opencode": _command_version("opencode"),
        "gh": _command_version("gh"),
    }
    target_status: Optional[Dict[str, Any]] = None
    if target is not None:
        resolved = target.expanduser().resolve()
        parent = resolved if resolved.exists() else resolved.parent
        target_status = {
            "path": str(resolved),
            "parent_exists": parent.exists(),
            "parent_writable": parent.exists() and os.access(str(parent), os.W_OK),
            "lock": target_lock_status(resolved),
        }
        if not target_status["parent_exists"] or not target_status["parent_writable"]:
            failures.append("target parent is not writable: {}".format(parent))
    return {
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest,
        "root": str(manifest.root),
        "python": sys.version.split()[0],
        "runtimes": runtimes,
        "tools": tools,
        "target": target_status,
        "failures": failures,
        "warnings": warnings,
        "credential_output_policy": "status-only; tokens and environment values are never emitted",
    }
