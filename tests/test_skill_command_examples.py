"""Execute the published Skill examples against isolated, observable failures."""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from itertools import chain
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "skills/adk-release-versioning/references/details.md"
FLAKY = "optional-skills/adk-test-flakiness-triage/references/details.md"
SECURITY = "optional-skills/adk-security-supply-chain/SKILL.md"
SUPPLY_RUNBOOK = "docs/runbooks/security-supply-chain.md"
BSP = "skills/adk-bsp-porting-playbook/SKILL.md"
INTERFACE = "skills/adk-interface-contract-design/references/details.md"
ADC = ROOT / "examples/embedded-test-matrix"
CMAKE = "skills/adk-cmake-cross-build/SKILL.md"
HIL = "skills/adk-integration-hil-sil/SKILL.md"


def bash_example(path: str, marker: str) -> str:
    blocks = re.findall(r"```bash\n(.*?)```", (ROOT / path).read_text(), re.S)
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"expected one executable example for {marker}: {path}")
    return matches[0]


def process_status(pid, *, proc_root=Path("/proc")):
    """Read bounded status and stable identity, never arguments or environment."""
    with (proc_root / str(pid) / "stat").open(encoding="utf-8", errors="replace") as stream:
        before, fields = stream.read(4096).rsplit(") ", 1)
    actual_pid, comm = before.split(" (", 1)
    if int(actual_pid) != pid:
        raise ValueError("process identity changed")
    fields = fields.split()
    return {"pid": pid, "ppid": int(fields[1]), "pgid": int(fields[2]), "sid": int(fields[3]),
            "start_ticks": int(fields[19]), "comm": comm, "state": fields[0],
            "user_ticks": int(fields[11]), "system_ticks": int(fields[12]), "wchan": "unavailable"}


def close_owned_scan(scan_state):
    context = scan_state.pop("context", None)
    scan_state.pop("entries", None)
    if context is not None:
        try:
            context.__exit__(None, None, None)
        except Exception:
            return False
    return True


def owned_process_snapshot(session_id, deadline, *, proc_root=Path("/proc"), limit=16, scan_state=None):
    """One bounded batch; a caller-owned cursor can continue within cleanup's deadline."""
    state = {} if scan_state is None else scan_state
    result = None
    try:
        result = process_snapshot_batch(session_id, deadline, proc_root, limit, state)
    finally:
        if scan_state is None and not close_owned_scan(state) and result is not None:
            result["status"] = "unavailable"
    return result


def process_snapshot_batch(session_id, deadline, proc_root, limit, scan_state):
    """Best-effort Linux status only; never collect arguments or environments."""
    scan_state["started"] = True
    records = []
    status = "observed"
    bounded_by = None
    scanned = 0
    seen = set()
    # A diagnostic shares the caller's cleanup deadline and gets at most 50 ms.
    deadline = min(deadline, time.monotonic() + 0.05)

    def bound(reason):
        nonlocal status, bounded_by
        status = "bounded"
        bounded_by = bounded_by or reason

    def available():
        if time.monotonic() >= deadline:
            bound("deadline")
        elif scanned >= 256:
            bound("entries")
        elif len(records) >= limit:
            bound("records")
        else:
            return True
        return False

    def take():
        nonlocal scanned
        if not available():
            return False
        scanned += 1
        return True

    def partial():
        nonlocal status
        if status == "observed":
            status = "partial"

    def observe(pid, *, owned_path, entry_reserved=False):
        if pid in seen or (not entry_reserved and not take()):
            return None
        seen.add(pid)
        try:
            record = process_status(pid, proc_root=proc_root)
            if record["sid"] != session_id:
                return None
            records.append(record)
            if available():
                try:
                    with (proc_root / str(pid) / "wchan").open(encoding="utf-8", errors="replace") as stream:
                        record["wchan"] = stream.read(128).strip()
                except OSError:
                    pass  # Optional wait detail does not establish process membership.
            return record
        except FileNotFoundError:
            if owned_path:
                partial()  # A vanished owned parent can leave reparented descendants.
        except (OSError, ValueError, IndexError):
            partial()
        return None

    # Spend the same bounded budget on our own tree before unrelated global PIDs.
    pending = deque([] if scan_state.get("priority_done") else [session_id])
    scan_state["priority_done"] = True
    queued = {session_id}
    while pending and available():
        record = observe(pending.popleft(), owned_path=True)
        if record is None or not available():
            continue
        try:
            with os.scandir(proc_root / str(record["pid"]) / "task") as threads:
                while take():
                    thread = next(threads, None)
                    if thread is None:
                        break
                    if not thread.name.isdecimal():
                        continue
                    with (Path(thread.path) / "children").open("rb") as stream:
                        children = stream.read(4097)
                    if len(children) > 4096:
                        bound("children-bytes")
                        children = children[:4096]
                        if children and not children[-1:].isspace():
                            pieces = children.rsplit(None, 1)
                            children = pieces[0] if len(pieces) == 2 else b""
                    for child in children.split():
                        if not take():
                            break
                        if not child.isdigit() or int(child) <= 0:
                            partial()
                            continue
                        pid = int(child)
                        if pid not in queued:
                            pending.append(pid)
                            queued.add(pid)
        except (OSError, ValueError):
            partial()  # Missing owned task/children data cannot prove tree completion.

    # A tree alone misses reparented same-session processes. Only a complete
    # global sweep can establish full observation; a bounded sweep retains the
    # owned records above so cleanup can still terminate their verified PIDs.
    if available() and not scan_state.get("exhausted"):
        try:
            if "entries" not in scan_state:
                scan_state["context"] = os.scandir(proc_root)
                scan_state["entries"] = scan_state["context"].__enter__()
            while take():
                entry = next(scan_state["entries"], None)
                if entry is None:
                    scan_state["exhausted"] = True
                    break
                scan_state["advanced"] = scan_state.get("advanced", 0) + 1
                if entry.name.isdecimal():
                    # The global directory entry and its bounded stat read are
                    # one reserved unit. Charging twice would consume a numeric
                    # boundary entry without observing it on any later page.
                    observe(int(entry.name), owned_path=False, entry_reserved=True)
        except OSError:
            status = "unavailable"
            scan_state["exhausted"] = True
    result = {"status": status, "processes": records}
    if status == "bounded":
        result["bounded_by"] = bounded_by
    report = scan_state.setdefault("report", {"status": "observed", "processes": [], "batches": 0,
                                               "scope": "accumulated-batches", "batch_results": []})
    report["batches"] += 1
    if status != "observed" and report["status"] == "observed":
        report["status"] = status  # Later complete pages must not erase earlier missing evidence.
    if len(report["batch_results"]) < 16:
        report["batch_results"].append({"status": status, "bounded_by": bounded_by,
                                         "records": len(records), "exhausted": bool(scan_state.get("exhausted"))})
    else:
        report["batch_results_truncated"] = True
    for record in records:
        for index, previous in enumerate(report["processes"]):
            if previous["pid"] == record["pid"]:
                report["processes"][index] = record
                break
        else:
            if len(report["processes"]) < 16:
                report["processes"].append(record)
            else:
                report["records_truncated"] = True
                if report["status"] == "observed":
                    report["status"] = "bounded"
    return result


def same_process(left, right):
    return all(left[key] == right[key] for key in ("pid", "sid", "start_ticks"))


def terminate_owned_process(record, session_id, deadline):
    """Signal an exact, freshly checked process; never a numeric foreign group."""
    if record["sid"] != session_id or time.monotonic() >= deadline:
        return False
    if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        return False
    descriptor = None
    try:
        descriptor = os.pidfd_open(record["pid"])
        current = process_status(record["pid"])
        if not same_process(record, current) or time.monotonic() >= deadline:
            return False
        if current["state"] not in {"Z", "X"}:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        return True
    except (ProcessLookupError, FileNotFoundError):
        return True  # The exact process has already exited; never signal its replacement.
    except (OSError, ValueError, IndexError):
        return False
    finally:
        if descriptor is not None:
            os.close(descriptor)


def cleanup_owned_session(leader, snapshot, deadline, *, scan_state=None):
    """Use the original leader as an unreaped identity anchor until cleanup ends."""
    if leader is None or leader["sid"] != leader["pid"]:
        return "session-unverified"
    if not same_process(leader, process_status(leader["pid"])):
        return "session-unverified"
    verified = (snapshot["status"] == "observed" and hasattr(os, "pidfd_open")
                and hasattr(signal, "pidfd_send_signal"))
    current = snapshot
    pass_had_live = False
    while time.monotonic() < deadline:
        verified = verified and current["status"] == "observed"
        report = scan_state.get("report") if scan_state is not None else None
        if report is not None:
            # A complete final page cannot erase gaps in accumulated evidence.
            verified = (verified and report.get("status") == "observed"
                        and not report.get("records_truncated") and not report.get("batch_results_truncated"))
        live = [item for item in current["processes"] if item["state"] not in {"Z", "X"}]
        continuing = scan_state is not None and scan_state.get("started")
        if not live and not continuing:
            return "complete" if verified else "session-unverified"
        pass_had_live = pass_had_live or bool(live)
        # Stop coordinators before their leaves; the leader is not reaped here.
        signalling_failed = False
        for record in sorted(live, key=lambda item: item["pid"] != leader["pid"]):
            if not terminate_owned_process(record, leader["sid"], deadline):
                signalling_failed = True
        if signalling_failed:
            return "session-unverified"
        if continuing and scan_state.get("exhausted"):
            if not pass_had_live:
                return "complete" if verified else "session-unverified"
            # Killing a member seen on an earlier page is not proof it exited.
            # A new pass must observe no live members before cleanup can finish.
            if not close_owned_scan(scan_state):
                return "session-unverified"
            scan_state["exhausted"] = False
            pass_had_live = False
        previous_progress = scan_state.get("advanced", 0) if continuing else 0
        current = owned_process_snapshot(leader["sid"], deadline, scan_state=scan_state)
        if (continuing and not scan_state.get("exhausted")
                and scan_state.get("advanced", 0) == previous_progress
                and not any(item["state"] not in {"Z", "X"} for item in current["processes"])):
            return "session-unverified"  # No new page or live member: do not spin on an empty observation.
    return "session-incomplete"


def run_example(code: str, root: Path, *arguments: str, environment=None,
                timeout=15, label="skill-example"):
    """Bound the whole example and clean its owned session, including new groups."""
    command = ["bash", "-c", code, "skill-example", *arguments]
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        leader = process_status(process.pid)
    except Exception:
        leader = None  # Fast normal exits or missing procfs must not fail normal commands.
    try:
        stdout, stderr = process.communicate(timeout=max(0, started + timeout - time.monotonic()))
    except subprocess.TimeoutExpired as expired:
        work_elapsed = time.monotonic() - started
        cleanup_started = time.monotonic()
        cleanup_deadline = cleanup_started + 1
        scan_state = {}
        try:
            snapshot = owned_process_snapshot(process.pid, cleanup_deadline, scan_state=scan_state)
        except Exception as error:
            # Diagnostics must never prevent termination or replace the timeout.
            snapshot = {"status": "unavailable", "error": type(error).__name__, "processes": []}
        try:
            cleanup_status = cleanup_owned_session(leader, snapshot, cleanup_deadline, scan_state=scan_state)
        except Exception:
            cleanup_status = "session-unverified"
        finally:
            if not close_owned_scan(scan_state):
                cleanup_status = "session-unverified"
            snapshot = scan_state.get("report", snapshot)
        # The original outer group remains anchored by our unreaped Popen.
        # Missing diagnostics must not disable that fallback; an observed
        # replacement identity, however, must never authorize a group signal.
        fallback_allowed = process.returncode is None
        if leader is not None:
            try:
                if not same_process(leader, process_status(process.pid)):
                    fallback_allowed = False
                    cleanup_status = "session-unverified"
            except Exception:
                cleanup_status = "session-unverified"
        try:
            if fallback_allowed:
                os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            cleanup_status = "session-unverified"
        try:
            stdout, stderr = process.communicate(timeout=max(0, cleanup_deadline - time.monotonic()))
        except subprocess.TimeoutExpired as draining:
            # A descendant outside this owned group could retain a pipe. Do not
            # let cleanup extend the work budget or wait without a limit.
            stdout, stderr = draining.stdout or expired.stdout, draining.stderr or expired.stderr
            process.stdout.close()
            process.stderr.close()
            try:
                process.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                cleanup_status = "leader-not-reaped"
            else:
                cleanup_status = "pipe-drain-incomplete"
        def decoded(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
        raise AssertionError(
            f"{label}: timeout; budget={timeout}s; work_elapsed={work_elapsed:.3f}s; "
            f"cleanup_elapsed={time.monotonic() - cleanup_started:.3f}s; cleanup={cleanup_status}\n"
            f"process_snapshot: {json.dumps(snapshot, sort_keys=True)}\n"
            f"stdout:\n{decoded(stdout)}\nstderr:\n{decoded(stderr)}"
        ) from None
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


class CommandExampleRunnerTests(unittest.TestCase):
    @contextmanager
    def foreign_proc_prefix(self, proc_root):
        """Add only unrelated directory entries; leave real procfs and signals intact."""
        original_scandir = os.scandir
        @contextmanager
        def scan(path):
            with original_scandir(path) as entries:
                prefix = (SimpleNamespace(name=f"unrelated-{number}") for number in range(256))
                yield chain(prefix, entries) if path == proc_root else entries
        with mock.patch("os.scandir", side_effect=scan):
            yield

    @staticmethod
    def proc_fixture(root, pid, *, sid=9000, children="", parent=1):
        path = root / str(pid)
        path.mkdir()
        (path / "stat").write_text(
            f"{pid} (fixture) S {parent} {pid} {sid} 0 0 0 0 0 0 0 7 8 0 0 0 0 0 0 99\n")
        thread = path / "task" / str(pid)
        thread.mkdir(parents=True)
        (thread / "children").write_text(children)
        return path

    def test_foreign_global_prefix_does_not_starve_owned_thread_descendants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = self.proc_fixture(root, 9000)
            thread = owner / "task/9004"
            thread.mkdir()
            (thread / "children").write_text("9001 9100 9001 ")
            self.proc_fixture(root, 9001, children="9002 ", parent=9000)
            self.proc_fixture(root, 9002, children="9003 ", parent=9001)
            self.proc_fixture(root, 9003, parent=9002)
            self.proc_fixture(root, 9100, sid=9100)
            # A controlled clock isolates traversal order/count, not runtime performance.
            with self.foreign_proc_prefix(root), mock.patch("time.monotonic", return_value=100):
                snapshot = owned_process_snapshot(9000, 101, proc_root=root)
            self.assertEqual({9000, 9001, 9002, 9003},
                             {record["pid"] for record in snapshot["processes"]}, snapshot)
            self.assertEqual(4, len(snapshot["processes"]), "duplicate children must be deduplicated")
            self.assertEqual("bounded", snapshot["status"], "the full SID was not observed")

    @unittest.skipUnless(sys.platform == "linux", "owned-session observation uses Linux procfs")
    def test_real_ninja_cleanup_survives_an_unrelated_global_proc_prefix(self):
        with self.foreign_proc_prefix(Path("/proc")):
            self.test_real_ninja_child_group_is_observed_and_cleaned_without_touching_another_session()

    def test_truncated_children_do_not_invent_a_partial_pid_or_lose_known_children(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = self.proc_fixture(root, 9000)
            self.proc_fixture(root, 9001)
            self.proc_fixture(root, 3)
            (owner / "task/9000/children").write_bytes(b"9001 " + b" " * 4090 + b"345 ")
            with self.foreign_proc_prefix(root), mock.patch("time.monotonic", return_value=100), \
                    mock.patch(__name__ + ".process_status", wraps=process_status) as read:
                snapshot = owned_process_snapshot(9000, 101, proc_root=root)
            self.assertEqual({9000, 9001}, {record["pid"] for record in snapshot["processes"]}, snapshot)
            self.assertNotIn(3, [call.args[0] for call in read.call_args_list])
            self.assertEqual("children-bytes", snapshot["bounded_by"])

    def test_missing_owned_children_remains_partial_after_a_complete_global_sweep(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = self.proc_fixture(root, 9000)
            (owner / "task/9000/children").unlink()
            with mock.patch("time.monotonic", return_value=100):
                snapshot = owned_process_snapshot(9000, 101, proc_root=root)
            self.assertEqual("partial", snapshot["status"])
            self.assertEqual([9000], [record["pid"] for record in snapshot["processes"]])

    def test_thread_and_global_discovery_share_the_existing_entry_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = self.proc_fixture(root, 9000)
            for tid in range(9001, 9301):
                thread = owner / "task" / str(tid)
                thread.mkdir()
                (thread / "children").write_text("")
            with mock.patch("time.monotonic", return_value=100), \
                    mock.patch("os.scandir", wraps=os.scandir) as scan:
                snapshot = owned_process_snapshot(9000, 101, proc_root=root)
            self.assertEqual("entries", snapshot["bounded_by"])
            self.assertNotIn(root, [call.args[0] for call in scan.call_args_list],
                             "global traversal cannot receive a second independent entry budget")

    def test_global_cursor_continues_without_restarting_and_closes_on_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.proc_fixture(root, 9000)
            original_scandir = os.scandir
            opened, closed, yielded = [], [], []
            def foreign_entries():
                for number in range(1024):
                    yielded.append(number)
                    yield SimpleNamespace(name="unrelated")
                raise RuntimeError("synthetic iterator error")
            @contextmanager
            def scan(path):
                if path == root:
                    opened.append(path)
                    try:
                        yield foreign_entries()
                    finally:
                        closed.append(path)
                else:
                    with original_scandir(path) as entries:
                        yield entries
            state = {}
            with mock.patch("time.monotonic", return_value=100), mock.patch("os.scandir", side_effect=scan):
                try:
                    for _ in range(3):
                        owned_process_snapshot(9000, 101, proc_root=root, scan_state=state)
                    self.assertEqual(1, len(opened))
                    self.assertEqual([], closed)
                    self.assertEqual(list(range(len(yielded))), yielded)
                    self.assertLessEqual(len(yielded), 3 * 256)
                    self.assertGreater(len(yielded), 2 * 256)
                    with self.assertRaisesRegex(RuntimeError, "synthetic iterator error"):
                        for _ in range(3):
                            owned_process_snapshot(9000, 101, proc_root=root, scan_state=state)
                finally:
                    self.assertTrue(close_owned_scan(state))
            self.assertEqual(1, len(closed))
            self.assertNotIn("entries", state)
            self.assertNotIn("context", state)

    def test_numeric_entries_at_cursor_boundaries_are_inspected_in_each_fresh_pass(self):
        for prefix_length in (255, 511):
            with self.subTest(prefix_length=prefix_length), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.proc_fixture(root, 9000)
                opened, closed = [], []
                @contextmanager
                def scan(path):
                    self.assertEqual(root, path)
                    opened.append(path)
                    entries = chain((SimpleNamespace(name="unrelated") for _ in range(prefix_length)),
                                    [SimpleNamespace(name="9000")])
                    try:
                        yield entries
                    finally:
                        closed.append(path)
                state = {"priority_done": True}
                passes = []
                with mock.patch("time.monotonic", return_value=100), \
                        mock.patch("os.scandir", side_effect=scan), \
                        mock.patch(__name__ + ".process_status", wraps=process_status) as read:
                    for _ in range(2):
                        pages = []
                        try:
                            for _ in range(prefix_length // 256 + 2):
                                advanced = state.get("advanced", 0)
                                page = owned_process_snapshot(9000, 101, proc_root=root, scan_state=state)
                                self.assertLessEqual(state.get("advanced", 0) - advanced, 256)
                                pages.append([record["pid"] for record in page["processes"]])
                            self.assertTrue(state.get("exhausted"))
                            passes.append(pages)
                        finally:
                            self.assertTrue(close_owned_scan(state))
                        state["exhausted"] = False
                self.assertEqual([9000, 9000], [call.args[0] for call in read.call_args_list], passes)
                self.assertTrue(all(sum(page.count(9000) for page in pages) == 1 for pages in passes), passes)
                self.assertEqual(2, len(opened))
                self.assertEqual(opened, closed)

    def test_standalone_snapshot_closes_its_cursor_when_observation_raises(self):
        closed = []
        @contextmanager
        def broken_scan(path):
            if path != Path("/synthetic-proc"):
                raise FileNotFoundError
            def broken_entries():
                yield SimpleNamespace(name="unrelated")
                raise RuntimeError("synthetic iterator error")
            try:
                yield broken_entries()
            finally:
                closed.append(True)
        with mock.patch("time.monotonic", return_value=100), \
                mock.patch("os.scandir", side_effect=broken_scan), \
                mock.patch(__name__ + ".process_status", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, "synthetic iterator error"):
                owned_process_snapshot(9000, 101, proc_root=Path("/synthetic-proc"))
        self.assertEqual([True], closed)

    def test_accumulated_diagnostics_keep_at_most_sixteen_records_and_prior_gaps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pid in range(9000, 9040):
                self.proc_fixture(root, pid)
            state = {}
            with mock.patch("time.monotonic", return_value=100):
                try:
                    for _ in range(5):
                        batch = owned_process_snapshot(9000, 101, proc_root=root, scan_state=state)
                        self.assertLessEqual(len(batch["processes"]), 16)
                        if state.get("exhausted"):
                            break
                    self.assertTrue(state.get("exhausted"))
                    self.assertEqual(16, len(state["report"]["processes"]))
                    self.assertTrue(state["report"]["records_truncated"])
                    self.assertEqual("bounded", state["report"]["status"])
                    self.assertEqual("observed", batch["status"])
                finally:
                    self.assertTrue(close_owned_scan(state))

    def test_cleanup_keeps_record_cap_unverified_while_signalling_all_fresh_members(self):
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / str(number) for number in range(3)]
            for root, pids in zip(roots, [range(9000, 9009), [9000, *range(9009, 9017)], [9000]]):
                root.mkdir()
                for pid in pids:
                    path = self.proc_fixture(root, pid)
                    if root != roots[0] and pid == 9000:
                        (path / "stat").write_text((path / "stat").read_text().replace(") S ", ") Z ", 1))
            real_snapshot, real_status = owned_process_snapshot, process_status
            leader = real_status(9000, proc_root=roots[0])
            state = {"priority_done": True}
            batches = []
            def snapshot(session_id, deadline, *, scan_state):
                batch = real_snapshot(session_id, deadline, proc_root=roots[len(batches)], scan_state=scan_state)
                batches.append(batch)
                return batch
            def status(pid, **kwargs):
                return real_status(pid, **kwargs) if kwargs else leader
            with mock.patch("time.monotonic", return_value=100), \
                    mock.patch(__name__ + ".process_status", side_effect=status), \
                    mock.patch(__name__ + ".owned_process_snapshot", side_effect=snapshot), \
                    mock.patch(__name__ + ".terminate_owned_process", return_value=True) as terminate:
                try:
                    first = snapshot(9000, 101, scan_state=state)
                    result = cleanup_owned_session(leader, first, 101, scan_state=state)
                finally:
                    self.assertTrue(close_owned_scan(state))
            self.assertEqual(["observed"] * 3, [batch["status"] for batch in batches])
            self.assertEqual(set(range(9000, 9017)), {call.args[0]["pid"] for call in terminate.call_args_list})
            self.assertEqual(17, terminate.call_count, "truncated diagnostics must not disable fresh cleanup")
            self.assertEqual(16, len(state["report"]["processes"]))
            self.assertTrue(state["report"]["records_truncated"])
            self.assertEqual("session-unverified", result, state["report"])

    def test_cleanup_keeps_actual_batch_log_truncation_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = self.proc_fixture(root, 9000)
            real_snapshot, real_status = owned_process_snapshot, process_status
            leader = real_status(9000, proc_root=root)
            state = {"priority_done": True}
            batches = []
            def snapshot(session_id, deadline, *, scan_state):
                if len(batches) == 16:
                    (owner / "stat").write_text((owner / "stat").read_text().replace(") S ", ") Z ", 1))
                batch = real_snapshot(session_id, deadline, proc_root=root, scan_state=scan_state)
                batches.append(batch)
                return batch
            def status(pid, **kwargs):
                return real_status(pid, **kwargs) if kwargs else leader
            with mock.patch("time.monotonic", return_value=100), \
                    mock.patch(__name__ + ".process_status", side_effect=status), \
                    mock.patch(__name__ + ".owned_process_snapshot", side_effect=snapshot), \
                    mock.patch(__name__ + ".terminate_owned_process", return_value=True) as terminate:
                try:
                    first = snapshot(9000, 101, scan_state=state)
                    result = cleanup_owned_session(leader, first, 101, scan_state=state)
                finally:
                    self.assertTrue(close_owned_scan(state))
            self.assertEqual(["observed"] * 17, [batch["status"] for batch in batches])
            self.assertEqual(16, terminate.call_count)
            self.assertEqual(16, len(state["report"]["batch_results"]))
            self.assertTrue(state["report"]["batch_results_truncated"])
            self.assertNotIn("records_truncated", state["report"])
            self.assertEqual("session-unverified", result, state["report"])

    def test_cleanup_requires_a_fresh_pass_after_signalling_the_last_page(self):
        leader = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        contexts = [mock.MagicMock() for _ in range(3)]
        state = {"started": True, "exhausted": True, "context": contexts[0], "entries": iter(())}
        observed = {"status": "observed", "processes": [leader]}
        fresh_passes = []
        def read_fresh(session_id, deadline, *, scan_state):
            self.assertFalse(scan_state["exhausted"], "an exhausted cursor is not an exit observation")
            self.assertNotIn("entries", scan_state)
            fresh_passes.append(True)
            scan_state.update(context=contexts[len(fresh_passes)], entries=iter(()), exhausted=True)
            record = dict(leader, state="S" if len(fresh_passes) == 1 else "Z")
            return {"status": "observed", "processes": [record]}
        with mock.patch("time.monotonic", return_value=100), \
                mock.patch(__name__ + ".process_status", return_value=leader), \
                mock.patch(__name__ + ".terminate_owned_process", return_value=True) as terminate, \
                mock.patch(__name__ + ".owned_process_snapshot", side_effect=read_fresh):
            try:
                result = cleanup_owned_session(leader, observed, 101, scan_state=state)
            finally:
                self.assertTrue(close_owned_scan(state))
        self.assertEqual("complete", result)
        self.assertEqual(2, len(fresh_passes))
        self.assertEqual(2, terminate.call_count)
        for context in contexts:
            context.__exit__.assert_called_once()

    def test_empty_bounded_continuation_stops_at_the_original_cleanup_deadline(self):
        leader = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        state = {"started": True, "exhausted": False}
        now = [100.0]
        bounded = {"status": "bounded", "bounded_by": "entries", "processes": []}
        def next_batch(session_id, deadline, *, scan_state):
            self.assertIs(state, scan_state)
            self.assertEqual(101, deadline)
            now[0] += 0.25
            scan_state["advanced"] = scan_state.get("advanced", 0) + 256
            return bounded
        with mock.patch("time.monotonic", side_effect=lambda: now[0]), \
                mock.patch(__name__ + ".process_status", return_value=leader), \
                mock.patch(__name__ + ".terminate_owned_process") as terminate, \
                mock.patch(__name__ + ".owned_process_snapshot", side_effect=next_batch) as snapshot:
            result = cleanup_owned_session(leader, bounded, 101, scan_state=state)
        self.assertEqual("session-incomplete", result)
        self.assertEqual(4, snapshot.call_count)
        terminate.assert_not_called()

    def test_empty_continuation_without_cursor_progress_does_not_busy_loop(self):
        leader = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        state = {"started": True, "exhausted": False, "advanced": 12}
        bounded = {"status": "bounded", "bounded_by": "deadline", "processes": []}
        with mock.patch("time.monotonic", return_value=100), \
                mock.patch(__name__ + ".process_status", return_value=leader), \
                mock.patch(__name__ + ".terminate_owned_process") as terminate, \
                mock.patch(__name__ + ".owned_process_snapshot", return_value=bounded) as snapshot:
            result = cleanup_owned_session(leader, bounded, 101, scan_state=state)
        self.assertEqual("session-unverified", result)
        snapshot.assert_called_once()
        terminate.assert_not_called()

    def test_default_budget_and_normal_exit_keep_the_original_contract(self):
        self.assertEqual(15, run_example.__kwdefaults__["timeout"])
        with tempfile.TemporaryDirectory() as directory:
            for status in (0, 7):
                result = run_example('printf "visible stdout\\n"; printf "visible stderr\\n" >&2; exit "$1"',
                                     Path(directory), str(status))
                self.assertEqual(status, result.returncode)
                self.assertEqual("visible stdout\n", result.stdout)
                self.assertEqual("visible stderr\n", result.stderr)

    @unittest.skipUnless(sys.platform == "linux", "owned-session observation uses Linux procfs")
    def test_real_ninja_child_group_is_observed_and_cleaned_without_touching_another_session(self):
        ninja = shutil.which("ninja")
        if not ninja:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail("hosted regression requires the existing Ninja tool")
            self.skipTest("Ninja unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            leaf = root / "leaf.py"
            leaf.write_text(
                "import json, os, time\nfrom pathlib import Path\n"
                "fields = Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()\n"
                "Path('leaf.json').write_text(json.dumps({'pid': os.getpid(), "
                "'pgid': os.getpgrp(), 'sid': os.getsid(0), 'start_ticks': int(fields[19])}))\n"
                "time.sleep(60)\n"
            )
            command = shlex.join([sys.executable, str(leaf)]).replace("$", "$$")
            (root / "build.ninja").write_text(f"rule hold\n  command = {command}\nbuild sentinel: hold\n")
            unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                                         start_new_session=True)
            identity = None
            try:
                code = ('printf "%s\\n" "$$" > owner.pid; "$1" -f build.ninja -j 1; '
                        'printf "unexpected completion\\n"')
                with self.assertRaises(AssertionError) as failure:
                    run_example(code, root, ninja, timeout=1, label="real-ninja-session")
                message = str(failure.exception)
                self.assertTrue((root / "leaf.json").exists(), message)
                identity = json.loads((root / "leaf.json").read_text())
                owner = int((root / "owner.pid").read_text())
                self.assertEqual(owner, identity["sid"])
                self.assertNotEqual(owner, identity["pgid"], "fixture must exercise Ninja's new group")
                snapshot = json.loads(message.split("process_snapshot: ", 1)[1].split("\nstdout:", 1)[0])
                with self.subTest("session snapshot"):
                    self.assertIn(identity["pid"], [item["pid"] for item in snapshot["processes"]], message)
                with self.subTest("live leaf cleanup"):
                    try:
                        fields = Path(f"/proc/{identity['pid']}/stat").read_text().rsplit(") ", 1)[1].split()
                    except FileNotFoundError:
                        pass
                    else:
                        self.assertIn(fields[0], {"Z", "X"}, message)
                self.assertIsNone(unrelated.poll(), "unrelated session must survive cleanup")
                self.assertNotIn(unrelated.pid, [item["pid"] for item in snapshot["processes"]])
            finally:
                unrelated.kill()
                unrelated.wait(timeout=2)
                # Independent fixture cleanup also protects a failing baseline.
                if identity is None and (root / "leaf.json").exists():
                    identity = json.loads((root / "leaf.json").read_text())
                if identity is not None:
                    try:
                        fields = Path(f"/proc/{identity['pid']}/stat").read_text().rsplit(") ", 1)[1].split()
                        if int(fields[3]) == identity["sid"] and int(fields[19]) == identity["start_ticks"]:
                            os.killpg(identity["pgid"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except FileNotFoundError:
                        pass

    def test_timeout_keeps_both_streams_kills_its_descendant_and_spares_another_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = "SYNTHETIC_PRIVATE_ARGUMENT_AND_ENVIRONMENT_8713"
            environment = dict(os.environ, DIAGNOSTIC_TEST_SECRET=private)
            unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", private],
                                         env=environment, start_new_session=True)
            try:
                code = ('"$1" -c "import time; time.sleep(60)" "$2" & child=$!; '
                        'printf "%s\\n" "$child" > child.pid; '
                        'printf "configure complete\\n"; printf "build waiting\\n" >&2; wait')
                with self.assertRaises(AssertionError) as failure:
                    run_example(code, root, sys.executable, private, environment=environment,
                                timeout=0.5, label="timeout-fixture")
                message = str(failure.exception)
                for expected in ("timeout-fixture", "budget=0.5s", "work_elapsed=", "cleanup_elapsed=",
                                 "stdout:\nconfigure complete", "stderr:\nbuild waiting"):
                    self.assertIn(expected, message)
                child = int((root / "child.pid").read_text())
                snapshot = json.loads(message.split("process_snapshot: ", 1)[1].split("\nstdout:", 1)[0])
                self.assertNotIn(private, message)
                self.assertNotIn(unrelated.pid, [record["pid"] for record in snapshot["processes"]])
                # Busy/inaccessible procfs may legitimately exhaust the small
                # diagnostic budget; that must not introduce a new timing flake.
                if sys.platform == "linux" and snapshot["status"] == "observed":
                    self.assertIn(child, [record["pid"] for record in snapshot["processes"]])
                if snapshot["processes"]:
                    self.assertEqual(1, len({record["pgid"] for record in snapshot["processes"]}))
                for record in snapshot["processes"]:
                    self.assertEqual({"pid", "ppid", "pgid", "sid", "start_ticks", "comm", "state",
                                      "user_ticks", "system_ticks", "wchan"},
                                     set(record))
                # Linux may briefly retain an already killed orphan as a zombie;
                # that is not a running child, and is reaped by its new parent.
                state = Path(f"/proc/{child}/stat")
                try:
                    child_state = state.read_text().rsplit(") ", 1)[1].split()[0]
                except FileNotFoundError:
                    pass
                else:
                    self.assertEqual("Z", child_state)
                self.assertIsNone(unrelated.poll(), "cleanup must not signal another process group")
            finally:
                unrelated.kill()
                unrelated.wait(timeout=2)
                if (root / "child.pid").exists():
                    try:
                        os.kill(int((root / "child.pid").read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_unavailable_diagnostics_do_not_replace_timeout_or_child_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch(__name__ + ".owned_process_snapshot", side_effect=OSError("private detail")):
                with self.assertRaises(AssertionError) as failure:
                    run_example('printf "started\\n"; sleep 60', root, timeout=0.1)
            message = str(failure.exception)
            self.assertIn("timeout; budget=0.1s", message)
            self.assertIn('"status": "unavailable"', message)
            self.assertIn("cleanup=session-unverified", message)
            self.assertNotIn("private detail", message)

    def test_late_status_errors_preserve_timeout_and_original_group_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            read_status = process_status
            calls = 0
            def fails_after_identity(pid, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return read_status(pid, **kwargs)
                raise RuntimeError("SYNTHETIC_PRIVATE_STATUS_FAILURE")
            try:
                with mock.patch(__name__ + ".process_status", side_effect=fails_after_identity):
                    with self.assertRaises(AssertionError) as failure:
                        run_example('printf "%s\\n" "$$" > owner.pid; printf "started\\n"; sleep 60',
                                    root, timeout=0.1)
                message = str(failure.exception)
                self.assertIn("timeout; budget=0.1s", message)
                self.assertIn("cleanup=session-unverified", message)
                self.assertIn("stdout:\nstarted", message)
                self.assertNotIn("SYNTHETIC_PRIVATE_STATUS_FAILURE", message)
            finally:
                if (root / "owner.pid").exists():
                    try:
                        owner = int((root / "owner.pid").read_text())
                        if os.getsid(owner) == owner:
                            os.killpg(owner, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_incomplete_session_observation_cannot_report_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            for status in ("bounded", "partial", "unavailable"):
                with self.subTest(status=status), mock.patch(
                        __name__ + ".owned_process_snapshot", return_value={"status": status, "processes": []}):
                    with self.assertRaises(AssertionError) as failure:
                        run_example('printf "started\\n"; sleep 60', Path(directory), timeout=0.1)
                    self.assertIn("cleanup=session-unverified", str(failure.exception))
                    self.assertIn("stdout:\nstarted", str(failure.exception))

    @unittest.skipUnless(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"), "pidfd unavailable")
    def test_process_identity_changes_are_rejected_before_signalling(self):
        original = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        for replacement in (dict(original, start_ticks=11), dict(original, sid=999)):
            with self.subTest(replacement=replacement), \
                    mock.patch(__name__ + ".process_status", return_value=replacement), \
                    mock.patch("os.pidfd_open", return_value=37), \
                    mock.patch("signal.pidfd_send_signal") as send, mock.patch("os.close") as close:
                self.assertFalse(terminate_owned_process(original, 123, time.monotonic() + 1))
                send.assert_not_called()
                close.assert_called_once_with(37)

    @unittest.skipUnless(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"), "pidfd unavailable")
    def test_foreign_session_expired_budget_and_permission_failure_never_signal(self):
        original = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        with mock.patch("os.pidfd_open") as opened, mock.patch("signal.pidfd_send_signal") as send:
            self.assertFalse(terminate_owned_process(original, 999, time.monotonic() + 1))
            self.assertFalse(terminate_owned_process(original, 123, time.monotonic() - 1))
            opened.assert_not_called()
            send.assert_not_called()
        with mock.patch("os.pidfd_open", side_effect=PermissionError), \
                mock.patch("signal.pidfd_send_signal") as send:
            self.assertFalse(terminate_owned_process(original, 123, time.monotonic() + 1))
            send.assert_not_called()

    def test_replaced_leader_cannot_authorize_session_cleanup(self):
        leader = {"pid": 123, "sid": 123, "start_ticks": 10, "state": "S"}
        snapshot = {"status": "observed", "processes": [leader]}
        with mock.patch(__name__ + ".process_status", return_value=dict(leader, start_ticks=11)), \
                mock.patch(__name__ + ".terminate_owned_process") as terminate:
            self.assertEqual("session-unverified", cleanup_owned_session(leader, snapshot, time.monotonic() + 1))
            terminate.assert_not_called()

    def test_process_snapshot_tolerates_missing_procfs_and_disappearing_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = owned_process_snapshot(123, time.monotonic() + 1, proc_root=root / "absent")
            self.assertEqual("unavailable", missing["status"])
            self.assertEqual([], missing["processes"])
            (root / "123").mkdir()  # Process disappears before stat can be read.
            (root / "124").mkdir()
            (root / "124/stat").write_text("incomplete procfs record")
            for pid, group, session in ((125, 999, 123), (126, 123, 999)):
                (root / str(pid)).mkdir()
                (root / str(pid) / "stat").write_text(
                    f"{pid} (fixture process) S 1 {group} {session} 0 0 0 0 0 0 0 7 8 0 0 0 0 0 0 99\n")
                (root / str(pid) / "cmdline").write_text("SYNTHETIC_PRIVATE_ARGUMENT")
                (root / str(pid) / "environ").write_text("SYNTHETIC_PRIVATE_ENVIRONMENT")
            snapshot = owned_process_snapshot(123, time.monotonic() + 1, proc_root=root)
            self.assertEqual([125], [record["pid"] for record in snapshot["processes"]])
            self.assertEqual("unavailable", snapshot["processes"][0]["wchan"])
            self.assertNotIn("SYNTHETIC_PRIVATE", json.dumps(snapshot))

    def test_process_snapshot_respects_record_and_expired_cleanup_budgets(self):
        with mock.patch("os.scandir", side_effect=AssertionError("expired diagnostic must not scan")):
            result = owned_process_snapshot(123, time.monotonic() - 1)
        self.assertEqual({"status": "bounded", "bounded_by": "deadline", "processes": []}, result)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pid in range(123, 128):
                (root / str(pid)).mkdir()
                (root / str(pid) / "stat").write_text(
                    f"{pid} (fixture) S 1 123 123 0 0 0 0 0 0 0 7 8 0 0 0 0 0 0 99\n")
            result = owned_process_snapshot(123, time.monotonic() + 1, proc_root=root, limit=2)
            self.assertEqual("bounded", result["status"])
            self.assertEqual(2, len(result["processes"]))


class ReleaseHistoryExampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "source repository"
        self.repo.mkdir()
        self.environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                                GIT_AUTHOR_NAME="Skill fixture", GIT_COMMITTER_NAME="Skill fixture",
                                GIT_AUTHOR_EMAIL="fixture@example.invalid",
                                GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.git("init", "-q")
        self.code = bash_example(RELEASE, "release_history()") + '\nrelease_history "$@"\n'

    def git(self, *arguments):
        result = subprocess.run(["git", *arguments], cwd=self.repo, env=self.environment,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def commit(self, subject, body=""):
        self.git("commit", "--allow-empty", "-q", "-m", subject, "-m", body)
        return self.git("rev-parse", "HEAD")

    def history(self, *arguments, root=None):
        return run_example(self.code, root or self.repo, *arguments, environment=self.environment)

    def test_initial_release_preserves_all_commits_without_tags(self):
        first = self.commit("first implementation", "Details without a conventional prefix")
        second = self.commit("fix: initial error", "Second paragraph\n\nMore evidence")
        result = self.history("initial")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=INITIAL", result.stdout)
        for value in (first, second, "first implementation", "Details without a conventional prefix",
                      "fix: initial error", "Second paragraph\n\nMore evidence"):
            self.assertIn(value, result.stdout)
        self.assertLess(result.stdout.index("commit " + first), result.stdout.index("commit " + second))

    def test_verified_release_range_keeps_breaking_revert_and_unknown_types(self):
        baseline = self.commit("published baseline")
        self.git("tag", "v1.0.0")
        changes = [
            ("feat: export data", "Export behavior"),
            ("build!: require toolchain 18", "BREAKING CHANGE: old build format is rejected"),
            ("revert: remove export", "Reverts the export behavior"),
            ("security patch for parser", "No conventional type; still needs review"),
        ]
        commits = []
        for index, (subject, body) in enumerate(changes):
            commits.append(self.commit(subject, body))
            if index == 2:
                self.git("tag", "scratch-checkpoint")
        result = self.history("since-release", "v1.0.0")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=" + baseline, result.stdout)
        self.assertNotIn("commit " + baseline, result.stdout)
        for identity, (subject, body) in zip(commits, changes):
            self.assertIn("commit " + identity, result.stdout)
            self.assertIn(subject, result.stdout)
            self.assertIn(body, result.stdout)
        self.assertEqual(commits[-1], self.git("rev-parse", "HEAD"))

    def test_invalid_or_unrelated_baseline_fails_without_initial_fallback(self):
        self.commit("baseline")
        unrelated = self.git("commit-tree", self.git("rev-parse", "HEAD^{tree}"), "-m", "unrelated root")
        for baseline in ("missing-release", "--all", unrelated):
            with self.subTest(baseline=baseline):
                result = self.history("since-release", baseline)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertTrue(result.stderr)

    def test_shallow_history_is_rejected_even_for_explicit_initial_mode(self):
        self.commit("first")
        self.commit("second")
        clone = self.root / "shallow"
        self.git("clone", "-q", "--depth=1", self.repo.as_uri(), str(clone))
        result = self.history("initial", root=clone)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("shallow", result.stderr)
        self.assertEqual("", result.stdout)

    def test_empty_verified_range_is_distinct_from_git_or_usage_failure(self):
        identity = self.commit("release")
        result = self.history("since-release", identity)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=" + identity, result.stdout)
        self.assertIn("target=" + identity, result.stdout)
        self.assertNotIn("commit ", result.stdout)
        for arguments, root in (((), self.repo), (("initial", "extra"), self.repo),
                                (("initial",), self.root)):
            with self.subTest(arguments=arguments, root=root.name):
                failed = self.history(*arguments, root=root)
                self.assertNotEqual(0, failed.returncode)
                self.assertEqual("", failed.stdout)


class SecurityScanExampleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("rg"), "execute published scans with real ripgrep")
        temporary = tempfile.TemporaryDirectory(prefix="adk scan evidence ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sentinel = "SYNTHETIC_ONLY_NOT_A_CREDENTIAL_8713"
        self.content = f'api_key="{self.sentinel}" license curl https writeFile BASE_URL\n'
        self.commands = []
        for source, count in ((SECURITY, 5), (SUPPLY_RUNBOOK, 2)):
            commands = [line for line in bash_example(source, "<candidate_path>").splitlines()
                        if line.startswith("rg ") and "<candidate_path>" in line]
            self.assertEqual(count, len(commands), source)
            self.commands.extend((source, index, command)
                                 for index, command in enumerate(commands, 1))

    def scan(self, command, candidate):
        code = "set -euo pipefail\n" + command.replace("<candidate_path>", '"$1"')
        return run_example(code, self.root, str(candidate), label="security-candidate-scan")

    def test_all_scans_keep_candidate_paths_without_printing_matching_contents(self):
        candidate = self.root / "candidate assets [fixture]"
        candidate.mkdir()
        paths = set()
        for index in range(24):
            path = candidate / f"asset-{index}.txt"
            path.write_text(self.content)
            paths.add(str(path))
        for source, index, command in self.commands:
            with self.subTest(source=source, command=index):
                result = self.scan(command, candidate)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(self.sentinel in result.stdout + result.stderr,
                                 "published scan printed synthetic file contents")
                self.assertEqual(paths, set(result.stdout.splitlines()))

    def test_no_match_and_io_errors_keep_distinct_status_and_diagnostics(self):
        ordinary = self.root / "ordinary.txt"
        ordinary.write_text("ordinary neutral prose\n")
        absent = self.root / "missing candidate.txt"
        for source, index, command in self.commands:
            with self.subTest(source=source, command=index):
                empty = self.scan(command, ordinary)
                self.assertEqual(1, empty.returncode, empty.stderr)
                self.assertEqual("", empty.stdout + empty.stderr)
                error = self.scan(command, absent)
                self.assertEqual(2, error.returncode, error.stderr)
                self.assertEqual("", error.stdout)
                self.assertIn(str(absent), error.stderr)

    def test_secret_scan_preserves_hidden_ignored_coverage_and_git_exclusion(self):
        candidate = self.root / "candidate"
        candidate.mkdir()
        (candidate / ".git").mkdir()
        (candidate / ".gitignore").write_text("ignored.txt\n")
        for path in (candidate / ".env", candidate / "ignored.txt", candidate / ".git/config"):
            path.write_text(self.content)
        source, index, command = next(item for item in self.commands
                                      if item[0] == SECURITY and "api[_-]?key" in item[2])
        result = self.scan(command, candidate)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({str(candidate / ".env"), str(candidate / "ignored.txt")},
                         set(result.stdout.splitlines()))
        self.assertNotIn(self.sentinel, result.stdout + result.stderr)


class FlakySampleExampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.code = bash_example(FLAKY, "run_flaky_samples()") + '\nrun_flaky_samples "$@"\n'
        self.runner = self.root / "sample runner [fixture].py"
        self.runner.write_text(
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "sample = Path(os.environ['FLAKY_SAMPLE_DIR'])\n"
            "attempt = int(sample.name.removeprefix('run-'))\n"
            "code = int(sys.argv[1].split(',')[attempt - 1])\n"
            "outcome = 'passed' if code == 0 else 'failed' if code == 1 else 'error'\n"
            "(sample / 'result.json').write_text(json.dumps({'name': sys.argv[2], 'outcome': outcome}))\n"
            "print('PASSED noisy_log_name\\nPASSED noisy_log_name')\n"
            "print(outcome, sys.argv[2], flush=True)\n"
            "print('stderr retained', file=sys.stderr)\n"
            "sys.exit(code)\n"
        )

    def sample(self, codes, name="test_items[case 1]", directory="new evidence", code=None):
        output = self.root / directory
        command = [sys.executable, str(self.runner), ",".join(map(str, codes)), name]
        if code is not None:
            command = [sys.executable, "-c", code]
        result = run_example(self.code, self.root, str(len(codes)), str(output), *command)
        return result, output

    def test_success_failure_and_mixed_runs_keep_exact_exit_codes_and_reports(self):
        literal_name = "test_items[case 1]; $(touch MUST_NOT_RUN)"
        for codes in ([0, 0, 0], [9, 9, 9], [0, 1, 2, 0], [0, 1, 9, 124]):
            with self.subTest(codes=codes):
                result, output = self.sample(codes, literal_name, directory="runs-" + "-".join(map(str, codes)))
                self.assertEqual(int(any(codes)), result.returncode, result.stderr)
                rows = (output / "results.tsv").read_text().splitlines()
                self.assertEqual(["attempt\texit_code", *[f"{i}\t{code}" for i, code in enumerate(codes, 1)]], rows)
                for attempt, code in enumerate(codes, 1):
                    run = output / f"run-{attempt}"
                    report = json.loads((run / "result.json").read_text())
                    self.assertEqual(literal_name, report["name"])
                    self.assertEqual("passed" if code == 0 else "failed" if code == 1 else "error", report["outcome"])
                    log = (run / "output.log").read_text()
                    self.assertIn("stderr retained", log)
                    self.assertIn(literal_name, log)
                self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_reported_interrupt_status_stops_after_preserving_the_current_sample(self):
        for status in (130, 143):
            with self.subTest(status=status):
                result, output = self.sample([status, 0, 0], directory=f"reported-{status}")
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-2").exists())
                self.assertEqual(["run-1"], sorted(path.name for path in output.glob("run-*")))
                log = (output / "run-1/output.log").read_text()
                self.assertIn("stderr retained", log)
                self.assertIn("error test_items[case 1]", log)
                self.assertTrue((output / "run-1/result.json").is_file())
                self.assertNotIn("attempts=3", result.stdout)

    def test_interrupt_after_an_observation_preserves_both_samples_and_stops(self):
        for previous, status in ((0, 130), (9, 143)):
            with self.subTest(previous=previous, status=status):
                result, output = self.sample([previous, status, 0], directory=f"later-{status}")
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{previous}\n2\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-3").exists())
                for attempt in (1, 2):
                    self.assertIn("stderr retained", (output / f"run-{attempt}/output.log").read_text())

    def test_child_self_signals_stop_sampling_without_claiming_parent_signal_handling(self):
        for signum, status in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(signal=signum.name):
                command = ("import os, signal, sys\n"
                           "print('before child signal', flush=True)\n"
                           "print('child stderr retained', file=sys.stderr, flush=True)\n"
                           f"signal.signal({int(signum)}, signal.SIG_DFL)\n"
                           f"os.kill(os.getpid(), {int(signum)})\n"
                           "raise AssertionError('child continued after its signal')\n")
                result, output = self.sample([status, 0, 0], directory=signum.name, code=command)
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-2").exists())
                self.assertEqual(["run-1"], sorted(path.name for path in output.glob("run-*")))
                log = (output / "run-1/output.log").read_text()
                self.assertIn("before child signal", log)
                self.assertIn("child stderr retained", log)
                self.assertNotIn("child continued", log)

    def test_existing_evidence_is_not_reused_or_overwritten(self):
        result, output = self.sample([0])
        self.assertEqual(0, result.returncode, result.stderr)
        before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
        result, _ = self.sample([1])
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(before, {path.relative_to(output): path.read_bytes()
                                  for path in output.rglob("*") if path.is_file()})

    def test_sample_collection_failure_stops_without_fake_completed_attempt(self):
        command = ("import os; from pathlib import Path; "
                   "sample=Path(os.environ['FLAKY_SAMPLE_DIR']); "
                   "(sample.parent / 'run-2').write_text('blocked collection path'); "
                   "print('first real observation')")
        result, output = self.sample([0, 0, 0], code=command)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("attempt\texit_code\n1\t0\n", (output / "results.tsv").read_text())
        self.assertIn("first real observation", (output / "run-1/output.log").read_text())
        self.assertFalse((output / "run-3").exists())
        self.assertNotIn("attempts=3", result.stdout)

    def test_status_write_failure_is_not_a_successful_collection(self):
        command = ("import os; from pathlib import Path; "
                   "status=Path(os.environ['FLAKY_SAMPLE_DIR']).parent / 'results.tsv'; "
                   "status.unlink(); status.mkdir(); print('test command returned zero')")
        result, output = self.sample([0], code=command)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("returned zero", (output / "run-1/output.log").read_text())

    def test_invalid_sample_budgets_do_not_execute_or_create_output(self):
        for budget in ("0", "21", "-1", "99999", "$(touch MUST_NOT_RUN)"):
            with self.subTest(budget=budget):
                output = self.root / "not-created"
                result = run_example(self.code, self.root, budget, str(output), "false")
                self.assertEqual(2, result.returncode)
                self.assertFalse(output.exists())
        self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_environment_example_only_prints_names_not_synthetic_secret_values(self):
        environment = {"PATH": os.environ["PATH"], "CI_JOB_TOKEN": "synthetic-private-value",
                       "TEST_PASSWORD": "another-private-value", "UNRELATED": "debug-value"}
        code = bash_example(FLAKY, "# environment-names:")
        result = run_example(code, self.root, environment=environment)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["CI_JOB_TOKEN", "TEST_PASSWORD"], json.loads(result.stdout))
        for value in environment.values():
            self.assertNotIn(value, result.stdout)


class BspBuildExampleTests(unittest.TestCase):
    """Run GNU make with a tiny recording Makefile, not a simulated device build."""

    def setUp(self):
        self.assertIsNotNone(shutil.which("make"), "the published example requires GNU make")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source tree"
        self.source.mkdir()
        self.output = self.root / "build output"
        self.capture = self.root / "make-calls.tsv"
        record = ('\t@printf "%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n" '
                  '"$@" "$(ARCH)" "$(CROSS_COMPILE)" "$(O)" "$(MAKEFLAGS)" '
                  '"$(CURDIR)" >> "$(BSP_CAPTURE)"\n')
        (self.source / "Makefile").write_text(
            ".PHONY: board_defconfig board-image board.dtb\n"
            "board_defconfig:\n" + record +
            '\t@test "$(FAIL_CONFIG)" != "1"\n'
            '\t@printf "CONFIG_BOARD=y\\n" > "$(O)/.config"\n'
            "board-image board.dtb:\n" + record +
            '\t@test -f "$(O)/.config"\n'
            '\t@test "$(FAIL_BUILD)" != "1"\n'
            '\t@printf "fixture artifact\\n" > "$(O)/$@"\n'
        )
        self.environment = dict(os.environ, BSP_SOURCE_DIR=str(self.source), BSP_OUTPUT_DIR=str(self.output),
                                BSP_ARCH="arm", BSP_CROSS_COMPILE="arm-linux-gnueabihf-",
                                BSP_DEFCONFIG="board_defconfig", BSP_IMAGE_TARGET="board-image",
                                BSP_DT_TARGET="board.dtb", BSP_BUILD_JOBS="2", BSP_CAPTURE=str(self.capture),
                                ARCH="arm64", CROSS_COMPILE="wrong-host-toolchain-", MAKEFLAGS="-j17",
                                FAIL_CONFIG="0", FAIL_BUILD="0")
        self.code = bash_example(BSP, "# verified-linux-kbuild:")

    def build(self, **overrides):
        return run_example(self.code, self.root, environment=dict(self.environment, **overrides))

    def calls(self):
        return [line.split("\t") for line in self.capture.read_text().splitlines()]

    def test_make_preserves_selected_arch_toolchain_config_output_and_cpu_ram_budget(self):
        result = self.build()
        self.assertEqual(0, result.returncode, result.stderr)
        rows = self.calls()
        self.assertEqual("board_defconfig", rows[0][0])
        self.assertCountEqual(["board-image", "board.dtb"], [row[0] for row in rows[1:]])
        for target, arch, cross, output, flags, source in rows:
            self.assertEqual("arm", arch, target)
            self.assertEqual("arm-linux-gnueabihf-", cross, target)
            self.assertEqual(str(self.output), output)
            self.assertEqual(str(self.source), source)
            self.assertRegex(flags, r"(?:^|\s)-j2(?:\s|$)")
            self.assertNotIn("-j17", flags)
        self.assertEqual("CONFIG_BOARD=y\n", (self.output / ".config").read_text())
        self.assertTrue((self.output / "board-image").is_file())
        self.assertTrue((self.output / "board.dtb").is_file())

    def test_no_dt_target_does_not_invent_a_dt_build(self):
        result = self.build(BSP_ARCH="arm64", BSP_CROSS_COMPILE="aarch64-linux-gnu-", BSP_DT_TARGET="")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["board_defconfig", "board-image"], [row[0] for row in self.calls()])
        self.assertTrue(all(row[1:3] == ["arm64", "aarch64-linux-gnu-"] for row in self.calls()))
        self.assertFalse((self.output / "board.dtb").exists())

    def test_invalid_job_budget_stops_before_configuration_or_output_creation(self):
        for jobs in ("", "0", "-1", "02", "2.5", "$(touch MUST_NOT_RUN)"):
            with self.subTest(jobs=jobs):
                result = self.build(BSP_BUILD_JOBS=jobs)
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.capture.exists())
        self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_existing_output_and_config_are_never_reused_or_reset(self):
        self.output.mkdir()
        original = self.output / ".config"
        original.write_text("CONFIG_USER_SETTING=y\n")
        result = self.build()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("CONFIG_USER_SETTING=y\n", original.read_text())
        self.assertFalse(self.capture.exists())

    def test_config_failure_prevents_image_and_dt_commands(self):
        result = self.build(FAIL_CONFIG="1")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(["board_defconfig"], [row[0] for row in self.calls()])
        self.assertFalse((self.output / "board-image").exists())
        self.assertFalse((self.output / "board.dtb").exists())

    def test_build_failure_is_reported_and_keeps_config_for_diagnosis(self):
        result = self.build(FAIL_BUILD="1", BSP_DT_TARGET="")
        self.assertNotEqual(0, result.returncode)
        self.assertTrue((self.output / ".config").is_file())
        self.assertFalse((self.output / "board-image").exists())

    def test_missing_identity_input_and_relative_output_do_not_build(self):
        for name in ("BSP_SOURCE_DIR", "BSP_OUTPUT_DIR", "BSP_ARCH", "BSP_CROSS_COMPILE",
                     "BSP_DEFCONFIG", "BSP_IMAGE_TARGET"):
            with self.subTest(missing=name):
                result = self.build(**{name: ""})
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.capture.exists())
        result = self.build(BSP_OUTPUT_DIR="relative-output")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "relative-output").exists())


class EmbeddedAdcExampleTests(unittest.TestCase):
    """Compile and execute the shipped C tests; no target/device claim."""

    def setUp(self):
        self.compiler = shutil.which("cc")
        self.assertIsNotNone(self.compiler, "the ADC example requires a real native C compiler")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def compile_and_run(self, *flags):
        executable = self.root / "adc-test"
        result = subprocess.run(
            [self.compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", *flags,
             "-I", str(ADC / "src"), str(ADC / "src/adc_scale.c"),
             str(ADC / "tests/test_adc_scale.c"), "-o", str(executable)],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for name in ("zero", "full-scale", "invalid", "maximum-int-full-scale", "maximum-int-clamped"):
            self.assertIn("PASS " + name + " ", result.stdout)

    def test_native_endpoints_clamping_and_invalid_inputs(self):
        self.compile_and_run("-DNDEBUG")

    def test_native_endpoints_with_supported_ubsan(self):
        flags = ("-fsanitize=signed-integer-overflow", "-fno-sanitize-recover=all")
        probe = self.root / "sanitizer-probe.c"
        probe.write_text("#include <limits.h>\nint main(void) { volatile int n = INT_MAX; return n + 1; }\n")
        executable = self.root / "sanitizer-probe"
        compiled = subprocess.run([self.compiler, *flags, str(probe), "-o", str(executable)],
                                  capture_output=True, text=True, timeout=15)
        if compiled.returncode:
            self.skipTest("UBSan capability unavailable: " + compiled.stderr.strip())
        result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 or "signed integer overflow" not in result.stderr:
            self.skipTest("UBSan runtime did not diagnose the overflow probe: " + result.stderr.strip())
        # A failure in the actual example is a regression, never a capability skip.
        self.compile_and_run(*flags)


class _CmakeExampleFixture:
    def prepare(self, *, register_tests=True, generator="Ninja"):
        backend = "make" if generator == "Unix Makefiles" else "ninja"
        required = ("cmake", "ctest", backend, "cc", "file", "size", "objdump", "python3", "mktemp")
        missing = [tool for tool in required if shutil.which(tool) is None]
        if missing:
            reason = "real CMake example not executed; missing tools: " + ", ".join(missing)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail(reason + "; GitHub Actions must execute this fixture")
            self.skipTest(reason)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / "test evidence"
        self.evidence.mkdir()
        self.source = self.root / "source project"
        self.source.mkdir()
        (self.source / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.21)\n'
            'project(adk_command_example C)\n'
            'enable_testing()\n'
            'set(FIXTURE_ID "manual" CACHE STRING "")\n'
            'add_executable(firmware main.c)\n'
            'set_target_properties(firmware PROPERTIES SUFFIX ".elf")\n'
            'file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/$<CONFIG>/identity.h"\n'
            '  CONTENT "#define FIXTURE_ID \\\"${FIXTURE_ID}:$<CONFIG>\\\"\\n")\n'
            'target_include_directories(firmware PRIVATE "${CMAKE_BINARY_DIR}/$<CONFIG>")\n'
            + ('add_test(NAME identity COMMAND firmware "${CMAKE_BINARY_DIR}/ctest-identity.txt")\n'
               if register_tests else ''))
        (self.source / "main.c").write_text(
            '#include <stdio.h>\n#include "identity.h"\n'
            'int main(int argc, char **argv) {\n'
            '  puts(FIXTURE_ID);\n'
            '  if (argc == 2) {\n'
            '    FILE *receipt = fopen(argv[1], "w");\n'
            '    if (!receipt) return 2;\n'
            '    int written = fprintf(receipt, "%s\\n", FIXTURE_ID);\n'
            '    if (fclose(receipt) != 0 || written < 0) return 3;\n'
            '  }\n'
            '  return 0;\n}\n')
        self.toolchain = self.source / "host toolchain.cmake"
        self.toolchain.write_text('set(CMAKE_C_COMPILER "' + shutil.which("cc") + '")\n')
        self.output = self.source / "out" / "manual build"
        self.environment = dict(
            os.environ, CC=shutil.which("cc"), VERBOSE="1", ADK_SOURCE_DIR=str(self.source),
            ADK_BINARY_DIR=str(self.output), ADK_GENERATOR=generator, ADK_BUILD_MODE="manual",
            ADK_TOOLCHAIN_FILE=str(self.toolchain), ADK_CONFIG="Release", ADK_BUILD_JOBS="1",
            ADK_TEST_BACKEND="host-unit", ADK_ELF=str(self.output / "firmware.elf"),
            ADK_SIZE=shutil.which("size"), ADK_OBJDUMP=shutil.which("objdump"),
            ADK_EVIDENCE_DIR=str(self.evidence),
            ADK_CONFIGURE_PRESET="unselected-configure", ADK_BUILD_PRESET="unselected-build",
            ADK_TEST_PRESET="unselected-test")

    def published(self, marker, **overrides):
        environment = dict(self.environment, **overrides)
        # Fixture-only trace identifies the last configure/build/CTest command
        # if the aggregate example budget expires; the published block is intact.
        return run_example("PS4='+${EPOCHREALTIME} ${LINENO}: '\nset -x\n" + bash_example(CMAKE, marker), self.source,
                           environment=environment, label=f"CMake/{environment['ADK_BUILD_MODE']}/{marker}")

    def assert_identity(self, identity, output, artifact):
        self.assertEqual(identity + "\n", (output / "ctest-identity.txt").read_text())
        self.assertEqual(b"\x7fELF", artifact.read_bytes()[:4])
        executed = subprocess.run([str(artifact)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, executed.returncode, executed.stderr)
        self.assertEqual(identity + "\n", executed.stdout)
        inspected = self.published("# built-artifact:", ADK_ELF=str(artifact))
        self.assertEqual(0, inspected.returncode, inspected.stdout + inspected.stderr)
        self.assertIn(str(artifact), inspected.stdout)
        self.assertIn(".text", inspected.stdout)


class CmakeBuildExampleTests(_CmakeExampleFixture, unittest.TestCase):
    """Keep the original Ninja/multiconfig cases and their CI tool requirement."""

    def test_preset_names_bind_binary_directory_configuration_tests_and_elf(self):
        self.prepare()
        old = self.source / "build" / "demo"
        # A real, separately configured old build makes a wrong directory observable.
        for command in (["cmake", "-S", str(self.source), "-B", str(old), "-G", "Ninja",
                         "-DFIXTURE_ID=old", "-DCMAKE_BUILD_TYPE=Debug"],
                        ["cmake", "--build", str(old), "--parallel", "1"]):
            result = subprocess.run(command, env=self.environment, capture_output=True, text=True, timeout=15)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        old_bytes = {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}
        output = self.source / "out" / "preset build"
        (self.source / "CMakePresets.json").write_text(json.dumps({
            "version": 3,
            "configurePresets": [{"name": "configure-board", "generator": "Ninja Multi-Config",
                                  "binaryDir": "${sourceDir}/out/preset build",
                                  "cacheVariables": {"FIXTURE_ID": "preset", "CMAKE_CONFIGURATION_TYPES": "Debug;Release"}}],
            "buildPresets": [{"name": "compile-release", "configurePreset": "configure-board", "configuration": "Release"}],
            "testPresets": [{"name": "run-release", "configurePreset": "configure-board", "configuration": "Release"}],
        }))
        result = self.published("# cmake-build:", ADK_BUILD_MODE="preset", ADK_CONFIGURE_PRESET="configure-board",
                                ADK_BUILD_PRESET="compile-release", ADK_TEST_PRESET="run-release",
                                ADK_BINARY_DIR=str(self.source / "must-not-be-created"),
                                ADK_TOOLCHAIN_FILE="missing-unselected-toolchain", ADK_GENERATOR="unselected")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assert_identity("preset:Release", output, output / "Release" / "firmware.elf")
        self.assertFalse((self.source / "must-not-be-created").exists())
        self.assertEqual(old_bytes, {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()})

    def test_manual_directory_configuration_tests_and_elf_do_not_invoke_presets(self):
        self.prepare()
        result = self.published("# cmake-build:", ADK_CONFIG="RelWithDebInfo")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assert_identity("manual:RelWithDebInfo", self.output, self.output / "firmware.elf")
        self.assertFalse((self.source / "build").exists())

    def test_empty_ctest_selection_fails_after_a_real_successful_build(self):
        self.prepare(register_tests=False)
        result = self.published("# cmake-build:")
        self.assertNotEqual(0, result.returncode)
        self.assertTrue((self.output / "firmware.elf").is_file())
        self.assertIn("No tests", result.stdout + result.stderr)
        self.assertFalse((self.output / "ctest-identity.txt").exists())

    def test_compile_only_preserves_not_run_without_invoking_ctest(self):
        self.prepare(register_tests=False)
        result = self.published("# cmake-build:", ADK_TEST_BACKEND="compile-only")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("target tests: not-run", result.stdout)
        self.assertTrue((self.output / "firmware.elf").is_file())
        self.assertFalse((self.output / "ctest-identity.txt").exists())

    def test_adc_cmake_target_builds_and_runs_with_a_strict_c90_default(self):
        self.prepare()
        # The library needs C11; its consumer tests themselves remain valid C90.
        self.toolchain.write_text(self.toolchain.read_text()
                                  + 'set(CMAKE_C_STANDARD 90)\n'
                                  + 'set(CMAKE_C_STANDARD_REQUIRED ON)\n'
                                  + 'set(CMAKE_C_EXTENSIONS OFF)\n')
        result = self.published("# cmake-build:", ADK_SOURCE_DIR=str(ADC), CFLAGS="-pedantic-errors")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("adc_scale_host_unit", result.stdout)
        executable = self.output / "test_adc_scale"
        executed = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, executed.returncode, executed.stdout + executed.stderr)
        self.assertIn("PASS maximum-int-full-scale ", executed.stdout)
        self.assertIn("PASS maximum-int-clamped ", executed.stdout)
        inspected = self.published("# built-artifact:", ADK_ELF=str(executable))
        self.assertEqual(0, inspected.returncode, inspected.stdout + inspected.stderr)
        self.assertIn(str(executable), inspected.stdout)


class CtestQualificationExampleTests(_CmakeExampleFixture, unittest.TestCase):
    """Real native CMake/CTest semantics, using an available single-config backend."""

    def prepare_native(self, *, register_tests=True, extra=""):
        self.prepare(register_tests=register_tests, generator="Unix Makefiles")
        cmake = self.source / "CMakeLists.txt"
        cmake.write_text(cmake.read_text() + extra)

    def reports(self):
        return sorted(self.evidence.glob("ctest.*/ctest.xml"))

    def test_all_skipped_is_rejected_despite_successful_ctest_exit(self):
        self.prepare_native(register_tests=False, extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'))
        result = self.published("# cmake-build:")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("passed=0 selected=1 skipped=1", result.stdout)
        self.assertIn("no executed passing tests", result.stderr)
        report, = self.reports()
        self.assertEqual("notrun", ET.parse(report).getroot().find("testcase").get("status"))

    def test_empty_and_all_disabled_selections_remain_failures(self):
        for extra in ("", 'add_test(NAME disabled COMMAND "${CMAKE_COMMAND}" -E true)\n'
                          'set_tests_properties(disabled PROPERTIES DISABLED TRUE)\n'):
            with self.subTest(disabled=bool(extra)):
                self.prepare_native(register_tests=False, extra=extra)
                result = self.published("# cmake-build:")
                self.assertNotEqual(0, result.returncode)
                self.assertTrue((self.output / "firmware.elf").is_file())
                self.assertIn("CTest report:", result.stdout)

    def test_mixed_results_report_partial_and_test_runs_only_once(self):
        self.prepare_native(extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'
            'add_test(NAME disabled COMMAND "${CMAKE_COMMAND}" -E true)\n'
            'set_tests_properties(disabled PROPERTIES DISABLED TRUE)\n'))
        main = self.source / "main.c"
        main.write_text(main.read_text().replace('fopen(argv[1], "w")', 'fopen(argv[1], "a")'))
        result = self.published("# cmake-build:")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("status=partial passed=1 selected=3 skipped=1 disabled=1", result.stdout)
        self.assertEqual("manual:Release\n", (self.output / "ctest-identity.txt").read_text())
        self.assertEqual(1, len(self.reports()))

    def test_new_run_cannot_reuse_a_previous_passing_report(self):
        self.prepare_native()
        first = self.published("# cmake-build:")
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertIn("status=pass passed=1 selected=1 skipped=0 disabled=0", first.stdout)
        original, = self.reports()
        original_bytes = original.read_bytes()
        cmake = self.source / "CMakeLists.txt"
        cmake.write_text(cmake.read_text() + 'set_tests_properties(identity PROPERTIES SKIP_RETURN_CODE 0)\n')
        second = self.published("# cmake-build:")
        self.assertNotEqual(0, second.returncode)
        self.assertIn("passed=0 selected=1 skipped=1", second.stdout)
        self.assertEqual(2, len(self.reports()))
        self.assertEqual(original_bytes, original.read_bytes())
        new_report, = [p for p in self.reports() if p != original]
        self.assertIn(str(new_report), second.stdout)

    def test_real_ctest_failure_keeps_its_nonzero_status(self):
        self.prepare_native(extra='add_test(NAME failing COMMAND "${CMAKE_COMMAND}" -E false)\n')
        result = self.published("# cmake-build:")
        self.assertEqual(8, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("status=pass", result.stdout)
        report, = self.reports()
        cases = ET.parse(report).getroot().findall("testcase")
        self.assertEqual({"run", "fail"}, {c.get("status") for c in cases})

    def test_failed_build_does_not_read_or_replace_an_old_report(self):
        self.prepare_native()
        old = self.evidence / "ctest.old"
        old.mkdir()
        report = old / "ctest.xml"
        original = b'<testsuite tests="1"><testcase status="run"/></testsuite>'
        report.write_bytes(original)
        (self.source / "main.c").write_text("this is an intentional compiler error\n")
        result = self.published("# cmake-build:")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("CTest report:", result.stdout)
        self.assertEqual([report], self.reports())
        self.assertEqual(original, report.read_bytes())

    def test_preset_compile_only_needs_no_test_preset_or_python(self):
        self.prepare_native(register_tests=False)
        output = self.source / "out" / "compile-only preset"
        (self.source / "CMakePresets.json").write_text(json.dumps({
            "version": 3,
            "configurePresets": [{"name": "native", "generator": "Unix Makefiles",
                                  "binaryDir": str(output),
                                  "cacheVariables": {"CMAKE_BUILD_TYPE": "Release",
                                                     "CMAKE_C_COMPILER": shutil.which("cc")}}],
            "buildPresets": [{"name": "compile", "configurePreset": "native"}],
        }))
        tool_path = self.root / "build-tools-without-python"
        tool_path.mkdir()
        for name in ("bash", "cmake", "make", "gmake", "cc", "as", "ld", "ar", "ranlib"):
            actual = shutil.which(name)
            if actual:
                (tool_path / name).symlink_to(actual)
        self.assertIsNone(shutil.which("python3", path=str(tool_path)))
        environment = dict(self.environment, PATH=str(tool_path), ADK_BUILD_MODE="preset",
                           ADK_CONFIGURE_PRESET="native", ADK_BUILD_PRESET="compile",
                           ADK_TEST_BACKEND="compile-only")
        for name in ("ADK_TEST_PRESET", "ADK_EVIDENCE_DIR"):
            environment.pop(name)
        result = run_example("set -x\n" + bash_example(CMAKE, "# cmake-build:"), self.source,
                             environment=environment, label="CMake/preset/compile-only/no-python")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("target tests: not-run", result.stdout)
        self.assertTrue((output / "firmware.elf").is_file())
        self.assertEqual([], self.reports())

    def test_hil_collection_preserves_skip_evidence_without_claiming_qualification(self):
        self.prepare_native(register_tests=False, extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'))
        built = self.published("# cmake-build:", ADK_TEST_BACKEND="compile-only")
        self.assertEqual(0, built.returncode, built.stdout + built.stderr)
        result = run_example(bash_example(HIL, "# hil-sil-ctest:"), self.source,
                             environment=self.environment, label="SIL/report-collection")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report, = self.reports()
        self.assertIn(str(report), result.stdout)
        self.assertEqual("notrun", ET.parse(report).getroot().find("testcase").get("status"))
        qualification = (ROOT / HIL).read_text()
        for marker in ("不自动判整项通过", "零实际 pass", "混合 pass/skip 为 partial", "缺必跑项 blocked"):
            self.assertIn(marker, qualification)


class CtestReportReaderTests(unittest.TestCase):
    def test_published_reader_rejects_missing_malformed_unknown_and_failure_results(self):
        block = bash_example(CMAKE, "# cmake-build:")
        reader, = re.findall(r"python3 - \"\$report\" <<'PY'\n(.*?)\nPY", block, re.S)
        passing = '<testcase name="passing" status="run"/>'
        skipped = '<testcase name="skipped" status="notrun"><skipped/></testcase>'
        disabled = '<testcase name="disabled" status="disabled"/>'
        cases = [
            (f'<testsuite tests="1">{passing}</testsuite>', True, "status=pass passed=1"),
            (f'<testsuite tests="3">{passing}{skipped}{disabled}</testsuite>', True,
             "status=partial passed=1 selected=3 skipped=1 disabled=1"),
            (f'<testsuite tests="1">{skipped}</testsuite>', False, "passed=0"),
            (f'<testsuite tests="1">{disabled}</testsuite>', False, "passed=0"),
            ('<testsuite tests="0"/>', False, "passed=0"),
            (f'<other tests="1">{passing}</other>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase/></testsuite>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase status="unknown"/></testsuite>', False,
             "invalid CTest report"),
            (f'<testsuite tests="99">{passing}</testsuite>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase status="fail"><failure/></testcase></testsuite>',
             False, "CTest failures in report"),
            (f'<testsuite tests="2">{passing}<testcase status="run"><error/></testcase></testsuite>',
             False, "CTest failures in report"),
            (f'<testsuite tests="2">{passing}<testcase status="run"><skipped/></testcase></testsuite>',
             False, "invalid passing status"),
            ("<testsuite", False, "ParseError"),
            ("", False, "ParseError"),
            (None, False, "FileNotFoundError"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for index, (xml, success, expected) in enumerate(cases):
                with self.subTest(index=index):
                    report = Path(directory) / f"report-{index}.xml"
                    if xml is not None:
                        report.write_text(xml)
                    result = subprocess.run([sys.executable, "-c", reader, str(report)],
                                            capture_output=True, text=True, timeout=15)
                    self.assertEqual(success, result.returncode == 0, result.stdout + result.stderr)
                    self.assertIn(expected, result.stdout + result.stderr)


class InterfaceVersionExampleTests(unittest.TestCase):
    def test_compiled_consumer_requires_minor_21_and_async_cancel(self):
        compiler = shutil.which("cc")
        self.assertIsNotNone(compiler, "compile the published C example with a real native compiler")
        blocks = re.findall(r"```c\n(.*?)```", (ROOT / INTERFACE).read_text(), re.S)
        code, = [block for block in blocks if "iface_version_compatible(" in block]
        # Literal vectors derive from the consumer contract, not the implementation macros.
        vectors = [(0x0000, 1, 0), (0x01ff, 1, 0), (0x0200, 1, 0), (0x0201, 1, 1),
                   (0x0202, 1, 1), (0x02ff, 1, 1), (0x0300, 1, 0), (0xffff, 1, 0),
                   (0x0201, 0, 0), (0x0202, 2, 0), (0x0202, 3, 1)]
        rows = ",\n".join(f"{{{version}, {caps}, {expected}}}" for version, caps, expected in vectors)
        harness = ('\n#include <stdio.h>\n'
                   'int main(void) {\n'
                   '  const struct { uint16_t version; uint32_t caps; bool expected; } cases[] = {\n' + rows +
                   '\n  };\n'
                   '  for (unsigned int i = 0; i < sizeof cases / sizeof cases[0]; ++i) {\n'
                   '    bool actual = iface_version_compatible(cases[i].version, cases[i].caps);\n'
                   '    if (actual != cases[i].expected) {\n'
                   '      fprintf(stderr, "case %u: actual=%d expected=%d\\n", i, actual, cases[i].expected);\n'
                   '      return 1;\n'
                   '    }\n'
                   '  }\n'
                   '  return 0;\n'
                   '}\n')
        with tempfile.TemporaryDirectory() as directory:
            source, executable = Path(directory) / "version.c", Path(directory) / "version-check"
            source.write_text(code + harness)
            compiled = subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                                       str(source), "-o", str(executable)], capture_output=True, text=True, timeout=15)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
