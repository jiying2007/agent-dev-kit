"""Record required source checks without changing test or qualification policy."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root, out = (Path(item).resolve() for item in sys.argv[1:3])
mode, expected = sys.argv[3:5]
out.mkdir(parents=True, exist_ok=True)
rtk = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
tool_bin = Path("/workspace/scratch/d417066aafa8/agent-dev-kit/.venv/bin")
env = dict(os.environ)
env["PATH"] = str(tool_bin) + os.pathsep + env["PATH"]
env["ADK_PYTHON_BIN"] = str(tool_bin / "python")
env["PYTHONPATH"] = str(root / "src") if mode == "adk" else str(root)

def git(*args: str) -> str:
    return subprocess.check_output([rtk, "proxy", "git", *args], cwd=root, text=True).strip()

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def snapshot() -> dict:
    names = git("ls-files", "-z").split("\0")
    rows = {}
    for name in names:
        path = root / name
        if name and not name.startswith(("docs/changes/", "reports/", "evals/results/")) and path.is_file():
            raw = path.read_bytes()
            rows[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "tracked_status": git("status", "--porcelain", "--untracked-files=no"), "files": rows}

before = snapshot()
if before["head"] != expected or before["tracked_status"]:
    raise SystemExit("candidate must be the expected clean tracked commit")
(out / "source-before.json").write_text(json.dumps(before, indent=2) + "\n")
stages = []
if mode == "adk":
    stages += [
        ("ruff", ["ruff", "check", "src", "tools", "tests/fixtures/fake_target_runtime.py"]),
        ("focused-ruff", ["ruff", "check", "src/agent_dev_kit/execution_policy", "--select", "E4,E7,E9,F,B,UP,SIM,I"]),
        ("mypy", ["mypy", "src/agent_dev_kit/contracts", "src/agent_dev_kit/evidence", "src/agent_dev_kit/target_adapters", "src/agent_dev_kit/distribution", "src/agent_dev_kit/execution_policy", "src/agent_dev_kit/versioning.py", "src/agent_dev_kit/installation_inventory.py", "src/agent_dev_kit/installation_plan.py", "src/agent_dev_kit/installation_transaction.py", "src/agent_dev_kit/targets.py", "src/agent_dev_kit/target_contracts.py", "src/agent_dev_kit/delivery_cli.py", "src/agent_dev_kit/release.py", "src/agent_dev_kit/native_campaign_diagnostics.py", "src/agent_dev_kit/review_evidence.py", "src/agent_dev_kit/task_evidence.py", "src/agent_dev_kit/task_trials.py", "src/agent_dev_kit/task_acceptance.py"]),
        ("format", ["bash", "scripts/check-format.sh"]),
        ("strict", ["bash", "scripts/devkit.sh", "validate", "--strict"]),
        ("release-check", ["bash", "scripts/devkit.sh", "release", "check", "--summary-json"]),
        ("export", ["bash", "scripts/devkit.sh", "export", "--target", "claude-code", "--profile", "core", "--out", str(out / "export"), "--clean"]),
    ]
elif mode != "root":
    raise SystemExit("mode must be adk or root")
stages.append(("full-regression", ["bash", "tests/run_all.sh", "--timing-json", str(out / "full-timing.json")]))
results = []
for name, command in stages:
    row = {"name": name, "command": [rtk, "proxy", *command], "started_at": now()}
    print(json.dumps({"status": "running", **row}), flush=True)
    start = time.monotonic()
    log = out / (name + ".log")
    with log.open("wb") as stream:
        result = subprocess.run(row["command"], cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    row.update(completed_at=now(), elapsed_seconds=time.monotonic() - start,
               exit_code=result.returncode, log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    results.append(row)
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(row), flush=True)
    print("\n".join(log.read_text(errors="replace").splitlines()[-4:]), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
after = snapshot()
(out / "source-after.json").write_text(json.dumps(after, indent=2) + "\n")
changed = [name for name in before["files"].keys() | after["files"].keys() if before["files"].get(name) != after["files"].get(name)]
valid = not changed and before["head"] == after["head"] and not after["tracked_status"]
summary = {"status": "pass" if valid else "source-drift", "mode": mode, "head": expected,
           "tree": before["tree"], "source_file_count": len(before["files"]), "changed_sources": sorted(changed),
           "stages": results, "evidence_completed_at": now()}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({key: summary[key] for key in ("status", "head", "tree", "source_file_count", "changed_sources")}), flush=True)
raise SystemExit(not valid)
