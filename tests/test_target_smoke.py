"""Behavioral budgets for the public caller-supplied target smoke."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import run_target_smoke


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Manifest.load(ROOT)
OUTPUT_LIMIT = 1024 * 1024
PRIVATE_OUTPUT = "private-smoke-output-must-not-appear-in-evidence"


class TargetSmokeBudgetTest(unittest.TestCase):
    def smoke(self, code: str, timeout: int = 5) -> dict:
        return run_target_smoke(
            MANIFEST, "claude-code", "discovery", [sys.executable, "-c", code],
            profile="core", timeout_seconds=timeout,
        )

    def assert_private(self, result: dict) -> None:
        self.assertEqual(result["certification"], "caller-supplied-smoke")
        self.assertNotIn(PRIVATE_OUTPUT, json.dumps(result))
        self.assertNotIn("stdout", result)
        self.assertNotIn("stderr", result)

    def test_success_retains_only_digests_counts_and_exit(self) -> None:
        stdout = PRIVATE_OUTPUT.encode()
        stderr = b"private-stderr"
        result = self.smoke(
            "import sys;sys.stdout.buffer.write(%r);sys.stderr.buffer.write(%r)" % (stdout, stderr)
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["runtime_exit_code"], 0)
        self.assertEqual(result["stdout_bytes"], len(stdout))
        self.assertEqual(result["stderr_bytes"], len(stderr))
        self.assertEqual(result["stdout_sha256"], hashlib.sha256(stdout).hexdigest())
        self.assertEqual(result["stderr_sha256"], hashlib.sha256(stderr).hexdigest())
        self.assert_private(result)

    def test_nonzero_exit_keeps_bounded_diagnostics(self) -> None:
        result = self.smoke("import sys;sys.stderr.write(%r);sys.exit(7)" % PRIVATE_OUTPUT)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["runtime_exit_code"], 7)
        self.assertEqual(result["stderr_bytes"], len(PRIVATE_OUTPUT))
        self.assert_private(result)

    def test_sixteen_megabyte_output_fails_with_sanitized_budget_code(self) -> None:
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                result = self.smoke(
                    "import sys;sys.stdout.write(%r);sys.%s.buffer.write(b'x'*(16*1024*1024))"
                    % (PRIVATE_OUTPUT, stream)
                )
                self.assertEqual(result["status"], "fail")
                self.assertEqual(result["error_code"], "runtime_output_budget_exceeded")
                self.assertEqual(result["output_limit_bytes"], OUTPUT_LIMIT)
                self.assert_private(result)

    def test_stdout_and_stderr_share_one_budget(self) -> None:
        result = self.smoke(
            "import sys;sys.stdout.buffer.write(b'a'*(600*1024));sys.stderr.buffer.write(b'b'*(600*1024))"
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["error_code"], "runtime_output_budget_exceeded")
        self.assert_private(result)

    def test_exact_combined_output_budget_passes(self) -> None:
        result = self.smoke(
            "import sys;sys.stdout.buffer.write(b'a'*(512*1024));sys.stderr.buffer.write(b'b'*(512*1024))"
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["stdout_bytes"] + result["stderr_bytes"], OUTPUT_LIMIT)
        self.assert_private(result)

    def test_public_cli_output_overflow_is_nonzero_and_private(self) -> None:
        command = [
            sys.executable, "-m", "agent_dev_kit.cli", "target", "smoke",
            "--target", "claude-code", "--stage", "discovery", "--profile", "core",
            "--timeout-seconds", "5", "--summary-json", "--runtime-command",
            sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'x'*(16*1024*1024))",
        ]
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["error_code"], "runtime_output_budget_exceeded")
        self.assert_private(result)

    @unittest.skipUnless(os.name == "posix", "requires POSIX pipe-holder cleanup")
    def test_timeout_closes_pipe_transports_before_the_event_loop(self) -> None:
        launcher = (
            "import subprocess,sys;"
            "subprocess.Popen([sys.executable,'-c','import time;time.sleep(3)'])"
        )
        script = (
            "import gc,json,sys,warnings;from pathlib import Path;"
            "from agent_dev_kit.model import Manifest;"
            "from agent_dev_kit.targets import run_target_smoke;"
            "warnings.simplefilter('always',ResourceWarning);"
            "result=run_target_smoke(Manifest.load(Path(%r)),'claude-code','discovery',"
            "[sys.executable,'-c',%r],profile='core',timeout_seconds=1);"
            "gc.collect();print(json.dumps(result))" % (str(ROOT), launcher)
        )
        completed = subprocess.run(
            [sys.executable, "-c", script], cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["error_code"], "runtime_timeout")
        self.assertEqual(completed.stderr, "", "pipe cleanup leaked transports or event-loop callbacks")

    def check_descendant_timeout(self, *, launcher_exits: bool) -> None:
        with tempfile.TemporaryDirectory(prefix="target-smoke-descendant-") as temp:
            marker = Path(temp) / "late-child.txt"
            parent_pid = Path(temp) / "parent.pid"
            child = (
                "import signal,time;from pathlib import Path;"
                "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                "time.sleep(3);Path(%r).write_text('late')" % str(marker)
            )
            code = (
                "import os,subprocess,sys,time;from pathlib import Path;"
                "Path(%r).write_text(str(os.getpid()));"
                "subprocess.Popen([sys.executable,'-c',%r]);" % (str(parent_pid), child)
            )
            if not launcher_exits:
                code += "time.sleep(10)"
            started = time.monotonic()
            result = self.smoke(code, timeout=1)
            elapsed = time.monotonic() - started
            # Leave scheduling slack without admitting the child's three-second work.
            self.assertLess(elapsed, 2.75)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["error_code"], "runtime_timeout")
            self.assertFalse(marker.exists(), "descendant completed before timeout return")
            self.assertTrue(parent_pid.exists(), "runtime was not started")
            with self.assertRaises(ProcessLookupError):
                os.kill(int(parent_pid.read_text()), 0)
            time.sleep(2.3)
            self.assertFalse(marker.exists(), "descendant survived the timeout cleanup")
            self.assert_private(result)

    @unittest.skipUnless(os.name == "posix", "requires POSIX process-group cleanup")
    def test_timeout_stops_descendant_before_returning(self) -> None:
        self.check_descendant_timeout(launcher_exits=False)

    @unittest.skipUnless(os.name == "posix", "requires POSIX process-group cleanup")
    def test_exited_launcher_pipe_holders_obey_the_same_deadline(self) -> None:
        self.check_descendant_timeout(launcher_exits=True)


if __name__ == "__main__":
    unittest.main()
