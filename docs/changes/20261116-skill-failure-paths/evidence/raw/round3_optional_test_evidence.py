"""Record real optional Skill regression commands and controlled fixture evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest


BASE = Path("/workspace/scratch/fe5385ca063a")
ROOT = BASE / "agent-dev-kit"
RTK = str(BASE / "verification-tools/rtk")
SOURCES = (
    "optional-skills/adk-security-supply-chain/SKILL.md",
    "optional-skills/adk-security-supply-chain/references/skill-scan-coverage.md",
    "optional-skills/adk-test-flakiness-triage/SKILL.md",
    "optional-skills/adk-test-flakiness-triage/references/details.md",
    "docs/runbooks/security-supply-chain.md",
    "tests/test_skill_command_examples.py",
)
sys.path.insert(0, str(ROOT))
from tests import test_skill_command_examples as examples


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity():
    return {path: {"bytes": len((ROOT / path).read_bytes()),
                   "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
            for path in SOURCES}


phase = sys.argv[1]
output = BASE / f"round3-optional-{phase}.json"
if output.exists():
    raise SystemExit(f"refusing to overwrite existing evidence: {output}")
started_at = utc()
started = time.monotonic()
before = identity()
observations = []
current_test = None
original = examples.run_example


def recorded_example(code, root, *arguments, **options):
    observed_at = utc()
    observed = time.monotonic()
    result = original(code, root, *arguments, **options)
    fixtures = []
    for path in sorted(root.rglob("*")):
        item = {"path": str(path.relative_to(root))}
        if path.is_dir():
            item["type"] = "directory"
        elif path.is_file():
            data = path.read_bytes()
            item.update(type="file", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            if path.suffix in {".tsv", ".log", ".json"}:
                item["content"] = data.decode("utf-8")
        else:
            item["type"] = "other"
        fixtures.append(item)
    observations.append({"test": current_test, "command": result.args, "cwd": str(root),
                         "started_at_utc": observed_at, "ended_at_utc": utc(),
                         "duration_seconds": time.monotonic() - observed,
                         "stdout": result.stdout, "stderr": result.stderr,
                         "exit_code": result.returncode, "fixtures_after": fixtures})
    return result


class RecordingResult(unittest.TextTestResult):
    def startTest(self, test):
        global current_test
        current_test = test.id()
        super().startTest(test)


examples.run_example = recorded_example
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                           for cls in (examples.SecurityScanExampleTests,
                                       examples.FlakySampleExampleTests))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(suite)
after = identity()
identity_unchanged = before == after
exit_code = int(not result.wasSuccessful() or not identity_unchanged)
record = {
    "schema": "round3-optional-regression-evidence/v1",
    "phase": phase,
    "invocation": [RTK, "python3", str(Path(__file__).resolve()), phase],
    "started_at_utc": started_at,
    "ended_at_utc": utc(),
    "duration_seconds": time.monotonic() - started,
    "python": sys.version,
    "source_before": before,
    "source_after": after,
    "source_unchanged_during_tests": identity_unchanged,
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "stdout": "",
    "stderr": stream.getvalue(),
    "exit_code": exit_code,
    "observations": observations,
    "boundary": "Synthetic file contents and owned child processes only; no real credentials, "
                "external requests, parent-shell signal delivery, process-group cancellation "
                "or keyboard Ctrl-C propagation are exercised.",
}
with output.open("x") as handle:
    json.dump(record, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(stream.getvalue(), end="")
print(json.dumps({"evidence": str(output), "exit_code": exit_code,
                  "observations": len(observations), "source_unchanged": identity_unchanged},
                 ensure_ascii=False))
raise SystemExit(exit_code)
