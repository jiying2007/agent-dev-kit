"""Record real local integration gates, without model or device execution."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
toolchain = Path(os.environ.get("ADK_VERIFY_TOOLCHAIN", str(root / ".venv")))
env["PATH"] = str(toolchain / "bin") + os.pathsep + env["PATH"]
env["PYTHONPATH"] = str(root / "src")
python = str(toolchain / "bin/python")
stages = [
    ("final-ruff", ["ruff", "check", "src", "tools", "tests/fixtures/fake_target_runtime.py"]),
    ("final-format", ["bash", "scripts/check-format.sh"]),
    ("strict", ["bash", "scripts/devkit.sh", "validate", "--strict"]),
    ("release-check", ["bash", "scripts/devkit.sh", "release", "check", "--summary-json"]),
    ("benchmark", [python, str(out / "benchmark_fixed.py"), str(root),
                   str(out / "benchmark-candidate60.json"), "--tasks",
                   "tests/fixtures/software_m5_eval_tasks.jsonl"]),
    ("full-regression", ["bash", "tests/run_all.sh", "--timing-json", str(out / "full-timing.json")]),
]
subprocess.run([python, str(out / "snapshot_sources.py"), str(root), str(out / "sources-final-before.json")],
               cwd=root, env=env, check=True)
rows = []
for name, command in stages:
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    print("START " + name + " " + started, flush=True)
    log = out / (name + ".log")
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    row = {"name": name, "command": command, "started_at": started,
           "completed_at": datetime.now(timezone.utc).isoformat(),
           "elapsed_seconds": time.perf_counter() - clock, "exit_code": result.returncode,
           "log": log.name}
    rows.append(row)
    print(json.dumps(row), flush=True)
    print("\n".join(log.read_text(errors="replace").splitlines()[-5:]), flush=True)
    (out / "integration-results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(result.returncode)
subprocess.run([python, str(out / "snapshot_sources.py"), str(root), str(out / "sources-final-after.json")],
               cwd=root, env=env, check=True)
before = json.loads((out / "sources-final-before.json").read_text())
after = json.loads((out / "sources-final-after.json").read_text())
changes = sorted(name for name in before["files"].keys() | after["files"].keys()
                 if before["files"].get(name) != after["files"].get(name))
summary = {"status": "pass" if not changes else "source-drift", "stages": rows,
           "compared_source_files": before["file_count"], "changed_sources": changes,
           "evidence_completed_at": datetime.now(timezone.utc).isoformat()}
(out / "integration-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: summary[key] for key in ("status", "compared_source_files", "changed_sources")}), flush=True)
raise SystemExit(bool(changes))
