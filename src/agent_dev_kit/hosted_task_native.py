"""Container-local official CLI execution and raw recording for one experiment."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import datetime as dt
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

MODEL = "qwen3:1.7b"


TASK_SECONDS = 300


MODEL_URL = "http://127.0.0.1:11439"


PROMPT_SHA = "5d70cb0689e244f868c32fb92600a3d96a0945fc4724be3d924952a2e8b252db"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(root: Path) -> dict[str, dict[str, str | int]]:
    result: dict[str, dict[str, str | int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Unexpected symlink in data: {path}")
        if path.is_file():
            result[str(path.relative_to(root))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    return result


def tool_inventory(root: Path) -> dict[str, dict[str, str | int]]:
    result: dict[str, dict[str, str | int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            assert path.resolve().is_relative_to(root.resolve()), "Official tool link escaped its collection"
            item: dict[str, str | int] = {"sha256": sha(path), "bytes": path.stat().st_size}
            if path.is_symlink():
                item["symlink_target"] = os.readlink(path)
            result[str(path.relative_to(root))] = item
    return result


def command(
    args: Sequence[str],
    directory: Path,
    label: str,
    timeout: float,
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if timeout <= 0:
        raise RuntimeError("Command budget exhausted before launch")
    directory.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "argv": list(args),
        "started_at": now(),
        "timeout_seconds": timeout,
        "timed_out": False,
        "launched": False,
    }
    started = time.monotonic()
    process: subprocess.Popen[bytes] | None = None
    try:
        with (directory / f"{label}.stdout").open("wb") as stdout, (directory / f"{label}.stderr").open("wb") as stderr:
            process = subprocess.Popen(args, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            record.update(launched=True, pid=process.pid)
            write_json(directory / f"{label}.json", record)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
            finally:
                # Also clean descendants on cancellation; the CLI may have forked.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
    finally:
        record.update(
            exit_code=process.returncode if process else None,
            ended_at=now(),
            duration_seconds=time.monotonic() - started,
        )
        write_json(directory / f"{label}.json", record)
    if check and record["exit_code"] != 0:
        raise RuntimeError(f"{label} failed ({record['exit_code']}); see preserved command output")
    return record


def opencode_config() -> dict[str, Any]:
    permissions = [{"action": "*", "resource": "*", "effect": "deny"}]
    for action, resources in {
        "read": [".", "docs", "docs/ADR-021.md", "/skills/adk-adr-writer/*"],
        "external_directory": ["/skills/adk-adr-writer/*"],
        "edit": ["docs/ADR-021.md"],
        "glob": ["*"],
        "grep": ["*"],
        "skill": ["adk-adr-writer"],
    }.items():
        permissions.extend({"action": action, "resource": item, "effect": "allow"} for item in resources)
    policies = [
        {"action": action, "resource": "*", "effect": "deny"}
        for action in (
            "provider.use",
            "integration.connect",
            "integration.use",
            "mcp.use",
            "plugin.use",
            "websearch.use",
            "skill.use",
            "tool.use",
        )
    ]
    policies += [
        {"action": action, "resource": resource, "effect": "allow"}
        for action, resource in (
            ("provider.use", "ollama"),
            ("integration.use", "ollama"),
            ("skill.use", "adk-adr-writer"),
            *(
                ("tool.use", item)
                for item in (
                    "read:*",
                    "edit:*",
                    "glob:*",
                    "grep:*",
                    "skill:adk-adr-writer",
                    "external_directory:/skills/adk-adr-writer/*",
                )
            ),
        )
    ]
    return {
        "$schema": "https://opencode.ai/v2/config.json",
        "model": "ollama/qwen3:1.7b",
        "default_agent": "build",
        "update": "disable",
        "share": "disabled",
        "warming": False,
        "snapshots": False,
        "formatter": False,
        "lsp": False,
        "compaction": {"auto": False},
        "instructions": [],
        "plugins": [],
        "mcp": {},
        "skills": ["/skills"],
        "permissions": permissions,
        "policies": policies,
        "agents": {
            "build": {"model": "ollama/qwen3:1.7b", "steps": 20},
            **{name: {"disabled": True} for name in ("general", "explore", "title", "summary", "compaction")},
        },
        "providers": {
            "ollama": {
                "name": "Task-local Ollama",
                "package": "@opencode/ai/providers/openai-compatible",
                "env": [],
                "settings": {"baseURL": MODEL_URL + "/v1", "apiKey": False, "provider": "ollama"},
                "models": {
                    MODEL: {
                        "name": MODEL,
                        "capabilities": {"tools": True, "input": ["text"], "output": ["text"], "temperature": True},
                        "limit": {"context": 16384, "output": 4096},
                        "body": {"temperature": 0, "seed": 20261114},
                    }
                },
            }
        },
        "experimental": {"subagent_depth": 0},
    }


def api(route: str, body: dict[str, Any] | None = None, timeout: float = 10) -> dict[str, Any]:
    request = urllib.request.Request(
        MODEL_URL + route,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result: dict[str, Any] = json.load(response)
        return result


def native_environment() -> dict[str, str]:
    # HOME is supplied by Docker for the image's real user; never override it.
    result = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
    result.update(
        {
            "XDG_CONFIG_HOME": "/scratch/config",
            "XDG_DATA_HOME": "/records/data",
            "XDG_STATE_HOME": "/records/state",
            "XDG_CACHE_HOME": "/scratch/cache",
            "TMPDIR": "/tmp",
            "OPENCODE_CONFIG_DIR": "/config",
            "OPENCODE_CONFIG": "/config/opencode.json",
            "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "OPENCODE_DISABLE_FILEWATCHER": "1",
            "OLLAMA_HOST": "127.0.0.1:11439",
            "OLLAMA_MODELS": "/models",
            "OLLAMA_NO_CLOUD": "1",
            "OLLAMA_NOHISTORY": "1",
            "OLLAMA_VULKAN": "0",
            "OLLAMA_CONTEXT_LENGTH": "16384",
            "OLLAMA_NUM_PARALLEL": "1",
            "OLLAMA_MAX_LOADED_MODELS": "1",
            "OLLAMA_KEEP_ALIVE": "5m",
        }
    )
    return result


def assert_offline_layout() -> dict[str, Any]:
    assert os.getuid() != 0 and os.environ.get("HOME") == "/home/pilot"
    assert not any(
        key.startswith(("GITHUB_", "ACTIONS_", "GH_", "AWS_", "OPENAI_", "ANTHROPIC_")) for key in os.environ
    )
    for path in ("/repo", "/case.json", "/github/workspace", "/var/run/docker.sock", "/.git"):
        assert not Path(path).exists(), path
    assert sorted(path.name for path in Path("/sys/class/net").iterdir()) == ["lo"]
    home = Path("/home/pilot")
    assert list(home.iterdir()) == [], "Each container must have a fresh private home"
    (home / "private-home-probe").write_text("task-local")
    (home / "private-home-probe").unlink()
    readonly = {
        path: bool(os.statvfs(path).f_flag & os.ST_RDONLY)
        for path in ("/", "/tools", "/config", "/skills", "/input", "/runner/run-pilot.py")
    }
    assert all(readonly.values()), readonly
    with socket.socket() as connection:
        connection.settimeout(1)
        try:
            connection.connect(("192.0.2.1", 9))
            raise RuntimeError("Unexpected external route in network-none container")
        except OSError as error:
            assert error.errno == errno.ENETUNREACH, error
    for target in (Path("/isolation-write-probe"), Path("/skills/isolation-write-probe")):
        try:
            target.write_text("must fail")
        except OSError as error:
            assert error.errno in (errno.EROFS, errno.EACCES)
        else:
            raise RuntimeError(f"Unexpected write outside work/records: {target}")
    return {
        "uid": os.getuid(),
        "home": os.environ["HOME"],
        "readonly": readonly,
        "interfaces": ["lo"],
        "external_connect_errno": errno.ENETUNREACH,
    }


def mount_spec(source: Path, destination: str, readonly: bool = True) -> str:
    if not source.is_absolute() or source.resolve() != source or "," in str(source):
        raise RuntimeError("Mount source must be a plain absolute task path")
    if not source.exists():
        raise RuntimeError(f"Mount source missing: {source}")
    return f"type=bind,source={source},target={destination}" + (",readonly" if readonly else "")


def capture_attempt(root: Path, evidence: Path, condition: str, attempt: dict[str, Any], stable: bool) -> None:
    records = root / condition / "records"
    for filename in ("task-start.json", "raw/task.json"):
        path = records / filename
        if path.exists():
            attempt[filename] = json.loads(path.read_text())
    proof = evidence / f"{condition}-task-result.json"
    if proof.exists():
        attempt["container_observation"] = json.loads(proof.read_text())
    attempt["work_snapshot_stable"] = stable
    if stable:
        write_json(evidence / f"{condition}-final-work.json", inventory(root / condition / "work"))
    write_json(evidence / f"{condition}-attempt.json", attempt)


def validate_container(
    created: dict[str, Any], mounts: list[tuple[Path, str, bool]], image: str, network: str, uid: int
) -> None:
    expected = {target: (str(source), not readonly) for source, target, readonly in mounts}
    actual = created["Mounts"]
    assert all(item["Type"] in ("bind", "tmpfs") for item in actual), "Unexpected volume mount"
    assert {item["Destination"]: (item["Source"], item["RW"]) for item in actual if item["Type"] == "bind"} == expected
    host = created["HostConfig"]
    assert host["NetworkMode"] == network and host["ReadonlyRootfs"]
    assert not host["Privileged"] and created["Image"] == image and created["Config"]["User"] == "pilot"
    assert host["CapDrop"] == ["ALL"] and host["CapAdd"] in (None, [])
    assert "no-new-privileges" in host["SecurityOpt"]
    assert host["PidMode"] == "" and host["IpcMode"] == "private" and not host.get("Binds")
    assert host["PidsLimit"] == 256 and host["Memory"] == 8 * 1024**3 and host["NanoCpus"] == 4 * 10**9
    expected_tmpfs = {
        target: f"rw,nosuid,nodev,size={size},uid={uid},gid={uid},mode=0700"
        for target, size in (("/home/pilot", "16m"), ("/tmp", "256m"), ("/scratch", "512m"))
    }
    assert host["Tmpfs"] == expected_tmpfs
    assert all(item["Destination"] in expected_tmpfs for item in actual if item["Type"] == "tmpfs")
    assert not any(
        item.split("=", 1)[0].startswith(("GITHUB_", "GH_", "ACTIONS_", "AWS_", "OPENAI_", "ANTHROPIC_"))
        for item in created["Config"]["Env"]
    )


def native_export(records: Path) -> None:
    # This mode has no /models mount or Ollama process and sees read-only /work.
    assert not Path("/models").exists()
    assert bool(os.statvfs("/work").f_flag & os.ST_RDONLY)
    env = native_environment()
    binary = "/tools/opencode/opencode"
    listed = command(
        [binary, "session", "list", "--standalone", "--format", "json"],
        records / "raw",
        "session-list",
        35,
        env=env,
        check=False,
    )
    identities: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("id", "sessionID", "session_id") and isinstance(item, str) and item.startswith("ses"):
                    identities.add(item)
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    if listed["exit_code"] == 0:
        visit(json.loads((records / "raw/session-list.stdout").read_text()))
    result: dict[str, Any] = {"session_ids": sorted(identities), "model_process_started": False}
    if len(identities) == 1:
        identity = next(iter(identities))
        result["export"] = command(
            [binary, "session", "export", "--standalone", identity],
            records / "raw",
            "session-export",
            45,
            env=env,
            check=False,
        )
    else:
        result["export_status"] = "unavailable: session identity not unique"
    write_json(records / "export-result.json", result)


def inside(mode: str) -> None:
    records = Path("/records")
    env = native_environment()
    write_json(records / "environment.json", env)
    if mode == "export":
        assert_offline_layout()
        native_export(records)
        return
    if mode != "prepare":
        write_json(records / "isolation.json", assert_offline_layout())
        assert bool(os.statvfs("/models").f_flag & os.ST_RDONLY)
    assert os.environ.get("HOME") == "/home/pilot" and os.getuid() != 0
    raw = records / "raw"
    raw.mkdir(exist_ok=True)
    server: subprocess.Popen[bytes] | None = None
    try:
        with (raw / "ollama-server.stdout").open("wb") as server_log:
            server = subprocess.Popen(
                ["/tools/ollama/bin/ollama", "serve"], env=env, stdout=server_log, stderr=subprocess.STDOUT
            )
            deadline = time.monotonic() + 12
            while True:
                try:
                    version = api("/api/version", timeout=1)
                    assert version["version"] == "0.40.16", version
                    break
                except (OSError, urllib.error.URLError):
                    if server.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Local Ollama health failed; no repair/retry of this host")
                    time.sleep(0.2)
            write_json(records / "server-version.json", version)
            if mode == "prepare":
                body = {"model": MODEL, "stream": True}
                request = urllib.request.Request(
                    MODEL_URL + "/api/pull",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                )
                write_json(
                    records / "model-pull-command.json",
                    {"url": MODEL_URL + "/api/pull", "body": body, "started_at": now(), "inference": False},
                )
                with (
                    urllib.request.urlopen(request, timeout=480) as response,
                    (raw / "model-pull.jsonl").open("wb") as log,
                ):
                    for line in response:
                        log.write(line)
                        log.flush()
                        item = json.loads(line)
                        if "error" in item:
                            raise RuntimeError(item["error"])
                model = next(item for item in api("/api/tags")["models"] if item["name"] == MODEL)
                assert re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", model["digest"])
                write_json(records / "model.json", model)
                write_json(records / "model-show.json", api("/api/show", {"model": MODEL}))
                return
            expected = json.loads(Path("/input/model.json").read_text())
            actual = next(item for item in api("/api/tags")["models"] if item["name"] == MODEL)
            assert actual["digest"] == expected["digest"]
            write_json(records / "model-identity.json", actual)
            binary = "/tools/opencode/opencode"
            if mode == "preflight":
                command(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"], raw, "image-packages", 10, env=env)
                command([binary, "--version"], raw, "opencode-version", 10, env=env)
                assert (raw / "opencode-version.stdout").read_text().strip() == "opencode v2.3.0"
                libraries = [
                    Path("/tools/opencode/opencode"),
                    Path("/tools/ollama/bin/ollama"),
                    Path("/tools/ollama/lib/ollama/llama-server"),
                ]
                libraries += sorted(Path("/tools/ollama/lib/ollama").glob("*.so*"))
                for index, library in enumerate(libraries):
                    command(["ldd", str(library)], raw, f"ldd-{index}", 5, env=env)
                    assert "not found" not in (raw / f"ldd-{index}.stdout").read_text()
                command(
                    [binary, "models", "--standalone", "--print-logs", "--log-level", "debug"],
                    raw,
                    "model-inventory",
                    35,
                    env=env,
                )
                assert MODEL in (raw / "model-inventory.stdout").read_text()
                write_json(records / "preflight.json", {"status": "pass", "inference_calls": 0, "at": now()})
                return
            assert mode == "task"
            prompt = Path("/input/prompt.txt").read_text()
            assert hashlib.sha256(prompt.encode()).hexdigest() == PROMPT_SHA
            write_json(
                records / "task-start.json",
                {"at": now(), "task_cli_attempts": 1, "model_inference_observed": "unavailable-pending-raw-review"},
            )
            command(
                [
                    binary,
                    "run",
                    "--standalone",
                    "--format",
                    "json",
                    "--print-logs",
                    "--log-level",
                    "debug",
                    "--agent",
                    "build",
                    "--model",
                    "ollama/qwen3:1.7b",
                    "--title",
                    "ADK targeted document edit pilot",
                    prompt,
                ],
                raw,
                "task",
                TASK_SECONDS,
                env=env,
                check=False,
            )
    finally:
        if server is not None:
            if server.poll() is None:
                server.kill()
            server.wait(timeout=5)
            write_json(records / "server-stop.json", {"at": now(), "exit_code": server.returncode})


SECRET_PATTERNS = (
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"ssh-(?:ed25519|rsa)\s+[A-Za-z0-9+/]{24,}",
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})",
    r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}",
    r"(?i)\bbearer\s+[A-Za-z0-9._~-]{12,}",
    r"https?://[^\s/\"'<>]+:[^\s/\"'<>]+@",
    r"""(?i)["'](?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|authorization)["']\s*:\s*["'][^"']+""",
)


def publish_evidence(root: Path, evidence: Path, summary: dict[str, Any]) -> None:
    summary["ended_at"] = now()
    attempted = {item["condition"] for item in summary["conditions"]}
    summary["not_started_conditions"] = [name for name in ("baseline", "candidate") if name not in attempted]
    summary["actual_skill_load"] = (
        "unavailable-pending-native-raw-review" if summary["possible_inference"] else "not-run"
    )
    summary["usage"] = "unavailable-pending-native-raw-review"
    write_json(evidence / "summary.json", summary)
    output = root / "published"
    output.mkdir(exist_ok=True)
    allowed = list(evidence.rglob("*.json")) + list(evidence.rglob("*.stdout")) + list(evidence.rglob("*.stderr"))
    allowed += [evidence / "Dockerfile"] if (evidence / "Dockerfile").exists() else []
    for condition in ("baseline", "candidate"):
        for folder in ("work", "skills", "config", "input"):
            if (root / condition / folder).exists():
                allowed += [path for path in (root / condition / folder).rglob("*") if path.is_file()]
        for phase in ("records", "preflight", "recovery"):
            phase_root = root / condition / phase
            if phase_root.exists():
                allowed += list(phase_root.glob("*.json"))
                if (phase_root / "raw").exists():
                    allowed += [path for path in (phase_root / "raw").iterdir() if path.is_file()]
    if (root / "prepare-records").exists():
        allowed += list((root / "prepare-records").glob("*.json"))
        allowed += [path for path in (root / "prepare-records/raw").glob("*") if path.is_file()]
    manifest, excluded = [], []
    for source in sorted(set(allowed)):
        relative = source.relative_to(root)
        if source.is_symlink() or any(
            part in ("home", "data", "state", "cache", "models", "sources", ".git") for part in relative.parts
        ):
            raise RuntimeError(f"Publication allowlist violation: {relative}")
        raw = source.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        removed = []
        if source.name == "ollama-server.stdout":
            lines = text.splitlines(keepends=True)
            removed = [
                index + 1
                for index, line in enumerate(lines)
                if "ssh-ed25519 " in line or "Couldn't find '" in line or "Your new public key is:" in line
            ]
            text = "".join(line for index, line in enumerate(lines) if index + 1 not in removed)
            relative = relative.with_name("ollama-server.sanitized.log")
        if any(re.search(pattern, text) for pattern in SECRET_PATTERNS):
            excluded.append(
                {
                    "path": str(relative),
                    "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "reason": "credential-pattern scan; raw preserved only in private job staging",
                }
            )
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode() if removed else raw)
        manifest.append(
            {
                "path": str(relative),
                "sha256": sha(target),
                "bytes": target.stat().st_size,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "removed_identity_line_numbers": removed,
                "byte_identical_raw": not removed,
            }
        )
    write_json(
        output / "manifest.json",
        {
            "files": manifest,
            "excluded_sensitive_files": excluded,
            "state_directories_excluded": True,
            "whole_repository_excluded": True,
        },
    )
    if excluded:
        write_json(
            output / "publication-limits.json",
            {"complete_raw_available": False, "excluded_sensitive_files": excluded, "coverage": "unavailable"},
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inside", choices=("prepare", "preflight", "task", "export"), required=True)
    inside(parser.parse_args().inside)
