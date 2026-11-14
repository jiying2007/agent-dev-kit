"""Contract boundaries, not a substitute for actual Docker/OpenCode qualification."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any
import unittest
from unittest.mock import patch

from agent_dev_kit import hosted_task_native as native
from agent_dev_kit import hosted_task_pilot as pilot


@contextmanager
def experiment() -> Iterator[pilot.HostedPilot]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        instance = pilot.HostedPilot(root, root, time.time())
        instance.uid = 1001
        instance.image = "sha256:" + "a" * 64
        yield instance


def inspected(mounts: list[pilot.Mount], image: str, uid: int) -> dict[str, Any]:
    """A synthetic daemon observation: tests rejection, never Docker compatibility."""
    return {
        "Mounts": [{"Type": "bind", "Destination": dest, "Source": str(src), "RW": not ro} for src, dest, ro in mounts],
        "Image": image,
        "Config": {"User": "pilot", "Env": ["PATH=/usr/local/bin:/usr/bin:/bin", "LANG=C.UTF-8"]},
        "HostConfig": {
            "NetworkMode": "none",
            "ReadonlyRootfs": True,
            "Privileged": False,
            "CapDrop": ["ALL"],
            "CapAdd": None,
            "SecurityOpt": ["no-new-privileges"],
            "PidMode": "",
            "IpcMode": "private",
            "Binds": None,
            "PidsLimit": 256,
            "Memory": 8 * 1024**3,
            "NanoCpus": 4 * 10**9,
            "Tmpfs": {
                target: f"rw,nosuid,nodev,size={size},uid={uid},gid={uid},mode=0700"
                for target, size in (("/home/pilot", "16m"), ("/tmp", "256m"), ("/scratch", "512m"))
            },
        },
    }


class TriggerTests(unittest.TestCase):
    def test_only_exact_first_registered_push_is_allowed(self) -> None:
        event = {
            "GITHUB_REPOSITORY": "jiying2007/agent-dev-kit",
            "GITHUB_REF": "refs/heads/experiment/hosted-task-pilot-run-20261114",
            "GITHUB_EVENT_NAME": "push",
            "PILOT_EVENT_BEFORE": "c57f4f8a7983f52257c0587eb85881a006e6dc07",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": "b" * 40,
        }
        self.assertTrue(pilot.trigger_allowed(event))
        for key, forbidden in (
            ("GITHUB_REPOSITORY", "someone/agent-dev-kit"),
            ("GITHUB_REF", "refs/heads/main"),
            ("GITHUB_EVENT_NAME", "workflow_dispatch"),
            ("PILOT_EVENT_BEFORE", "0" * 40),
            ("PILOT_EVENT_BEFORE", "b" * 40),
            ("GITHUB_RUN_ATTEMPT", "2"),
            ("GITHUB_SHA", "main"),
        ):
            with self.subTest(key=key, forbidden=forbidden):
                self.assertFalse(pilot.trigger_allowed({**event, key: forbidden}))

    def test_workflow_has_no_dispatch_secret_or_write_permission(self) -> None:
        import yaml

        path = Path(__file__).resolve().parents[1] / ".github/workflows/opencode-task-pilot-once.yml"
        workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"push"})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["pilot"]
        self.assertEqual(job["timeout-minutes"], "30")
        self.assertIn("PILOT_JOB_STARTED_EPOCH", job["steps"][0]["run"])
        self.assertNotIn("secrets.", path.read_text())
        self.assertEqual(job["steps"][-1]["with"]["include-hidden-files"], "true")


class IsolationTests(unittest.TestCase):
    def test_mount_rejects_parent_symlink_relative_path_and_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").mkdir()
            (root / "real/file").write_text("public")
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            (root / "comma,file").write_text("public")
            self.assertTrue(native.mount_spec(root / "real/file", "/input/file").endswith(",readonly"))
            for source in (root / "link/file", Path("relative"), root / "comma,file"):
                with self.subTest(source=str(source)), self.assertRaises(RuntimeError):
                    native.mount_spec(source, "/input/file")

    def test_archive_selection_excludes_gpu_and_traversal(self) -> None:
        self.assertTrue(pilot.cpu_member("lib/ollama/libggml-cpu-x64.so"))
        self.assertTrue(pilot.cpu_member("bin/ollama"))
        for path in (
            "../../bin/ollama",
            "/bin/ollama",
            "lib/ollama/cuda_v12/libggml.so",
            "lib/ollama/../libggml.so",
            "lib/ollama/vulkan/libvulkan.so",
            "lib/ollama/id_ed25519",
        ):
            self.assertFalse(pilot.cpu_member(path), path)

    def test_incomplete_or_weakened_daemon_observation_is_rejected(self) -> None:
        mounts = [(Path("/task/work"), "/work", False)]
        original = inspected(mounts, "fixed-image", 1001)
        native.validate_container(original, mounts, "fixed-image", "none", 1001)
        variants = []
        for key, value in (
            ("NetworkMode", "bridge"),
            ("ReadonlyRootfs", False),
            ("Privileged", True),
            ("CapAdd", ["SYS_ADMIN"]),
            ("PidMode", "host"),
            ("IpcMode", "host"),
            ("Tmpfs", {}),
        ):
            altered = copy.deepcopy(original)
            altered["HostConfig"][key] = value
            variants.append(altered)
        altered = copy.deepcopy(original)
        altered["Mounts"].append(
            {"Type": "bind", "Source": "/var/run/docker.sock", "Destination": "/var/run/docker.sock", "RW": True}
        )
        variants.append(altered)
        altered = copy.deepcopy(original)
        altered["Config"]["Env"].append("GITHUB_TOKEN=synthetic-forbidden-variable")
        variants.append(altered)
        altered = copy.deepcopy(original)
        del altered["HostConfig"]["Privileged"]
        variants.append(altered)
        for index, altered in enumerate(variants):
            with self.subTest(index=index), self.assertRaises((AssertionError, KeyError)):
                native.validate_container(altered, mounts, "fixed-image", "none", 1001)

    def test_recovery_has_no_models_and_work_is_read_only(self) -> None:
        with experiment() as run:
            normal = run.mounts("baseline", run.root / "baseline/records")
            recovery = run.mounts("baseline", run.root / "baseline/recovery", recovery=True)
            self.assertIn((run.root / "models", "/models", True), normal)
            self.assertFalse(any(target == "/models" for _, target, _ in recovery))
            self.assertIn((run.root / "baseline/work", "/work", True), recovery)
            self.assertIn((run.root / "export-tools", "/tools", True), recovery)

    def test_changed_frozen_work_skill_config_or_model_input_is_rejected(self) -> None:
        with experiment() as run:
            target = run.root / "baseline"
            for folder in ("work", "skills", "config", "input"):
                (target / folder).mkdir(parents=True)
            for folder in ("work", "skills", "config"):
                (target / folder / "fixture").write_text("original public fixture")
            task = Path(__file__).parent / "fixtures/skill_execution_tasks/targeted-document-edit/task.md"
            (target / "input/prompt.txt").write_bytes(
                task.read_bytes() + "\n请使用 `adk-adr-writer` Skill 完成上述任务。\n".encode()
            )
            (run.root / "run-pilot.py").write_bytes(Path(native.__file__).read_bytes())
            model = {"digest": "synthetic-unit-test-identity"}
            native.write_json(target / "input/model.json", model)
            native.write_json(run.evidence / "frozen-runtime.json", {"model": model})
            native.write_json(
                run.evidence / "frozen-inputs.json",
                {
                    "conditions": {
                        "baseline": {
                            folder: native.inventory(target / folder) for folder in ("work", "skills", "config")
                        }
                    }
                },
            )
            run.verify_inputs("baseline")
            for folder in ("work", "skills", "config"):
                changed = target / folder / "fixture"
                changed.write_text("changed after preflight")
                with self.subTest(folder=folder), self.assertRaises(AssertionError):
                    run.verify_inputs("baseline")
                changed.write_text("original public fixture")
            native.write_json(target / "input/model.json", {"digest": "changed-unit-test-identity"})
            with self.assertRaises(AssertionError):
                run.verify_inputs("baseline")


class DeadlineTests(unittest.TestCase):
    def test_expired_preparation_never_launches_a_child(self) -> None:
        with experiment() as run:
            self.assertEqual(pilot.JOB_SECONDS - pilot.PAIR_RESERVE, 420)
            run.deadline = time.monotonic() + pilot.PAIR_RESERVE - 1
            witness = run.root / "forbidden-child"
            with self.assertRaises(RuntimeError):
                run.host_command(
                    [sys.executable, "-c", f"from pathlib import Path; Path({str(witness)!r}).touch()"], "expired", 10
                )
            self.assertFalse(witness.exists())
            with self.assertRaises(AssertionError):
                run.finish_preparation()
            self.assertTrue(run.preparing)
            self.assertEqual(run.summary["model_runs"], 0)

    def test_preparation_time_is_charged_from_first_workflow_step(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = pilot.HostedPilot(Path(temporary), Path(temporary), time.time() - 425)
            with self.assertRaises(AssertionError):
                run.finish_preparation()
            self.assertLess(run.remaining(), pilot.PAIR_RESERVE)

    def test_real_timeout_kills_process_group_and_preserves_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            witness, pidfile = root / "descendant-survived", root / "child-pid"
            child = f"import time; from pathlib import Path; time.sleep(0.7); Path({str(witness)!r}).touch(); time.sleep(30)"
            parent = f"import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c',{child!r}]); Path({str(pidfile)!r}).write_text(str(p.pid)); time.sleep(30)"
            result = native.command([sys.executable, "-c", parent], root / "raw", "timeout", 0.25, check=False)
            self.assertTrue(result["timed_out"])
            self.assertEqual(result["exit_code"], -9)
            self.assertTrue(pidfile.exists(), "The descendant must actually start for this test")
            time.sleep(0.8)
            self.assertFalse(witness.exists(), "Killing only the client/parent would leave this witness")
            state = Path("/proc") / pidfile.read_text() / "stat"
            if state.exists():
                self.assertEqual(state.read_text().split()[2], "Z")
            receipt = json.loads((root / "raw/timeout.json").read_text())
            self.assertEqual(receipt["exit_code"], -9)
            self.assertGreater(receipt["duration_seconds"], 0.2)


class PartialExecutionTests(unittest.TestCase):
    def test_post_start_inspect_or_remove_failure_cannot_report_zero_runs(self) -> None:
        for failing_suffix in ("-stopped", "-remove"):
            with self.subTest(failing_suffix=failing_suffix), experiment() as run:
                for folder in (
                    "tools",
                    "models",
                    "baseline/config",
                    "baseline/skills",
                    "baseline/input",
                    "baseline/work",
                    "baseline/records",
                ):
                    (run.root / folder).mkdir(parents=True)
                (run.root / "run-pilot.py").write_text("test-only")
                run.preparing = False
                created = inspected(run.mounts("baseline", run.root / "baseline/records"), run.image, run.uid)
                identity = "f" * 64

                def fake_docker(
                    args: Sequence[str], label: str, timeout: float = 30, check: bool = True
                ) -> dict[str, Any]:
                    if label.endswith(failing_suffix):
                        raise RuntimeError("injected daemon observation failure after task start")
                    commands = run.evidence / "commands"
                    commands.mkdir(exist_ok=True)
                    stdout = commands / f"{label}.stdout"
                    if args[0] == "create":
                        stdout.write_text(identity)
                    elif label.endswith("-created"):
                        stdout.write_text(json.dumps([created]))
                    elif args[0] == "start":
                        native.write_json(
                            run.root / "baseline/records/task-start.json",
                            {"task_cli_attempts": 1, "model_inference_observed": "unavailable"},
                        )
                    elif label.endswith("-stopped"):
                        stdout.write_text(
                            json.dumps(
                                [
                                    {
                                        "State": {
                                            "Running": False,
                                            "ExitCode": 0,
                                            "StartedAt": "2026-11-14T00:00:00Z",
                                            "FinishedAt": "2026-11-14T00:00:01Z",
                                        }
                                    }
                                ]
                            )
                        )
                    return {"exit_code": 0, "timed_out": False}

                with (
                    patch.dict(os.environ, {"GITHUB_RUN_ID": "synthetic-unit-test"}),
                    patch.object(run, "verify_inputs"),
                    patch.object(run, "docker", side_effect=fake_docker),
                ):
                    with self.assertRaisesRegex(RuntimeError, "injected daemon"):
                        run.run_condition("baseline")
                run.publish()
                summary = json.loads((run.root / "published/evidence/summary.json").read_text())
                self.assertNotEqual(summary["model_runs"], 0)
                self.assertNotEqual(summary["actual_skill_load"], "not-run")
                self.assertEqual(len(summary["conditions"]), 1)
                self.assertEqual(summary["conditions"][0]["task-start.json"]["task_cli_attempts"], 1)
                self.assertEqual(summary["conditions"][0]["status"], "execution-or-observation-failed")


class EvidenceTests(unittest.TestCase):
    def test_no_attempt_is_explicitly_not_run_for_both_conditions(self) -> None:
        with experiment() as run:
            run.publish()
            summary = json.loads((run.root / "published/evidence/summary.json").read_text())
            self.assertEqual(summary["model_runs"], 0)
            self.assertEqual(summary["model_digest"], "unavailable")
            self.assertEqual(summary["not_started_conditions"], ["baseline", "candidate"])
            self.assertEqual(summary["actual_skill_load"], "not-run")

    def test_allowlist_excludes_private_state_and_labels_identity_redaction(self) -> None:
        with experiment() as run:
            for folder in (
                "home",
                "models",
                "sources",
                "baseline/records/data",
                "baseline/records/state",
                "baseline/work",
                "baseline/records/raw",
            ):
                (run.root / folder).mkdir(parents=True)
                (run.root / folder / "excluded.txt").write_text("synthetic private state")
            original = run.root / "baseline/records/raw/ollama-server.stdout"
            (run.root / "baseline/work/.extra-file").write_text("unexpected public output for independent grader")
            original.write_text("server startup\nYour new public key is:\nssh-ed25519 " + "A" * 60 + "\nhealthy\n")
            secret = run.root / "baseline/records/raw/credentials.stdout"
            secret.write_text("ghp_" + "A" * 30)
            raw_hash = native.sha(original)
            run.publish()
            manifest = json.loads((run.root / "published/manifest.json").read_text())
            paths = [item["path"] for item in manifest["files"]]
            self.assertIn("baseline/work/.extra-file", paths)
            self.assertFalse(
                any(
                    "/data/" in path or "/state/" in path or path.startswith(("home/", "models/", "sources/"))
                    for path in paths
                )
            )
            entry = next(item for item in manifest["files"] if item["path"].endswith("ollama-server.sanitized.log"))
            self.assertFalse(entry["byte_identical_raw"])
            self.assertEqual(entry["raw_sha256"], raw_hash)
            self.assertEqual(entry["removed_identity_line_numbers"], [2, 3])
            self.assertEqual(native.sha(original), raw_hash)
            self.assertEqual(len(manifest["excluded_sensitive_files"]), 1)
            limits = json.loads((run.root / "published/publication-limits.json").read_text())
            self.assertEqual(limits["coverage"], "unavailable")


if __name__ == "__main__":
    unittest.main()
