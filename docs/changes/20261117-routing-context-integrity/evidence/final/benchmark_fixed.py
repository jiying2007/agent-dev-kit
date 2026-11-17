"""Observe unchanged ADK deterministic work; never dispatch a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--tasks", required=True)
args = parser.parse_args()
root = args.root.resolve()
sys.path.insert(0, str(root / "src"))
from agent_dev_kit.model import Manifest
from agent_dev_kit.evaluation_runtime import load_tasks, run_deterministic
from agent_dev_kit.phase_context import resolve_phase_context
from agent_dev_kit.skill_relationships import resolve_delivery_lifecycle

manifest = Manifest.load(root)
task_path = root / args.tasks
tasks = load_tasks(task_path)
reports = []
for index in range(3):
    start = time.perf_counter()
    routing = run_deterministic(manifest, tasks)
    for _ in range(10):
        resolve_phase_context(manifest, "general", "review")
        resolve_phase_context(manifest, "general", "verify")
        resolve_delivery_lifecycle(manifest)
    reports.append({"round": index + 1, "seconds": time.perf_counter() - start,
                    "routing": routing})
result = {
    "scope": "local-deterministic-tool-overhead-only",
    "python": platform.python_version(),
    "tasks_sha256": hashlib.sha256(task_path.read_bytes()).hexdigest(),
    "task_count": len(tasks), "phase_resolutions_per_round": 20,
    "lifecycle_resolutions_per_round": 10,
    "median_seconds": statistics.median(row["seconds"] for row in reports),
    "rounds": reports,
    "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((root / "src/agent_dev_kit").glob("*.py"))},
    "provider_tokens_measured": False, "provider_cost_measured": False,
}
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: result[key] for key in ("scope", "task_count", "median_seconds")}, indent=2))
