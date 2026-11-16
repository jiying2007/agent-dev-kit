"""Keep actual commands, streams, timestamps and input identities for this task."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path("/workspace/scratch/fe5385ca063a/agent-dev-kit")
RTK = "/workspace/scratch/fe5385ca063a/verification-tools/rtk"
EVIDENCE = ROOT.parent / "round3-core-runs"


def snapshot():
    paths = sorted(set(
        list((ROOT / "skills/adk-interface-contract-design").rglob("*"))
        + list((ROOT / "skills/adk-parallel-agent-governance").rglob("*"))
        + [ROOT / "tests/test_skill_contract_methods.py",
           ROOT / "manifests/profile_context_ratchets.json"]
        + list((ROOT / "docs/changes/20261116-skill-failure-paths").glob("*.md"))))
    result = []
    for path in paths:
        if not path.is_file():
            continue
        data = path.read_bytes()
        result.append({"path": str(path.relative_to(ROOT)), "bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest(),
                       "git_blob_sha1": hashlib.sha1(
                           b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()})
    return result


def main():
    label, *command = sys.argv[1:]
    if not command:
        raise SystemExit("a command is required")
    EVIDENCE.mkdir(exist_ok=True)
    target = EVIDENCE / (label + ".json")
    if target.exists():
        raise SystemExit("refusing to overwrite an earlier observation: " + str(target))
    argv = [RTK, "run", *command]
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    before = snapshot()
    head = subprocess.run([RTK, "run", "git", "rev-parse", "HEAD"], cwd=ROOT,
                          text=True, capture_output=True, check=True).stdout.strip()
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, env=environment,
                            capture_output=True, text=True, timeout=120)
    finished_at = datetime.now(timezone.utc).isoformat()
    after = snapshot()
    record = {"label": label, "command_argv": argv, "cwd": str(ROOT),
              "environment_overrides": {"PYTHONPATH": environment["PYTHONPATH"]},
              "head": head, "started_at_utc": started_at, "finished_at_utc": finished_at,
              "duration_seconds": time.monotonic() - started,
              "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
              "python": platform.python_version(),
              "jsonschema": importlib.metadata.version("jsonschema"),
              "source_before": before, "source_after": after,
              "source_unchanged_during_command": before == after}
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"label": label, "receipt": str(target), "exit_code": result.returncode,
                      "started_at_utc": started_at, "finished_at_utc": finished_at,
                      "stdout": result.stdout, "stderr": result.stderr}, ensure_ascii=False, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
