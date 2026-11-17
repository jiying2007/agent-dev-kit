"""One diagnostic-only observation of the unchanged skill-content unittest command.

This in-process unittest entry point is deliberately NOT the original shell entry
point or a reproduction without perturbation. Four bounded observers can compete
for CPU/GIL and change caches. No result grants release or historical root-cause
qualification. The original suite alone determines the process exit status.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import threading
import time
import unittest


BASE = "0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb"
BASE_TREE = "77dcf4a3f0bdd08f9572329c7c2ef1de8f276ca1"
ADDITIONS = frozenset({
    "tools/diagnostics/adc_wait_20261118.py",
    ".github/workflows/adc-diagnostic-20261118.yml",
    "docs/changes/20261118-adc-wait-diagnostic/requirements.md",
    "docs/changes/20261118-adc-wait-diagnostic/design.md",
    "docs/changes/20261118-adc-wait-diagnostic/tasks.md",
})
TARGET = ("tests.test_skill_command_examples.CmakeBuildExampleTests."
          "test_adc_cmake_target_builds_and_runs_with_a_strict_c90_default")
OFFSETS = (0.25, 2.0, 7.0, 14.0)
SAMPLE_SECONDS = 0.05
READ_BYTES = 4096
MAX_RECORDS = 16
MAX_FDS = 64  # Shared by the whole sample, stricter than 64 per owned PID.
CACHE_KEYS = frozenset({"CMAKE_C_COMPILER", "CMAKE_AR", "CMAKE_RANLIB", "CMAKE_MAKE_PROGRAM",
                        "CMAKE_C_COMPILER_AR", "CMAKE_C_COMPILER_RANLIB"})
ARTIFACTS = ("CMakeFiles/adc_scale.dir/src/adc_scale.c.o", "libadc_scale.a",
             "CMakeFiles/test_adc_scale.dir/tests/test_adc_scale.c.o", "test_adc_scale")
IO_KEYS = frozenset({"rchar", "wchar", "syscr", "syscw", "read_bytes", "write_bytes",
                     "cancelled_write_bytes"})
SIGNAL_KEYS = frozenset({"SigPnd", "ShdPnd", "SigBlk", "SigIgn", "SigCgt"})
SWITCH_KEYS = frozenset({"voluntary_ctxt_switches", "nonvoluntary_ctxt_switches"})


def stamp():
    return {"monotonic": time.monotonic(), "utc": datetime.now(timezone.utc).isoformat()}


def unknown(reason):
    return {"status": "UNKNOWN", "reason": reason}


class FieldUnavailable(ValueError):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def reason_for(error):
    return error.reason if isinstance(error, FieldUnavailable) else type(error).__name__


def error_record(errors, where, error):
    if len(errors) < 64:
        errors.append({"where": where, "error": type(error).__name__})


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          timeout=15).stdout.decode("utf-8", errors="strict").strip("\n")


def source_identity(root):
    """Reject any original blob/worktree change, not merely a changed test file."""
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("unexpected repository root")
    if git(root, "rev-parse", f"{BASE}^{{tree}}") != BASE_TREE:
        raise ValueError("base tree mismatch")
    git(root, "merge-base", "--is-ancestor", BASE, "HEAD")
    # Compare the worktree to BASE, and separately HEAD to BASE so a worktree
    # restoration cannot conceal an original-file modification in the commit.
    changes = {}
    for label, args in (("head", ("diff", "--no-ext-diff", "--no-renames", "--name-status", "-z", BASE, "HEAD")),
                        ("worktree", ("diff", "--no-ext-diff", "--no-renames", "--name-status", "-z", BASE))):
        fields = git(root, *args).split("\0")
        if fields[-1] == "":
            fields.pop()
        if len(fields) % 2:
            raise ValueError("unexpected git change encoding")
        pairs = list(zip(fields[::2], fields[1::2], strict=True))
        if any(kind != "A" or path not in ADDITIONS for kind, path in pairs):
            raise ValueError("change outside the five registered additions")
        changes[label] = [{"kind": kind, "path": path} for kind, path in pairs]
    untracked = set(filter(None, git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    if not untracked <= ADDITIONS:
        raise ValueError("unregistered untracked input")
    for path in ADDITIONS:
        if not (root / path).is_file() or (root / path).is_symlink():
            raise ValueError("registered addition missing or symlinked")
    return {"status": "OBSERVED", "base": BASE, "base_tree": BASE_TREE,
            "head": git(root, "rev-parse", "HEAD"), "tree": git(root, "rev-parse", "HEAD^{tree}"),
            "changes": changes, "untracked": sorted(untracked),
            "registered_sha256": {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                                  for path in sorted(ADDITIONS)}}


def unittest_arguments(script):
    commands = []
    for line in script.splitlines():
        tokens = shlex.split(line, comments=True, posix=True)
        if tokens and tokens[0].startswith("python"):
            commands.append(tokens)
    if len(commands) != 1 or commands[0][:3] != ["python3", "-m", "unittest"]:
        raise ValueError("expected exactly one python3 -m unittest command")
    arguments = commands[0][3:]
    if (not arguments or arguments[-1] != "-v"
            or any(not re.fullmatch(r"tests\.test_[a-z0-9_]+", item) for item in arguments[:-1])
            or len(set(arguments[:-1])) != len(arguments[:-1])
            or "tests.test_skill_command_examples" not in arguments):
        raise ValueError("unexpected unittest modules or options")
    if 'export PYTHONPATH="$ROOT_DIR/src"' not in script or 'cd "$ROOT_DIR"' not in script:
        raise ValueError("unexpected shell import/cwd contract")
    return arguments


def identity(record):
    return {key: record[key] for key in ("pid", "sid", "start_ticks")}


def checked_read(path, deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("sample budget exhausted")
    with path.open("rb", buffering=0) as stream:
        data = stream.read(READ_BYTES)
    # An exactly full read might be truncated; never parse a possibly partial
    # counter as if it were complete. The individual read never exceeds 4096B.
    if len(data) == READ_BYTES:
        raise FieldUnavailable("possibly_truncated_4096_byte_read")
    return data.decode("ascii", errors="strict")


def parse_fields(text, keys, *, hexadecimal=()):
    values = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key in keys:
            value = value.strip()
            if key in hexadecimal:
                if not re.fullmatch(r"[0-9A-Fa-f]+", value):
                    raise ValueError("invalid signal mask")
                values[key] = value
            else:
                values[key] = int(value)
    return {"values": values, "missing": sorted(keys - values.keys())}


class Observer:
    """One Popen, four scheduled opportunities, no catch-up or continuation scan."""

    def __init__(self, module, process, called, returned):
        self.module = module
        self.snapshot = module.owned_process_snapshot
        self.process = process
        self.called = called
        self.returned = returned
        self.cleanup = None
        self.stop = threading.Event()
        self.samples = []
        self.errors = []
        self.sealed = False
        self.thread = threading.Thread(target=self.observe, name="adc-read-only-observer", daemon=True)

    def phase(self):
        return "cleanup_entered" if self.cleanup is not None else "before_cleanup_hook"

    def group(self, record, deadline, read):
        before_time = stamp()
        before = after = None
        data = None
        reason = None
        try:
            if self.stop.is_set() or time.monotonic() >= deadline:
                raise TimeoutError("sample budget exhausted")
            before = identity(self.module.process_status(record["pid"]))
            if before != identity(record):
                before = None  # A replacement/foreign identity is not output.
                raise FieldUnavailable("identity_changed_before_field_group")
            data = read()
            if self.stop.is_set() or time.monotonic() >= deadline:
                raise TimeoutError("sample budget exhausted before identity recheck")
            after = identity(self.module.process_status(record["pid"]))
            if after != before:
                after = None
                raise FieldUnavailable("identity_changed_after_field_group")
        except Exception as error:
            reason = reason_for(error)
        result = {"status": "OBSERVED" if reason is None else "UNKNOWN", "reason": reason,
                  "read_before": before_time, "read_after": stamp(),
                  "identity_before": before, "identity_after": after,
                  "identity_consistent": reason is None and before == after}
        if reason is None:
            result["data"] = data
        return result

    def pipes(self, pid, deadline, fd_budget):
        pipes = []
        exhausted = False
        with os.scandir(Path("/proc") / str(pid) / "fd") as entries:
            while fd_budget[0] < MAX_FDS:
                if self.stop.is_set() or time.monotonic() >= deadline:
                    raise TimeoutError("sample budget exhausted")
                entry = next(entries, None)
                if entry is None:
                    exhausted = True
                    break
                fd_budget[0] += 1
                if not entry.name.isdecimal():
                    continue
                if self.stop.is_set() or time.monotonic() >= deadline:
                    raise TimeoutError("sample budget exhausted")
                target = os.readlink(entry.path)
                match = re.fullmatch(r"pipe:\[(\d+)\]", target)
                if match is None:
                    continue  # Never retain regular paths or inspect their contents.
                info = checked_read(Path("/proc") / str(pid) / "fdinfo" / entry.name, deadline)
                flags = next((line.split(":", 1)[1].strip() for line in info.splitlines()
                              if line.startswith("flags:")), None)
                pipes.append({"fd": int(entry.name), "inode": int(match[1]),
                              "flags_octal": flags,
                              "access_mode": int(flags, 8) & os.O_ACCMODE if flags is not None else None})
        return {"pipes": pipes, "fd_directory_exhausted": exhausted, "truncated": not exhausted,
                "sample_fd_entries": fd_budget[0], "foreign_writers": "UNKNOWN_NOT_INSPECTED"}

    def sample(self, offset):
        if self.stop.is_set():
            return {"scheduled_offset": offset, "status": "NOT_OBSERVED",
                    "reason": "published_invocation_finished", "decided_at": stamp()}
        started = stamp()
        deadline = started["monotonic"] + SAMPLE_SECONDS
        result = {"scheduled_offset": offset, "status": "OBSERVED", "started": started,
                  "actual_offset": started["monotonic"] - self.returned["monotonic"],
                  "phase_start": self.phase(), "deadline": deadline, "processes": []}
        state = {}
        fd_budget = [0]
        try:
            snapshot = self.snapshot(self.process.pid, deadline, limit=MAX_RECORDS, scan_state=state)
            result["discovery"] = {key: value for key, value in snapshot.items() if key != "processes"}
            result["discovery"]["scan_advanced"] = state.get("advanced", 0)
            result["discovery"]["exhausted"] = bool(state.get("exhausted"))
            # Foreign candidate stat reads are inherent in the original helper.
            # Foreign records never reach additional field/FD reads or output.
            owned = [record for record in snapshot["processes"] if record.get("sid") == self.process.pid]
            result["discovery"]["records_truncated"] = len(owned) > MAX_RECORDS
            for record in owned[:MAX_RECORDS]:
                path = Path("/proc") / str(record["pid"])
                item = {"discovery_record": record, "fields": {}}
                readers = {
                    "schedstat": lambda p=path: self.schedstat(checked_read(p / "schedstat", deadline)),
                    "io": lambda p=path: parse_fields(checked_read(p / "io", deadline), IO_KEYS),
                    "status": lambda p=path: parse_fields(checked_read(p / "status", deadline),
                                                         SIGNAL_KEYS | SWITCH_KEYS, hexadecimal=SIGNAL_KEYS),
                    "wchan": lambda p=path: checked_read(p / "wchan", deadline).strip(),
                    "pipes": lambda p=record["pid"]: self.pipes(p, deadline, fd_budget),
                }
                for key, read in readers.items():
                    item["fields"][key] = self.group(record, deadline, read)
                result["processes"].append(item)
            result["pressure"] = {}
            for kind in ("cpu", "io", "memory"):
                try:
                    if self.stop.is_set():
                        raise TimeoutError("published invocation finished")
                    data = checked_read(Path("/proc/pressure") / kind, deadline)
                    result["pressure"][kind] = {"status": "OBSERVED", "data": self.pressure(data)}
                except Exception as error:
                    result["pressure"][kind] = unknown(reason_for(error))
        except Exception as error:
            result["status"] = "UNKNOWN"
            result["error"] = type(error).__name__
        finally:
            try:
                result["scan_closed"] = self.module.close_owned_scan(state)
            except Exception as error:
                result["scan_closed"] = False
                error_record(self.errors, "scan_close", error)
        result["finished"] = stamp()
        result["phase_end"] = self.phase()
        result["elapsed"] = result["finished"]["monotonic"] - started["monotonic"]
        result["deadline_overrun"] = max(0.0, result["finished"]["monotonic"] - deadline)
        result["fd_entries"] = fd_budget[0]
        return result

    @staticmethod
    def schedstat(text):
        values = [int(item) for item in text.split()]
        if len(values) != 3:
            raise ValueError("unexpected schedstat field count")
        return dict(zip(("runtime_ns", "runqueue_wait_ns", "timeslices"), values, strict=True))

    @staticmethod
    def pressure(text):
        result = {}
        for line in text.splitlines():
            parts = line.split()
            if not parts or parts[0] not in {"some", "full"}:
                continue
            values = {}
            for part in parts[1:]:
                key, separator, value = part.partition("=")
                if separator and key in {"avg10", "avg60", "avg300", "total"}:
                    values[key] = int(value) if key == "total" else float(value)
            result[parts[0]] = values
        return result

    def observe(self):
        try:
            for index, offset in enumerate(OFFSETS):
                due = self.returned["monotonic"] + offset
                remaining = due - time.monotonic()
                reason = None
                if self.stop.is_set():
                    reason = "published_invocation_finished"
                elif remaining <= 0:
                    reason = "scheduled_point_already_missed_no_catch_up"
                elif self.stop.wait(remaining):
                    reason = "published_invocation_finished"
                now = time.monotonic()
                next_due = (self.returned["monotonic"] + OFFSETS[index + 1]
                            if index + 1 < len(OFFSETS) else self.called["monotonic"] + 15)
                if reason is None and (now >= next_due or now >= self.called["monotonic"] + 15):
                    reason = "late_outside_scheduled_or_work_window"
                if reason is None and self.cleanup is not None:
                    reason = "cleanup_hook_already_entered"
                if reason is None:
                    sample = self.sample(offset)
                else:
                    sample = {"scheduled_offset": offset, "status": "NOT_OBSERVED", "reason": reason,
                              "decided_at": stamp(), "phase": self.phase()}
                if not self.sealed:
                    self.samples.append(sample)
        except Exception as error:
            error_record(self.errors, "observer_thread", error)

    def finish(self):
        self.stop.set()
        self.thread.join(timeout=0.1)
        self.sealed = True
        samples = list(self.samples)
        seen = {sample["scheduled_offset"] for sample in samples}
        for offset in OFFSETS:
            if offset not in seen:
                samples.append({"scheduled_offset": offset, "status": "NOT_OBSERVED",
                                "reason": "observer_did_not_finish_within_bounded_join"})
        return {"popen_called": self.called, "popen_returned": self.returned,
                "session_id": self.process.pid, "cleanup_hook_entered": self.cleanup,
                "observer_joined": not self.thread.is_alive(), "errors": list(self.errors),
                "samples": sorted(samples, key=lambda sample: sample["scheduled_offset"])}


def file_stat(value):
    return {"device": value.st_dev, "inode": value.st_ino, "mode": value.st_mode,
            "size": value.st_size, "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns}


def open_fixture(root, relative):
    """Open only a caller-whitelisted file, refusing symlinks in every component."""
    if not root.is_absolute() or any(part == ".." for part in root.parts):
        raise ValueError("unsafe fixture root")
    relative = Path(relative)
    if relative.is_absolute() or any(part in {"..", "."} for part in relative.parts):
        raise ValueError("unsafe fixture relative path")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = (*root.parts[1:], *relative.parts)
        for part in parts[:-1]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        opened = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        if not stat.S_ISREG(os.fstat(opened).st_mode):
            os.close(opened)
            raise ValueError("fixture artifact is not a regular file")
        return os.fdopen(opened, "rb")
    finally:
        os.close(descriptor)


def limited_fixture_bytes(root, relative, deadline):
    with open_fixture(root, relative) as stream:
        metadata = file_stat(os.fstat(stream.fileno()))
        chunks = []
        count = 0
        while count < 65536 and time.monotonic() < deadline:
            chunk = stream.read(min(READ_BYTES, 65536 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
        return b"".join(chunks), {"stat": metadata, "bytes_retained": count,
                                 "truncated": metadata["size"] > count}


def fixture_evidence(test, out):
    root = Path(test.root)
    expected = root / "source project/out/manual build"
    if Path(test.output) != expected:
        raise ValueError("unexpected fixture output")
    deadline = time.monotonic() + 0.1
    result = {"captured_at": stamp(), "cache_tools": {}, "artifacts": {}}
    for filename in ("CMakeCache.txt", ".ninja_log", *ARTIFACTS):
        try:
            if time.monotonic() >= deadline:
                raise TimeoutError("fixture metadata budget exhausted")
            relative = str(Path("source project/out/manual build") / filename)
            if filename in ARTIFACTS:
                with open_fixture(root, relative) as stream:
                    result["artifacts"][filename] = {"status": "OBSERVED", "stat": file_stat(os.fstat(stream.fileno()))}
                continue
            data, metadata = limited_fixture_bytes(root, relative, deadline)
            result["artifacts"][filename] = {"status": "OBSERVED", **metadata}
            if filename == ".ninja_log":
                (out / "adc.ninja_log").write_bytes(data)
            else:
                for line in data.decode("utf-8", errors="replace").splitlines(keepends=True):
                    if not line.endswith("\n"):
                        continue
                    key_type, separator, value = line.rstrip("\r\n").partition("=")
                    key, _, _kind = key_type.partition(":")
                    if separator and key in CACHE_KEYS:
                        result["cache_tools"][key] = value
        except Exception as error:
            result["artifacts"][filename] = unknown(type(error).__name__)
    result["finished_at"] = stamp()
    return result


def tools_before():
    records = {}
    for name in ("cmake", "ctest", "ninja", "cc", "ar", "ranlib", "gcc-ar", "gcc-ranlib"):
        try:
            located = shutil.which(name)
            if located is None:
                records[name] = unknown("not_on_path")
                continue
            path = Path(located).resolve(strict=True)
            metadata = path.stat()
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("tool is not a regular file")
            records[name] = {"status": "OBSERVED", "path": located, "resolved": str(path),
                             "stat": file_stat(metadata)}
        except Exception as error:
            records[name] = unknown(type(error).__name__)
    return records


def tools_after(records):
    result = {}
    for name, before in records.items():
        if before["status"] != "OBSERVED":
            result[name] = before
            continue
        try:
            path = Path(before["resolved"])
            if file_stat(path.stat()) != before["stat"]:
                raise ValueError("tool changed before post-suite inspection")
            digest = hashlib.sha256()
            deadline = time.monotonic() + 2
            count = 0
            with path.open("rb") as stream:
                while True:
                    if time.monotonic() >= deadline or count > 128 * 1024 * 1024:
                        raise TimeoutError("tool hash budget exhausted")
                    chunk = stream.read(READ_BYTES)
                    if not chunk:
                        break
                    count += len(chunk)
                    digest.update(chunk)
            version = subprocess.run([str(path), "--version"], capture_output=True, timeout=2, check=False)
            after = file_stat(path.stat())
            if after != before["stat"]:
                raise ValueError("tool changed during post-suite inspection")
            result[name] = {"status": "OBSERVED", "sha256": digest.hexdigest(), "bytes_hashed": count,
                            "stat_unchanged": True, "version_exit_code": version.returncode,
                            "version_stdout": version.stdout[:READ_BYTES].decode(errors="replace"),
                            "version_stderr": version.stderr[:READ_BYTES].decode(errors="replace"),
                            "version_truncated": len(version.stdout) > READ_BYTES or len(version.stderr) > READ_BYTES}
        except Exception as error:
            result[name] = unknown(type(error).__name__)
    return result


class SubprocessView:
    """A module-local Popen observer; the real subprocess module is untouched."""

    def __init__(self, original, popen):
        self.original = original
        self.Popen = popen

    def __getattr__(self, name):
        return getattr(self.original, name)


class Diagnostic:
    def __init__(self, root, out):
        self.root = root
        self.out = out
        self.errors = []
        self.target_tests = 0
        self.invocations = 0
        self.observation = {"status": "NOT_OBSERVED", "reason": "target_invocation_not_reached",
                            "samples": [{"scheduled_offset": offset, "status": "NOT_OBSERVED",
                                         "reason": "target_invocation_not_reached"} for offset in OFFSETS]}
        self.fixture = unknown("target_invocation_not_reached")
        self.attached = {}

    def attach(self, test):
        if test.id() != TARGET:
            return
        self.target_tests += 1
        original = test.published
        self.attached[id(test)] = (test, test.__dict__.get("published"), "published" in test.__dict__)

        def published(marker, **overrides):
            if marker != "# cmake-build:" or overrides.get("ADK_SOURCE_DIR") != str(self.root / "examples/embedded-test-matrix"):
                return original(marker, **overrides)
            self.invocations += 1
            if self.invocations != 1:
                self.errors.append({"where": "selection", "error": "UnexpectedAdditionalTargetInvocation"})
                return original(marker, **overrides)
            return self.invoke(test, original, marker, overrides)

        test.published = published

    def detach(self, test):
        stored = self.attached.pop(id(test), None)
        if stored is not None:
            _test, previous, existed = stored
            if existed:
                test.published = previous
            else:
                del test.published

    def invoke(self, test, original, marker, overrides):
        try:
            module = sys.modules[test.__class__.__module__]
            original_subprocess = module.subprocess
            original_snapshot = module.owned_process_snapshot
        except Exception as error:
            error_record(self.errors, "hook_setup", error)
            return original(marker, **overrides)
        observer = None
        published_started = stamp()

        def popen(*args, **kwargs):
            nonlocal observer
            called = stamp()
            process = original_subprocess.Popen(*args, **kwargs)
            returned = stamp()
            try:
                command = args[0] if args else kwargs.get("args")
                environment = kwargs.get("env")
                if (observer is None and isinstance(command, (list, tuple)) and list(command[:2]) == ["bash", "-c"]
                        and kwargs.get("start_new_session") is True and isinstance(environment, dict)
                        and environment.get("ADK_SOURCE_DIR") == str(self.root / "examples/embedded-test-matrix")):
                    observer = Observer(module, process, called, returned)
                    observer.snapshot = original_snapshot
                    observer.thread.start()
            except Exception as error:
                error_record(self.errors, "popen_observer", error)
            return process

        def cleanup_snapshot(session_id, *args, **kwargs):
            try:
                if observer is not None and session_id == observer.process.pid and observer.cleanup is None:
                    observer.cleanup = stamp()
            except Exception as error:
                error_record(self.errors, "cleanup_event", error)
            return original_snapshot(session_id, *args, **kwargs)

        module.subprocess = SubprocessView(original_subprocess, popen)
        module.owned_process_snapshot = cleanup_snapshot
        try:
            return original(marker, **overrides)
        finally:
            published_finished = stamp()
            # Restore hooks before any diagnostic file or version operation.
            module.subprocess = original_subprocess
            module.owned_process_snapshot = original_snapshot
            try:
                if observer is not None:
                    self.observation = observer.finish()
                    self.observation["published_entered"] = published_started
                    self.observation["published_finished"] = published_finished
            except Exception as error:
                error_record(self.errors, "observer_finish", error)
            try:
                self.fixture = fixture_evidence(test, self.out)
            except Exception as error:
                error_record(self.errors, "fixture_capture", error)

    def result_class(self):
        diagnostic = self

        class ObservedResult(unittest.TextTestResult):
            def startTest(self, test):
                super().startTest(test)
                try:
                    diagnostic.attach(test)
                except Exception as error:
                    error_record(diagnostic.errors, "attach", error)

            def stopTest(self, test):
                try:
                    diagnostic.detach(test)
                except Exception as error:
                    error_record(diagnostic.errors, "detach", error)
                super().stopTest(test)

        return ObservedResult


def write_report(out, report):
    with (out / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.out
    created = False
    report = {"qualification": "DIAGNOSTIC_ONLY_NONE", "historical_root_cause": "UNKNOWN",
              "entry_point": "equivalent in-process unittest wrapper; not the original shell invocation",
              "perturbation": "4 x 50ms opportunities can compete for CPU/GIL and alter procfs/cache",
              "phase_semantics": "before_cleanup_hook is not proof of being before TimeoutExpired",
              "work_clock": "Popen call/return bracket is recorded; run_example work-start is not instrumented",
              "sample_budget": {"seconds": SAMPLE_SECONDS, "discovery_entries": 256,
                                "owned_records": MAX_RECORDS, "fd_entries_total": MAX_FDS,
                                "best_effort_blocking_read_overruns_are_reported": True},
              "started": stamp(), "suite": {"status": "NOT_RUN"}, "errors": []}
    try:
        if (not out.is_absolute() or ".." in out.parts or out.resolve() != out
                or out.is_relative_to(root) or out.exists()):
            raise ValueError("out must be a fresh canonical absolute directory outside the repository")
        out.mkdir(mode=0o700)
        created = True
        if sys.version_info[:2] != (3, 12) or sys.platform != "linux":
            raise ValueError("diagnostic requires the registered Linux/Python 3.12 environment")
        report["source_before"] = source_identity(root)
        script = (root / "tests/test_skill_content.sh").read_text()
        arguments = unittest_arguments(script)
        report["unittest_arguments"] = arguments
        report["script_sha256"] = hashlib.sha256(script.encode()).hexdigest()
        report["python"] = {"version": sys.version, "executable": sys.executable}
        try:
            report["clk_tck"] = {"status": "OBSERVED", "value": os.sysconf("SC_CLK_TCK")}
        except (OSError, ValueError) as error:
            report["clk_tck"] = unknown(type(error).__name__)
        report["tools_before"] = tools_before()
    except Exception as error:
        error_record(report["errors"], "precondition_NOT_RUN", error)
        if created:
            try:
                write_report(out, report)
            except Exception:
                pass
        print(f"DIAGNOSTIC NOT_RUN: {type(error).__name__}", file=sys.stderr)
        return 2

    os.chdir(root)
    os.environ["PYTHONPATH"] = str(root / "src")
    sys.path[:] = [str(root), str(root / "src"), *[entry for entry in sys.path
                   if entry not in {str(root), str(root / "src"), str(Path(__file__).parent)}]]
    diagnostic = Diagnostic(root, out)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=diagnostic.result_class())
    report["suite"]["started"] = stamp()
    try:
        program = unittest.main(module=None, argv=["python3 -m unittest", *arguments], testRunner=runner, exit=False)
        result = program.result
        # Match Python 3.12 unittest.TestProgram.runTests, including empty runs
        # and module-level skips (which can have testsRun == 0).
        exit_code = 5 if result.testsRun == 0 and not result.skipped else (0 if result.wasSuccessful() else 1)
        report["suite"].update({"status": "COMPLETED", "exit_code": exit_code,
                                "tests_run": result.testsRun, "failures": len(result.failures),
                                "errors": len(result.errors), "skipped": len(result.skipped)})
        if exit_code == 0:
            print("[PASS] Skills content v2, OpenAI metadata and Commit Policy")
        return exit_code
    finally:
        if report["suite"]["status"] == "NOT_RUN":
            report["suite"]["status"] = "INTERRUPTED"
        report["suite"]["finished"] = stamp()
        report["target_tests"] = diagnostic.target_tests
        report["target_invocations"] = diagnostic.invocations
        report["observation"] = diagnostic.observation
        report["fixture"] = diagnostic.fixture
        report["errors"].extend(diagnostic.errors)
        # Diagnostic failures must not replace an AssertionError, SkipTest,
        # KeyboardInterrupt, unittest failure, or the suite's exit code.
        try:
            report["tools_after"] = tools_after(report["tools_before"])
            report["source_after"] = source_identity(root)
            report["source_unchanged"] = report["source_after"] == report["source_before"]
        except Exception as error:
            error_record(report["errors"], "post_suite", error)
        report["finished"] = stamp()
        try:
            write_report(out, report)
        except Exception as error:
            print(f"DIAGNOSTIC report unavailable: {type(error).__name__}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
