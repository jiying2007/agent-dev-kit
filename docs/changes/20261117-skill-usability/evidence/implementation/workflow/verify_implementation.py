"""Replay T3b's existing gate owners and preserve their raw output outside the repo."""
from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
COMMANDS = {
    "skill-content-gate": ["bash", "tests/test_skill_content.sh"],
    "intent-boundary-gate": ["bash", "tests/test_intent_boundary_governance.sh"],
    "trigger-matrix": [sys.executable, "-B", "-m", "unittest", "tests.test_skill_trigger_matrix", "-v"],
    "t3b-ruff": ["/workspace/scratch/fe8de3b42084/verification-tools/adk-quality-venv/bin/ruff",
                 "check", "src/agent_dev_kit/intent_boundary.py",
                 "tests/test_task_package_delivery.py", "tests/test_skill_trigger_matrix.py"],
}


def run(name: str) -> dict[str, object]:
    command = [RTK, "bypass", *COMMANDS[name]]
    run_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(command, cwd=ROOT, env=run_env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (OUT / f"{name}.txt").write_text(result.stdout, encoding="utf-8")
    record = {"command": command, "cwd": str(ROOT), "exit_code": result.returncode,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(), "output": result.stdout}
    (OUT / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"name": name, "exit_code": result.returncode, "tail": result.stdout[-1600:]}


if __name__ == "__main__":
    selected = sys.argv[1:] or list(COMMANDS)
    if any(name not in COMMANDS for name in selected):
        raise SystemExit("choose a known gate: " + ", ".join(COMMANDS))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, selected))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(int(any(item["exit_code"] for item in results)))
