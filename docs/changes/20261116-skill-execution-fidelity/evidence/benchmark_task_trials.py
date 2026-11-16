"""Measure deterministic local evaluation overhead, without running a model."""
import cProfile
from datetime import datetime, timezone
import json
from pathlib import Path
import pstats
import statistics
import subprocess
import sys
import time

from test_task_trials import synthetic_task_trials
from test_task_evidence import MANIFEST
from agent_dev_kit.task_trials import compare_task_trials

phase = sys.argv[1]
root = Path(__file__).resolve().parent
package = root / "benchmark-fixed-population"
synthetic_task_trials(package)
started_at = datetime.now(timezone.utc).isoformat()
samples = []
profiles = []
for _ in range(3):
    started = time.perf_counter()
    result = compare_task_trials(package / "task-trials.json", MANIFEST)
    samples.append(time.perf_counter() - started)
for index in range(3):
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    result = compare_task_trials(package / "task-trials.json", MANIFEST)
    profiler.disable()
    elapsed = time.perf_counter() - started
    profile_path = root / f"task-trials-{phase}-{index}.pstats"
    profiler.dump_stats(profile_path)
    selected = []
    for (path, line, name), (primitive, calls, own, cumulative, _) in pstats.Stats(profiler).stats.items():
        if name in {"load_contract", "check_schema", "read_task_evidence", "_read_task_evidence"}:
            selected.append({"file": path, "line": line, "function": name, "calls": calls,
                             "self_seconds": own, "cumulative_seconds": cumulative})
    profiles.append({"wall_seconds": elapsed, "profile": str(profile_path), "selected": selected})
record = {"synthetic": True, "phase": phase, "started_at": started_at,
          "finished_at": datetime.now(timezone.utc).isoformat(),
          "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=MANIFEST.root, text=True).strip(),
          "runs": result["comparison"]["run_count"], "verdict": result["verdict"],
          "samples_seconds": samples, "median_seconds": statistics.median(samples), "profiles": profiles,
          "model_calls_executed": 0, "limitations": "local synthetic comparison overhead; no model, Token, device or production metric"}
(root / f"performance-{phase}.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
