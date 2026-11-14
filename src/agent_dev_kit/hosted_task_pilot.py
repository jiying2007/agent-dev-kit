"""One preregistered experiment; no public CLI registration, grader, or retry loop."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from types import FrameType
from typing import Any

from . import hosted_task_native as native
from .hosted_task_native import (
    PROMPT_SHA,
    TASK_SECONDS,
    command,
    inventory,
    now,
    opencode_config,
    sha,
    write_json,
)

REPOSITORY = "jiying2007/agent-dev-kit"
BRANCH = "refs/heads/experiment/hosted-task-pilot-run-20261114"
BEFORE = "c57f4f8a7983f52257c0587eb85881a006e6dc07"
BASELINE = "7aed1d2545babce16c41dc021ead01c8c324ce07"
LOCAL_NEGATIVE = "6b5a76779320f45422ca4a06dfa394fff85106d352b65e7fbea56da7aa6018ca"
BASE_IMAGE = "docker.io/library/python:3.12-slim-bookworm"
JOB_SECONDS = 26 * 60
PAIR_RESERVE = 2 * (TASK_SECONDS + 100 + 2 * 70) + 60
Mount = tuple[Path, str, bool]
TASK_SHA = "6bc93366986b29af97fe8328f1c338ae90763a235ba917531b803e8df7e6bc44"
CASE_SHA = "a9a6143b2a36c324435c321171ad09925457dd8d7f8209180ff64f1ecebe59e0"
WORK_SHA = "6a6249b2f8df6c2a8cbea872f13319dd42cb07779bea6e204bfd614f19144359"
SKILL_SHA = {
    "baseline": "e0672708e80c0636abaa812fa6be8d81d7b9f062a62e322b505c7f7d07c4e215",
    "candidate": "a21c9d9d2fd3aaf1e759e28c0353139a1fee67c2ea1e790e1fc882a54f0c60d4",
}
SOURCE_SHA = {
    "baseline": "04267d6288de34d97f2774aa016f1c3366f75699a8638d9c57a5875f376dfcc1",
    "candidate": "e013d6e67dc993a3c3a0cf589d6e1c1e3b4534c1a053422c8c1df0c04813dba2",
}
ASSETS = {
    "opencode": (
        "https://github.com/anomalyco/opencode/releases/download/v2.3.0/opencode-linux-x64.tar.gz",
        "fc0f81522aceeabac47693d88389efa2bc517ce74c2c38fd6967819fcc6e4d3b",
    ),
    "ollama": (
        "https://github.com/ollama/ollama/releases/download/v0.40.16/ollama-linux-amd64.tar.zst",
        "87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d",
    ),
}


def trigger_allowed(values: Mapping[str, str]) -> bool:
    return (
        values.get("GITHUB_REPOSITORY") == REPOSITORY
        and values.get("GITHUB_REF") == BRANCH
        and values.get("GITHUB_EVENT_NAME") == "push"
        and values.get("PILOT_EVENT_BEFORE") == BEFORE
        and values.get("GITHUB_RUN_ATTEMPT") == "1"
        and bool(re.fullmatch(r"[0-9a-f]{40}", values.get("GITHUB_SHA", "")))
    )


def cpu_member(name: str) -> bool:
    path = PurePosixPath(name)
    return name == "bin/ollama" or (
        len(path.parts) == 3
        and path.parts[:2] == ("lib", "ollama")
        and (".so" in path.name or path.name == "llama-server" or path.name.endswith(("LICENSE", "NOTICE")))
    )


class HostedPilot:
    def __init__(self, repo: Path, root: Path, job_started: float) -> None:
        self.repo, self.root = repo, root
        self.evidence = root / "evidence"
        self.evidence.mkdir(parents=True)
        self.docker_env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ}
        self.docker_env["DOCKER_CONFIG"] = str(root / "docker-config")
        Path(self.docker_env["DOCKER_CONFIG"]).mkdir()
        self.uid = os.getuid()
        self.image = ""
        self.live: set[str] = set()
        self.sequence = 0
        self.deadline = time.monotonic() + job_started + JOB_SECONDS - time.time()
        self.preparing = True
        self.alarms_enabled = False
        self.cleaning = False
        self.summary: dict[str, Any] = {
            "started_at": now(),
            "status": "preparing",
            "job_started_epoch": job_started,
            "coordinator_deadline_epoch": job_started + JOB_SECONDS,
            "local_negative_sha256": LOCAL_NEGATIVE,
            "model_runs": 0,
            "model_digest": "unavailable",
            "conditions": [],
            "possible_inference": False,
        }

    def remaining(self) -> float:
        return max(0, self.deadline - time.monotonic())

    def host_command(
        self,
        args: Sequence[str],
        label: str,
        timeout: float,
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        check: bool = True,
    ) -> dict[str, Any]:
        budget = timeout if self.cleaning else min(timeout, self.remaining())
        if self.preparing and not self.cleaning:
            budget = min(budget, max(0, self.remaining() - PAIR_RESERVE))
        return command(args, self.evidence / "commands", label, budget, cwd=cwd, env=env, check=check)

    def docker(self, args: Sequence[str], label: str, timeout: float = 30, check: bool = True) -> dict[str, Any]:
        return self.host_command(["docker", *args], label, timeout, env=self.docker_env, check=check)

    def output(self, label: str) -> str:
        return (self.evidence / "commands" / f"{label}.stdout").read_text()

    def prepare_sources(self) -> None:
        assert self.uid >= 1000, "Hosted worker must run as an ordinary user"
        assert trigger_allowed(os.environ), "Unregistered event/ref/before/attempt"
        self.host_command(["git", "rev-parse", "HEAD"], "source-head", 10, cwd=self.repo)
        assert self.output("source-head").strip() == os.environ["GITHUB_SHA"]
        resources: dict[str, Any] = {
            "cpu_count": os.cpu_count(),
            "disk_free_bytes": shutil.disk_usage(self.root).free,
            "meminfo": Path("/proc/meminfo").read_text(),
            "runner": {
                key: os.environ.get(key)
                for key in (
                    "ImageOS",
                    "ImageVersion",
                    "RUNNER_OS",
                    "RUNNER_ARCH",
                    "GITHUB_REPOSITORY",
                    "GITHUB_SHA",
                    "GITHUB_RUN_ID",
                    "GITHUB_RUN_ATTEMPT",
                )
            },
        }
        assert resources["disk_free_bytes"] >= 8 * 1024**3, "Insufficient free task storage"
        match = re.search(r"MemAvailable:\s+(\d+)", resources["meminfo"])
        assert match is not None
        available = int(match[1])
        assert available >= 8 * 1024**2 and resources["cpu_count"] >= 4
        write_json(self.evidence / "resources.json", resources)
        shutil.copyfile(native.__file__, self.root / "run-pilot.py")
        assert sha(Path(native.__file__)) == sha(self.root / "run-pilot.py")
        write_json(
            self.evidence / "native-module.json",
            {
                "source": "src/agent_dev_kit/hosted_task_native.py",
                "source_sha256": sha(Path(native.__file__)),
                "mounted_copy_sha256": sha(self.root / "run-pilot.py"),
            },
        )
        for condition, commit in (("baseline", BASELINE), ("candidate", BEFORE)):
            source = self.root / "sources" / condition
            source.mkdir(parents=True)
            archive = self.root / f"{condition}-source.tar"
            self.host_command(
                ["git", "archive", "--format=tar", "--output", str(archive), commit],
                f"{condition}-source",
                30,
                cwd=self.repo,
            )
            with tarfile.open(archive) as contents:
                contents.extractall(source, filter="data")
            assert sha(source / "skills/adk-adr-writer/SKILL.md") == SOURCE_SHA[condition]
            env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ}
            env["ADK_PYTHON_BIN"] = sys.executable
            self.host_command(
                [
                    "bash",
                    "scripts/devkit.sh",
                    "export",
                    "--target",
                    "opencode",
                    "--profile",
                    "core",
                    "--asset-kind",
                    "skill",
                    "--out",
                    str(self.root / "exports" / condition),
                    "--summary-json",
                ],
                f"{condition}-export",
                60,
                cwd=source,
                env=env,
            )
            target = self.root / condition
            selected = self.root / "exports" / condition / "opencode/skills/adk-adr-writer"
            assert inventory(selected) == {
                "SKILL.md": {"sha256": SKILL_SHA[condition], "bytes": (selected / "SKILL.md").stat().st_size}
            }
            shutil.copytree(selected, target / "skills/adk-adr-writer")
            fixture = self.root / "sources/candidate/tests/fixtures/skill_execution_tasks/targeted-document-edit"
            if condition == "baseline":
                continue
            assert sha(fixture / "task.md") == TASK_SHA and sha(fixture / "case.json") == CASE_SHA
            assert sha(fixture / "initial/docs/ADR-021.md") == WORK_SHA
            prompt = (fixture / "task.md").read_bytes() + "\n请使用 `adk-adr-writer` Skill 完成上述任务。\n".encode()
            assert hashlib.sha256(prompt).hexdigest() == PROMPT_SHA
            for name in ("baseline", "candidate"):
                target = self.root / name
                shutil.copytree(fixture / "initial", target / "work")
                for folder in ("input", "config", "records", "preflight", "recovery"):
                    (target / folder).mkdir(parents=True)
                (target / "input/prompt.txt").write_bytes(prompt)
                write_json(target / "config/opencode.json", opencode_config())
        inputs = {
            name: {
                "source_commit": BASELINE if name == "baseline" else BEFORE,
                "work": inventory(self.root / name / "work"),
                "skills": inventory(self.root / name / "skills"),
                "input": inventory(self.root / name / "input"),
                "config": inventory(self.root / name / "config"),
                "references": [],
            }
            for name in ("baseline", "candidate")
        }
        write_json(
            self.evidence / "frozen-inputs.json",
            {"task_sha256": TASK_SHA, "case_sha256": CASE_SHA, "prompt_sha256": PROMPT_SHA, "conditions": inputs},
        )

    def prepare_tools(self) -> None:
        for name, (url, expected) in ASSETS.items():
            archive = self.root / (name + (".tar.gz" if name == "opencode" else ".tar.zst"))
            self.host_command(
                [
                    "curl",
                    "--disable",
                    "--fail",
                    "--location",
                    "--proto",
                    "=https",
                    "--tlsv1.2",
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    "240",
                    "--retry",
                    "0",
                    "--output",
                    str(archive),
                    url,
                ],
                name + "-download",
                250,
                env=self.docker_env,
            )
            assert sha(archive) == expected, f"{name} archive checksum mismatch"
            destination = self.root / "tools" / name
            destination.mkdir(parents=True)
            selected: list[str] = []
            if name == "opencode":
                with tarfile.open(archive) as contents:
                    for item in contents:
                        if item.name.lstrip("./") == "opencode" and item.isfile():
                            contents.extract(item, destination, filter="data")
                            selected.append(item.name)
            else:
                decompressor = subprocess.Popen(
                    ["zstd", "--decompress", "--stdout", str(archive)], stdout=subprocess.PIPE
                )
                assert decompressor.stdout is not None
                try:
                    with tarfile.open(fileobj=decompressor.stdout, mode="r|") as contents:
                        for item in contents:
                            if cpu_member(item.name):
                                contents.extract(item, destination, filter="data")
                                selected.append(item.name)
                finally:
                    decompressor.stdout.close()
                    assert decompressor.wait(timeout=20) == 0
                assert "bin/ollama" in selected and "lib/ollama/llama-server" in selected
            write_json(
                self.evidence / f"{name}-asset.json",
                {
                    "url": url,
                    "archive_sha256": expected,
                    "archive_bytes": archive.stat().st_size,
                    "extracted_members": selected,
                },
            )
            archive.unlink()  # Only the task-owned, already-verified download.

    def prepare_image(self) -> None:
        self.docker(["version", "--format", "{{json .}}"], "docker-version")
        self.docker(["pull", "--platform", "linux/amd64", BASE_IMAGE], "base-pull", 240)
        self.docker(["image", "inspect", BASE_IMAGE], "base-inspect")
        base = json.loads(self.output("base-inspect"))[0]
        assert base["Architecture"] == "amd64" and base["Os"] == "linux"
        references = [ref for ref in base["RepoDigests"] if ref.split("@")[0] in ("python", "docker.io/library/python")]
        assert len(references) == 1
        reference = references[0]
        self.docker(["buildx", "imagetools", "inspect", "--raw", reference], "base-manifest", 30)
        manifest = json.loads(self.output("base-manifest"))
        if "manifests" in manifest:
            platforms = [
                item["digest"]
                for item in manifest["manifests"]
                if item.get("platform", {}).get("os") == "linux"
                and item.get("platform", {}).get("architecture") == "amd64"
            ]
            assert len(platforms) == 1
            platform_digest = platforms[0]
        else:
            platform_digest = reference.split("@", 1)[1]
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", platform_digest)
        pinned = "docker.io/library/python@" + platform_digest
        self.docker(["pull", "--platform", "linux/amd64", pinned], "platform-pull", 120)
        self.docker(["image", "inspect", pinned], "platform-inspect")
        pinned_image = json.loads(self.output("platform-inspect"))[0]
        assert (
            pinned_image["Id"] == base["Id"]
            and pinned_image["Architecture"] == "amd64"
            and pinned_image["Os"] == "linux"
        )
        build = self.root / "image-build"
        build.mkdir()
        dockerfile = f"""FROM {pinned}
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 passwd && rm -rf /var/lib/apt/lists/* && useradd --create-home --uid {self.uid} --user-group --home-dir /home/pilot pilot && mkdir -p /work /records /config /skills /input /tools /runner /scratch
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1
USER pilot
WORKDIR /work
"""
        (build / "Dockerfile").write_text(dockerfile)
        shutil.copyfile(build / "Dockerfile", self.evidence / "Dockerfile")
        tag = "adk-hosted-pilot:" + os.environ["GITHUB_RUN_ID"]
        self.docker(
            ["build", "--platform", "linux/amd64", "--network", "default", "--tag", tag, str(build)], "image-build", 240
        )
        self.docker(["image", "inspect", tag], "image-inspect")
        final = json.loads(self.output("image-inspect"))[0]
        assert final["Architecture"] == "amd64" and final["Os"] == "linux" and final["Config"]["User"] == "pilot"
        self.image = final["Id"]
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", self.image)
        write_json(
            self.evidence / "image-identity.json",
            {
                "base_tag": BASE_IMAGE,
                "base_repository_digest": reference,
                "amd64_manifest_digest": platform_digest,
                "base_image_id": base["Id"],
                "final_image_id": self.image,
                "dockerfile_sha256": sha(build / "Dockerfile"),
                "frozen_at": now(),
            },
        )

    def container(
        self, mode: str, label: str, mounts: list[Mount], budget: float, network: str = "none"
    ) -> dict[str, Any]:
        self.sequence += 1
        name = f"adk-pilot-{os.environ['GITHUB_RUN_ID']}-{self.sequence}"
        args = [
            "create",
            "--name",
            name,
            "--init",
            "--network",
            network,
            "--ipc",
            "private",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "256",
            "--cpus",
            "4",
            "--memory",
            "8g",
            "--stop-timeout",
            "0",
        ]
        for target, size in (("/home/pilot", "16m"), ("/tmp", "256m"), ("/scratch", "512m")):
            args += ["--tmpfs", f"{target}:rw,nosuid,nodev,size={size},uid={self.uid},gid={self.uid},mode=0700"]
        for source, target, readonly in mounts:
            assert source.resolve().is_relative_to(self.root.resolve())
            args += ["--mount", native.mount_spec(source, target, readonly)]
        args += [self.image, "python3", "/runner/run-pilot.py", "--inside", mode]
        self.live.add(name)
        self.docker(args, label + "-create", 10)
        identity = self.output(label + "-create").strip()
        assert re.fullmatch(r"[0-9a-f]{64}", identity)
        self.live.add(identity)
        self.live.remove(name)
        self.docker(["inspect", identity], label + "-created", 10)
        created = json.loads(self.output(label + "-created"))[0]
        native.validate_container(created, mounts, self.image, network, self.uid)
        started = time.monotonic()
        self.docker(["start", identity], label + "-start", min(10, budget))
        wait = self.docker(
            ["wait", identity], label + "-wait", max(0.1, budget - (time.monotonic() - started)), check=False
        )
        timed_out = wait["timed_out"]
        if timed_out:
            self.docker(["kill", "--signal", "KILL", identity], label + "-deadline-kill", 10, check=False)
            self.docker(["wait", identity], label + "-after-kill", 10, check=False)
        self.docker(["inspect", identity], label + "-stopped", 10)
        stopped = json.loads(self.output(label + "-stopped"))[0]
        assert stopped["State"]["Running"] is False, "Container termination was not established"
        self.docker(["logs", "--timestamps", identity], label + "-container-log", 10, check=False)
        result = {
            "label": label,
            "mode": mode,
            "container_id": identity,
            "image_id": self.image,
            "network": network,
            "budget_seconds": budget,
            "timed_out": timed_out,
            "state": stopped["State"],
            "observed_terminated": True,
            "finished_observation": now(),
        }
        state = stopped["State"]
        result["actual_container_seconds"] = (
            dt.datetime.fromisoformat(state["FinishedAt"].replace("Z", "+00:00"))
            - dt.datetime.fromisoformat(state["StartedAt"].replace("Z", "+00:00"))
        ).total_seconds()
        result["termination_observation_seconds"] = time.monotonic() - started
        write_json(self.evidence / f"{label}-result.json", result)
        self.docker(["rm", identity], label + "-remove", 10)
        self.live.remove(identity)
        return result

    def mounts(self, condition: str, records: Path, *, recovery: bool = False) -> list[Mount]:
        target = self.root / condition
        tools = self.root / "tools" if not recovery else self.root / "export-tools"
        mounts = [
            (tools, "/tools", True),
            (self.root / "run-pilot.py", "/runner/run-pilot.py", True),
            (target / "config", "/config", True),
            (target / "skills", "/skills", True),
            (target / "input", "/input", True),
            (target / "work", "/work", recovery),
            (records, "/records", False),
        ]
        if not recovery:
            mounts.append((self.root / "models", "/models", True))
        return mounts

    def run(self) -> None:
        self.prepare_sources()
        self.prepare_tools()
        self.prepare_image()
        for path in (self.root / "models", self.root / "prepare-records"):
            path.mkdir()
        prepared = self.container(
            "prepare",
            "model-prepare",
            [
                (self.root / "tools", "/tools", True),
                (self.root / "run-pilot.py", "/runner/run-pilot.py", True),
                (self.root / "models", "/models", False),
                (self.root / "prepare-records", "/records", False),
            ],
            540,
            network="bridge",
        )
        assert prepared["state"]["ExitCode"] == 0 and not prepared["timed_out"], "Model preparation blocked"
        model = json.loads((self.root / "prepare-records/model.json").read_text())
        files = inventory(self.root / "models")
        assert any(
            item["sha256"] == model["digest"].removeprefix("sha256:")
            for path, item in files.items()
            if path.startswith("manifests/")
        )
        self.summary["model_digest"] = model["digest"]
        for condition in ("baseline", "candidate"):
            write_json(self.root / condition / "input/model.json", model)
        write_json(
            self.evidence / "frozen-runtime.json",
            {
                "frozen_at": now(),
                "image": json.loads((self.evidence / "image-identity.json").read_text()),
                "model": model,
                "model_files": files,
                "tool_files": native.tool_inventory(self.root / "tools"),
                "task_order": ["baseline", "candidate"],
                "task_seconds_each": TASK_SECONDS,
                "inference_started": False,
            },
        )
        for condition in ("baseline", "candidate"):
            preflight = self.container(
                "preflight", condition + "-preflight", self.mounts(condition, self.root / condition / "preflight"), 100
            )
            assert preflight["state"]["ExitCode"] == 0 and not preflight["timed_out"], (
                "Offline preflight failed; no condition will run"
            )
            assert sha(self.root / condition / "work/docs/ADR-021.md") == WORK_SHA
        packages = {
            name: sha(self.root / name / "preflight/raw/image-packages.stdout") for name in ("baseline", "candidate")
        }
        assert len(set(packages.values())) == 1, "The two containers have different installed dependencies"
        write_json(
            self.evidence / "frozen-dependencies.json",
            {"image_id": self.image, "inventory_sha256": packages, "frozen_at": now()},
        )
        shutil.copytree(self.root / "tools/opencode", self.root / "export-tools/opencode")
        self.finish_preparation()
        for condition in ("baseline", "candidate"):
            self.run_condition(condition)
        self.summary["status"] = "executed-awaiting-independent-grading"

    def finish_preparation(self) -> None:
        assert self.remaining() >= PAIR_RESERVE, "420-second preparation deadline exhausted; neither task may start"
        self.preparing = False
        if self.alarms_enabled:
            signal.setitimer(signal.ITIMER_REAL, self.remaining())

    def verify_inputs(self, condition: str) -> None:
        frozen = json.loads((self.evidence / "frozen-inputs.json").read_text())["conditions"][condition]
        for folder in ("work", "skills", "config"):
            assert inventory(self.root / condition / folder) == frozen[folder], (
                f"Changed frozen input: {condition}/{folder}"
            )
        assert sha(self.root / condition / "input/prompt.txt") == PROMPT_SHA
        assert sha(self.root / "run-pilot.py") == sha(Path(native.__file__))
        runtime = json.loads((self.evidence / "frozen-runtime.json").read_text())
        assert json.loads((self.root / condition / "input/model.json").read_text()) == runtime["model"]

    def capture_attempt(self, condition: str, attempt: dict[str, Any]) -> None:
        native.capture_attempt(self.root, self.evidence, condition, attempt, not self.live)

    def run_condition(self, condition: str) -> None:
        self.verify_inputs(condition)
        original = self.root / condition / "records"
        assert not (original / "task-start.json").exists()
        attempt: dict[str, Any] = {
            "condition": condition,
            "registered_at": now(),
            "status": "execution-may-start",
            "native_task_cli_attempts": "unavailable-pending-raw-review",
        }
        self.summary["conditions"].append(attempt)
        self.summary.update(possible_inference=True, model_runs="unavailable-pending-raw-review")
        write_json(self.evidence / f"{condition}-attempt.json", attempt)
        try:
            attempt["container_observation"] = self.container(
                "task", condition + "-task", self.mounts(condition, original), TASK_SECONDS
            )
            attempt["status"] = "container-stopped"
        except Exception as error:
            attempt.update(status="execution-or-observation-failed", error=str(error))
            raise
        finally:
            self.capture_attempt(condition, attempt)
        before = {name: inventory(original / name) if (original / name).exists() else {} for name in ("data", "state")}
        write_json(self.evidence / f"{condition}-native-state.json", {"original": before, "export_uses_copy": True})
        recovery = self.root / condition / "recovery"
        for name in ("data", "state"):
            if (original / name).exists():
                shutil.copytree(original / name, recovery / name)
        try:
            attempt["read_only_export"] = self.container(
                "export", condition + "-export", self.mounts(condition, recovery, recovery=True), 100
            )
        finally:
            after = {
                name: inventory(original / name) if (original / name).exists() else {} for name in ("data", "state")
            }
            write_json(
                self.evidence / f"{condition}-native-state-after-export.json",
                {"original": after, "unchanged": before == after},
            )
            assert before == after, "Recovery modified original native state"
            self.capture_attempt(condition, attempt)

    def cleanup(self) -> None:
        self.cleaning = True
        failures: list[str] = []
        for index, identity in enumerate(list(self.live)):
            try:
                self.docker(["kill", "--signal", "KILL", identity], f"cleanup-{index}-kill", 10, check=False)
                self.docker(["inspect", identity], f"cleanup-{index}-inspect", 10)
                state = json.loads(self.output(f"cleanup-{index}-inspect"))[0]["State"]
                assert state["Running"] is False
                self.docker(["rm", identity], f"cleanup-{index}-remove", 10)
                self.live.remove(identity)
            except Exception as error:
                failures.append(str(error))
        self.summary["cleanup"] = {"remaining_containers": sorted(self.live), "failures": failures}
        for attempt in self.summary["conditions"]:
            try:
                self.capture_attempt(attempt["condition"], attempt)
            except Exception as error:
                failures.append(str(error))

    def publish(self) -> None:
        native.publish_evidence(self.root, self.evidence, self.summary)


def stop_coordinator(signum: int, frame: FrameType | None) -> None:
    raise TimeoutError(f"Coordinator deadline or cancellation signal {signum}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    assert args.repo and args.out and trigger_allowed(os.environ)
    root = args.out.resolve()
    assert root.is_relative_to(Path(os.environ["RUNNER_TEMP"]).resolve())
    assert not root.exists(), "The one registered hosted attempt must use a fresh task directory"
    root.mkdir()
    pilot = HostedPilot(args.repo.resolve(), root, float(os.environ["PILOT_JOB_STARTED_EPOCH"]))
    signal.signal(signal.SIGTERM, stop_coordinator)
    signal.signal(signal.SIGINT, stop_coordinator)
    signal.signal(signal.SIGALRM, stop_coordinator)
    try:
        assert pilot.remaining() > 0, "Job preparation used the entire coordinator budget"
        assert pilot.remaining() > PAIR_RESERVE, "Preparation deadline exhausted before coordinator launch"
        pilot.alarms_enabled = True
        signal.setitimer(signal.ITIMER_REAL, pilot.remaining() - PAIR_RESERVE)
        pilot.run()
    except Exception as error:
        pilot.summary.update(status="blocked-or-partial", error=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        pilot.cleanup()
        pilot.publish()
    print(json.dumps(pilot.summary, ensure_ascii=False))
    return 0 if pilot.summary["status"] == "executed-awaiting-independent-grading" and not pilot.live else 1


if __name__ == "__main__":
    raise SystemExit(main())
