"""Run published observation/waiting examples on owned host processes and threads."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import queue
import re
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "skills/adk-performance-profiling-embedded/references/mcu-memory-footprint.md"
FLAKY = ROOT / "optional-skills/adk-test-flakiness-triage/references/details.md"


def example(path: Path, language: str, marker: str) -> str:
    matches = [code for code in re.findall(r"```" + language + r"\n(.*?)```", path.read_text(), re.S)
               if marker in code]
    if len(matches) != 1:
        raise AssertionError(f"expected one published {marker} example")
    return matches[0]


@unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("cc") and shutil.which("rg"),
                     "owned ELF loader fixture requires Linux, a C compiler and rg")
class RunningObjectEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="adk runtime evidence ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.baseline = self.root / "baseline library"
        self.candidate = self.root / "candidate library"
        self.library = "libprofile_fixture.so"
        for directory, value in ((self.baseline, 7), (self.candidate, 11)):
            directory.mkdir()
            source = directory / "probe.c"
            source.write_text(f"int profile_sample(void) {{ return {value}; }}\n")
            self.compile("-shared", "-fPIC", str(source), "-Wl,-soname," + self.library,
                         "-o", str(directory / self.library))
        source = self.root / "runner.c"
        source.write_text(
            '#include <stdio.h>\n#include <unistd.h>\n'
            'extern int profile_sample(void);\n'
            'int main(void) { char done; printf("%d\\n", profile_sample()); fflush(stdout);\n'
            '  return read(0, &done, 1) == 1 ? 0 : 3; }\n')
        self.binary = self.root / "runner"
        self.compile(str(source), "-L" + str(self.baseline), "-lprofile_fixture",
                     "-Wl,--enable-new-dtags,-rpath," + str(self.baseline),
                     "-o", str(self.binary))
        self.snapshot_code = example(PROFILE, "sh", "profile-object-snapshot")

    def compile(self, *arguments):
        result = subprocess.run([shutil.which("cc"), *arguments], capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    @contextmanager
    def running(self, directory=None):
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT"}}
        if directory is not None:
            environment["LD_LIBRARY_PATH"] = str(directory)
        process = subprocess.Popen([str(self.binary)], env=environment, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            readable, _, _ = select.select([process.stdout], [], [], 5)
            self.assertTrue(readable, "owned runner did not reach its observation barrier")
            line = process.stdout.readline()
            self.assertTrue(line, "owned runner exited before observation")
            yield process, int(line)
            process.stdin.write("x")
            process.stdin.flush()
            self.assertEqual(0, process.wait(timeout=3))
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()

    def snapshot(self, process, object_name=None):
        result = self.collect(process, object_name)
        self.assertEqual(0, result.returncode, result.stderr)
        lines = result.stdout.splitlines()
        return {"executable": lines[0], "mapped_objects": sorted({
            line.split(None, 5)[5] for line in lines[1:]})}

    def collect(self, process, object_name=None):
        environment = dict(os.environ, profile_pid=str(process.pid),
                           profile_object=object_name or self.library)
        return subprocess.run(["bash", "-euc", self.snapshot_code], env=environment,
                              capture_output=True, text=True, timeout=5)

    def test_same_executable_can_run_a_different_library(self):
        binary_hash = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        with self.running() as (process, output):
            baseline = self.snapshot(process)
            self.assertEqual(7, output)
            self.assertEqual([str(self.baseline / self.library)], baseline["mapped_objects"])
            self.assertNotIn(str(self.candidate / self.library), baseline["mapped_objects"])
        with self.running(self.candidate) as (process, output):
            candidate = self.snapshot(process)
            self.assertEqual(11, output)
            self.assertEqual([str(self.candidate / self.library)], candidate["mapped_objects"])
        self.assertEqual(binary_hash, hashlib.sha256(self.binary.read_bytes()).hexdigest())
        for observed in (baseline, candidate):
            self.assertEqual(str(self.binary), observed["executable"])

    def test_deleted_and_absent_objects_do_not_become_verified_files(self):
        with self.running() as (process, output):
            self.assertEqual(7, output)
            (self.baseline / self.library).unlink()
            observed = self.snapshot(process)
            self.assertEqual([str(self.baseline / self.library) + " (deleted)"],
                             observed["mapped_objects"])
            absent = self.collect(process, "unloaded.so")
            self.assertNotEqual(0, absent.returncode)
            self.assertEqual(str(self.binary), absent.stdout.strip())
        gone = self.collect(process)
        self.assertNotEqual(0, gone.returncode)
        self.assertEqual("", gone.stdout)


class SignallingCondition(threading.Condition):
    """Expose each actual wait entry to control order without scheduling sleeps."""
    def __init__(self):
        super().__init__()
        self.wait_entries = queue.Queue()

    def wait(self, timeout=None):
        self.wait_entries.put(timeout)
        return super().wait(timeout)


class OperationReadinessTests(unittest.TestCase):
    def setUp(self):
        namespace = {}
        exec(compile(example(FLAKY, "python", "def wait_for_operation"), str(FLAKY), "exec"), namespace)
        self.wait_for_operation = namespace["wait_for_operation"]

    @contextmanager
    def waiting(self, state, operation_id="current"):
        cv, result = SignallingCondition(), queue.Queue()
        def worker():
            try:
                result.put(("value", self.wait_for_operation(cv, state, operation_id, 3)))
            except BaseException as error:
                result.put(("error", error))
        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
        try:
            yield cv, result
        finally:
            with cv:
                state.update(id=operation_id, cancelled=True)
                cv.notify_all()
            worker_thread.join(timeout=5)
            self.assertFalse(worker_thread.is_alive(), "owned worker did not stop")

    def test_old_completion_and_spurious_notification_cannot_complete_new_request(self):
        state = dict(id="old", ready=True, cancelled=False, result=42)
        with self.waiting(state) as (cv, result):
            cv.wait_entries.get(timeout=2)
            with cv:
                cv.notify_all()  # no new operation result
            cv.wait_entries.get(timeout=2)  # it had to inspect the old ID and wait again
            self.assertTrue(result.empty())
            with cv:
                state.update(id="current", ready=True, result=0)
                cv.notify_all()
            self.assertEqual(("value", 0), result.get(timeout=2))

    def test_pending_work_uses_notification_and_preserves_cancellation(self):
        state = dict(id="current", ready=False, cancelled=False, result=None)
        with self.waiting(state) as (cv, result):
            cv.wait_entries.get(timeout=2)
            self.assertTrue(result.empty())  # inspecting before completion would be wrong
            with cv:
                state.update(cancelled=True, ready=True, result=99)
                cv.notify_all()
            kind, value = result.get(timeout=2)
            self.assertEqual("error", kind)
            self.assertIsInstance(value, InterruptedError)

    def test_timeout_and_completed_zero_value_are_distinct(self):
        cv = threading.Condition()
        state = dict(id="current", ready=False, cancelled=False, result=0)
        for invalid in (None, -1, float("nan"), float("inf")):
            with self.subTest(timeout=invalid), self.assertRaises(ValueError):
                self.wait_for_operation(cv, state, "current", invalid)
        with patch("time.time", side_effect=AssertionError("wall clock must not set deadline")):
            with self.assertRaises(TimeoutError):
                self.wait_for_operation(cv, state, "current", 0.01)
            state["ready"] = True
            self.assertEqual(0, self.wait_for_operation(cv, state, "current", 0))


if __name__ == "__main__":
    unittest.main()
