"""Scratch evidence runner; not an ADK runtime or consumer-compliance test."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import unittest

parser = argparse.ArgumentParser()
parser.add_argument("stage", choices=("baseline", "repaired"))
args = parser.parse_args()
root = Path(__file__).resolve().parent / "agent-dev-kit"
sys.path.insert(0, str(root))
from tests.test_skill_cmake_methods import CmakeBuildIdentityMethodsTests

def artifact(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

sources = [artifact(root / path) for path in (
    "skills/adk-cmake-cross-build/SKILL.md", "tests/test_skill_cmake_methods.py",
    "tests/test_skill_command_examples.py")]
versions = {"python": platform.python_version()}
for name in ("cmake", "ctest", "ninja", "cc", "rtk"):
    tool = shutil.which(name)
    run = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=10)
    versions[name] = {"path": tool, "exit_code": run.returncode,
                      "stdout": run.stdout, "stderr": run.stderr}
suite = unittest.defaultTestLoader.loadTestsFromTestCase(CmakeBuildIdentityMethodsTests)
cases = list(suite)
stream = io.StringIO()
started = time.monotonic()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
evidence = {
    "stage": args.stage,
    "kind": "published-command-real-host-identity-controls",
    "sources": sources,
    "tools": versions,
    "argv": sys.argv,
    "path": os.environ["PATH"],
    "duration_seconds": time.monotonic() - started,
    "tests_run": result.testsRun,
    "successful": result.wasSuccessful(),
    "skipped": len(result.skipped),
    "test_output": stream.getvalue(),
    "cases": [{"id": case.id(), "records": getattr(case, "records", [])} for case in cases],
    "limits": [
        "These real host controls pass with both old and repaired prose; no model RED/GREEN claim.",
        "Host compiler and CMake/Ninja only; no target ABI, hardware, runtime discovery or SDK guard proof.",
        "A separate new-consumer task is required to assess use of the revised method.",
    ],
}
output = root.parent / f"round3-cmake-test-{args.stage}.json"
output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
print(stream.getvalue(), end="")
print(json.dumps({"evidence": str(output), "successful": result.wasSuccessful(),
                  "tests_run": result.testsRun, "skipped": len(result.skipped)}))
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
