"""Run the existing owners affected by the reviewed implicit-context correction."""
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
QUALITY = Path("/workspace/scratch/fe8de3b42084/verification-tools/adk-quality-venv/bin")
COMMANDS = {
    "trigger-matrix": [sys.executable, "-B", "-m", "unittest", "tests.test_skill_trigger_matrix", "-v"],
    "routing-ir": [sys.executable, "-B", "-m", "unittest", "tests.test_routing_ir_contract", "-v"],
    "match-boundary": ["bash", "tests/test_boundary_conditions_match.sh"],
    "match-effectiveness": ["bash", "tests/test_match_effectiveness.sh"],
    "module-budget": ["bash", "tests/test_module_size_budget.sh"],
    "ruff": [str(QUALITY / "ruff"), "check", "src/agent_dev_kit/_matcher_kernel.py",
             "tests/test_skill_trigger_matrix.py"],
    "mypy": [str(QUALITY / "mypy"), "--no-incremental", "src/agent_dev_kit/_matcher_kernel.py"],
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
    return {"name": name, "exit_code": result.returncode, "tail": result.stdout[-1800:]}


if __name__ == "__main__":
    selected = sys.argv[1:] or list(COMMANDS)
    if any(name not in COMMANDS for name in selected):
        raise SystemExit("choose a known gate: " + ", ".join(COMMANDS))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, selected))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(int(any(item["exit_code"] for item in results)))
