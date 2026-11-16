"""Record actual targeted test runs for the PR 275 CI parser follow-up."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import unittest


AREA = Path("/workspace/scratch/fe5385ca063a")
ROOT = AREA / "agent-dev-kit"
RECEIPT = AREA / "round2-ci-parser-fix.json"
RTK = str(AREA / "verification-tools/rtk")
TEST_FILE = ROOT / "tests/test_skill_bisect_methods.py"
CI_LOG = AREA / "round2-pr-first-regression.log"
sys.path.insert(0, str(ROOT))


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def identity(path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {"path": str(path), "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest()}


phase, *targets = sys.argv[1:]
if not targets:
    raise SystemExit("At least one unittest target is required")
record = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else {
    "schema": "round2-ci-parser-fix/v1",
    "base_source_sha": "bc2f4b2ca3bbef2cb5515322048a144639e79004",
    "ci": {"run_id": 43812320483, "job_id": 133116507717,
           "url": "https://github.com/jiying2007/agent-dev-kit/actions/runs/43812320483/job/133116507717",
           "observed_git_version": "2.56.1", "raw_log": identity(CI_LOG)},
    "local_git_2_56_1_executed": False,
    "full_regression": "not-run-by-this-worker; main PR owner will run on the new head",
    "historical_lesson_search": {
        "command": "rtk run rg -n -i 'bisect|git|解析|CI|引号|portable' knowledge/L2-domain/lessons.md",
        "exit": 2, "result": "knowledge/L2-domain/lessons.md does not exist",
    },
    "runs": [],
}
source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
git_version = subprocess.check_output(["git", "--version"], cwd=ROOT, text=True).strip()
command_argv = [RTK, "run", "env", "PYTHONPATH=src", "PYTHONDONTWRITEBYTECODE=1",
                sys.executable, "-B", str(Path(__file__).resolve()), phase, *targets]
run = {"phase": phase, "command": shlex.join(command_argv), "argv": command_argv,
       "cwd": str(ROOT), "source_sha": source_sha, "test_source": identity(TEST_FILE),
       "python": sys.version, "git_version": git_version, "started_at": timestamp()}
module = importlib.import_module("tests.test_skill_bisect_methods")
stream = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromNames(targets)
result = unittest.TextTestRunner(verbosity=2, stream=stream).run(suite)
run.update({"finished_at": timestamp(), "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors),
            "exit": 0 if result.wasSuccessful() else 1, "output": stream.getvalue(),
            "actual_command_receipts": module.RECEIPTS,
            "test_source_after": identity(TEST_FILE)})
record["runs"].append(run)
RECEIPT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(stream.getvalue(), end="")
print(json.dumps({"receipt": str(RECEIPT), "phase": phase,
                  "started_at": run["started_at"], "finished_at": run["finished_at"],
                  "source_sha": source_sha, "test_sha256": run["test_source"]["sha256"],
                  "git_version": git_version, "tests_run": result.testsRun,
                  "failures": len(result.failures), "errors": len(result.errors)}, ensure_ascii=False))
raise SystemExit(run["exit"])
