"""One fixed archive-method observation, not an ADC test or release qualification.

Only openat is traced. Successful open is not proof of dlopen/mmap; missing
records do not prove absence of other file access. Fixed ordering and caches
preclude timing causality. Raw trace streams stay outside the artifact directory.
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time


BASE = "0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb"
BASE_TREE = "77dcf4a3f0bdd08f9572329c7c2ef1de8f276ca1"
ADDITIONS = frozenset({"tools/diagnostics/archive_selection_20261118.py",
                        ".github/workflows/archive-selection-20261118.yml",
                        *[f"docs/changes/20261118-archive-selection/{name}.md"
                          for name in ("requirements", "design", "tasks")]})
TRACE_LIMIT = 1024 * 1024
PREFIX = r"(?:(?P<pid>\d+)\s+|\[pid\s+(?P<bracket_pid>\d+)\]\s+)?"
OPENAT = re.compile(PREFIX + r'openat\((?P<dirfd>[^,]+), (?P<path>"(?:[^"\\]|\\.)*"), '
                    r'(?P<flags>[^\n]+)\)\s+=\s+(?P<result>-?\d+)(?:\s+(?P<errno>[A-Z][A-Z0-9_]+))?'
                    r'(?:\s+\([^\n]*\))?$')
CONTROL = re.compile(PREFIX + r"(?:\+\+\+ (?:exited with \d+|killed by [A-Z0-9]+).*\+\+\+|--- SIG[A-Z0-9]+ .*---)$")
CONSUMER_LINE = re.compile(r"(?:PASS|FAIL) [a-z0-9-]+ expected=-?\d+ actual=-?\d+$")
ARM_SHELL = """set -u
printf started > "$6/ar.started"
"$1" -f -e trace=openat -s 4096 -o "$6/ar.raw" -- "$2" qc "$4" "$5"
code=$?
printf '%s\\n' "$code" > "$6/ar.exit"
if [ "$code" -ne 0 ]; then exit "$code"; fi
printf started > "$6/ranlib.started"
"$1" -f -e trace=openat -s 4096 -o "$6/ranlib.raw" -- "$3" "$4"
code=$?
printf '%s\\n' "$code" > "$6/ranlib.exit"
exit "$code"
"""


def now():
    return {"utc": datetime.now(timezone.utc).isoformat(), "monotonic": time.monotonic()}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def not_run(reason):
    return {"status": "NOT_RUN", "reason": reason}


def git(root, *arguments):
    return subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True,
                          timeout=15).stdout.decode().rstrip("\n")


def source_guard(root):
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("repository root mismatch")
    if git(root, "rev-parse", f"{BASE}^{{tree}}") != BASE_TREE:
        raise ValueError("base tree mismatch")
    git(root, "merge-base", "--is-ancestor", BASE, "HEAD")
    changes = {}
    for name, suffix in (("head", (BASE, "HEAD")), ("worktree", (BASE,))):
        fields = git(root, "diff", "--no-ext-diff", "--no-renames", "--name-status", "-z", *suffix).split("\0")
        if fields[-1] == "":
            fields.pop()
        if len(fields) % 2:
            raise ValueError("invalid change encoding")
        pairs = list(zip(fields[::2], fields[1::2], strict=True))
        if any(kind != "A" or path not in ADDITIONS for kind, path in pairs):
            raise ValueError("original tracked input changed")
        changes[name] = pairs
    untracked = set(filter(None, git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    if not untracked <= ADDITIONS or any(not (root / path).is_file() or (root / path).is_symlink() for path in ADDITIONS):
        raise ValueError("unexpected additions")
    return {"base": BASE, "base_tree": BASE_TREE, "head": git(root, "rev-parse", "HEAD"),
            "tree": git(root, "rev-parse", "HEAD^{tree}"), "changes": changes, "untracked": sorted(untracked),
            "addition_sha256": {path: digest((root / path).read_bytes()) for path in sorted(ADDITIONS)}}


def fresh_output(path, root):
    if not path.is_absolute() or ".." in path.parts or path.resolve() != path or path.is_relative_to(root) or path.exists():
        raise ValueError("output must be fresh, canonical, absolute and outside repository")
    path.mkdir(mode=0o700)


def file_stat(path):
    value = path.stat()
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("not a regular file")
    return {"device": value.st_dev, "inode": value.st_ino, "size": value.st_size,
            "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns}


def file_evidence(path):
    if path.is_symlink():
        raise ValueError("artifact is a symlink")
    before = file_stat(path)
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            sha.update(block)
    after = file_stat(path)
    return {"sha256": sha.hexdigest(), "stat_before": before, "stat_after": after, "stable": before == after}


def locate(name):
    located = shutil.which(name)
    if located is None:
        raise FileNotFoundError(name)
    path = Path(located)
    resolved = path.resolve(strict=True)
    return {"path": str(path), "resolved": str(resolved), "stat": file_stat(resolved)}


def select_tools():
    tools = {name: locate(name) for name in ("cc", "ar", "ranlib", "strace")}
    # This one necessary GNU-selection query is the explicit pre-experiment
    # exception. A dumpversion number alone would also accept Clang.
    query = subprocess.run([tools["cc"]["path"], "-v"], capture_output=True, timeout=3, check=False)
    lines = re.findall(r"^gcc version (\d+)[^\r\n]*", query.stderr.decode(errors="replace"), re.M)
    if query.returncode != 0 or len(lines) != 1:
        raise ValueError("compiler did not identify unambiguously as GNU")
    major = lines[0]
    if not re.fullmatch(r"(?:[A-Za-z0-9_]+-)*gcc(?:-" + re.escape(major) + r")?", Path(tools["cc"]["resolved"]).name):
        raise ValueError("resolved compiler name does not match GNU major")
    tools["gcc-ar"] = locate("gcc-ar-" + major)
    tools["gcc-ranlib"] = locate("gcc-ranlib-" + major)
    return tools, {"exit_code": query.returncode, "gnu_major": major,
                   "gnu_lines": [line for line in query.stderr.decode(errors="replace").splitlines()
                                 if re.match(r"^gcc version \d+", line)],
                   "stdout_sha256": digest(query.stdout), "stderr_sha256": digest(query.stderr)}


def output_summary(text):
    data = text.encode("utf-8", errors="replace")
    lines = text.splitlines()
    # Never copy unexpected strace lines or arbitrary diagnostic paths through
    # stdout/stderr. Keep exact digests and only the original consumer grammar.
    retained = [line for line in lines if CONSUMER_LINE.fullmatch(line)
                or line == "SKIP 24-bit cases: int cannot represent these inputs"]
    return {"decoded_utf8_sha256": digest(data), "decoded_utf8_bytes": len(data),
            "consumer_lines": retained, "other_lines_not_retained": len(lines) - len(retained)}


def execute(helper, label, cwd, arguments, *, code='exec "$@"'):
    started = now()
    try:
        result = helper(code, cwd, *map(str, arguments), label="archive-selection/" + label)
        return {"status": "COMPLETED", "exit_code": result.returncode, "cleanup": "not_required",
                "stdout": output_summary(result.stdout), "stderr": output_summary(result.stderr),
                "started": started, "finished": now()}
    except AssertionError as error:
        first = str(error).split("\n", 1)[0]
        cleanup = re.search(r"(?:^|; )cleanup=([a-z-]+)", first)
        return {"status": "TIMEOUT" if ": timeout;" in first else "ERROR", "exit_code": None,
                "cleanup": cleanup[1] if cleanup else "UNKNOWN", "started": started, "finished": now(),
                "exception_type": type(error).__name__, "exception_decoded_sha256": digest(str(error).encode())}
    except Exception as error:
        return {"status": "ERROR", "exit_code": None, "cleanup": "UNKNOWN", "started": started,
                "finished": now(), "exception_type": type(error).__name__}


def safe_to_continue(result):
    return result["status"] == "COMPLETED" or result.get("cleanup") == "complete"


def succeeded(result):
    return result["status"] == "COMPLETED" and result.get("exit_code") == 0


def allowed_path(value, dirfd, cwd, build):
    path = Path(value)
    if not path.is_absolute():
        if dirfd.strip() != "AT_FDCWD":
            return None
        path = cwd / path
    path = Path(os.path.normpath(str(path)))  # Lexical only; no file-content/cache reads.
    libraries = (Path("/lib"), Path("/lib64"), Path("/usr/lib"), Path("/usr/lib64"), Path("/usr/local/lib"))
    if path == Path("/etc/ld.so.cache") or path.is_relative_to(build) or any(path.is_relative_to(base) for base in libraries):
        return str(path)
    return None


def trace_evidence(path, cwd, build, command_finished):
    result = {"status": "UNKNOWN", "records": [], "filtered": 0, "parse_failed": 0,
              "control_lines": 0, "terminal_lines": 0, "signal_terminals": 0,
              "successful_openat": 0, "failed_openat": 0}
    try:
        if path.is_symlink():
            raise ValueError("raw trace is a symlink")
        before = file_stat(path)
        sha = hashlib.sha256()
        prefix = bytearray()
        count = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                sha.update(block)
                count += len(block)
                prefix.extend(block[:max(0, TRACE_LIMIT - len(prefix))])
        after = file_stat(path)
        truncated = count > len(prefix)
        result.update({"stream_sha256": sha.hexdigest(), "stream_bytes_hashed": count,
                       "stat_before": before, "stat_after": after, "stable_stream": before == after,
                       "full_stream_hashed": before == after and count == after["size"],
                       "parse_bytes": len(prefix), "parse_truncated": truncated})
        lines = bytes(prefix).splitlines(keepends=True)
        for raw in lines:
            if not raw.endswith(b"\n"):
                result["parse_failed"] += 1
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            matched = OPENAT.fullmatch(line)
            if matched is None:
                if CONTROL.fullmatch(line):
                    result["control_lines"] += 1
                    result["terminal_lines"] += int("+++" in line)
                    result["signal_terminals"] += int("+++ killed by " in line)
                else:
                    result["parse_failed"] += 1
                continue
            try:
                value = ast.literal_eval(matched["path"])
                kept = allowed_path(value, matched["dirfd"], cwd, build)
                returned = int(matched["result"])
                errno = matched["errno"]
                if (returned < 0 and errno is None) or (returned >= 0 and errno is not None):
                    raise ValueError("ambiguous syscall result")
            except (SyntaxError, ValueError):
                result["parse_failed"] += 1
                continue
            result["successful_openat" if returned >= 0 else "failed_openat"] += 1
            if kept is None:
                result["filtered"] += 1
                continue
            result["records"].append({"pid": int(matched["pid"] or matched["bracket_pid"] or 0) or None,
                                      "path": kept, "result_fd": returned if returned >= 0 else None,
                                      "errno": errno, "success": returned >= 0})
        complete = (command_finished and result["full_stream_hashed"] and not truncated
                    and result["parse_failed"] == 0 and result["terminal_lines"] > 0
                    and result["signal_terminals"] == 0)
        result.update({"status": "OBSERVED", "capture_and_parse_complete": complete,
                       "scope": "filtered openat only; positive observations survive incomplete capture"})
    except Exception as error:
        result.update({"error": type(error).__name__, "capture_and_parse_complete": False})
    return result


def arm(helper, name, tools, directory, object_path, private, build, result):
    directory.mkdir()
    private.mkdir()
    archive = directory / "libadc_scale.a"
    ar, ranlib = ("ar", "ranlib") if name == "generic" else ("gcc-ar", "gcc-ranlib")
    arguments = [tools["strace"]["path"], tools[ar]["path"], tools[ranlib]["path"], archive, object_path, private]
    result.update(execute(helper, name, directory, arguments, code=ARM_SHELL))
    result["commands"] = {}
    result["traces"] = {}
    for stage, tool in (("ar", ar), ("ranlib", ranlib)):
        marker = private / (stage + ".exit")
        if marker.exists():
            code = int(marker.read_text().strip())
            command = {"status": "COMPLETED", "exit_code": code, "tool": tools[tool]}
        elif (private / (stage + ".started")).exists():
            command = {"status": "INCOMPLETE", "exit_code": None, "tool": tools[tool]}
        else:
            command = not_run("earlier command failed or invocation did not reach this stage")
        result["commands"][stage] = command
        result["traces"][stage] = trace_evidence(private / (stage + ".raw"), directory, build,
                                                 command["status"] == "COMPLETED" and 0 <= command["exit_code"] < 128)
    return result


def tools_after(tools, allow_execution):
    records = {}
    for name, before in tools.items():
        try:
            path = Path(before["resolved"])
            if Path(before["path"]).resolve() != path or file_stat(path) != before["stat"]:
                raise ValueError("tool identity drift")
            evidence = file_evidence(path)
            if allow_execution:
                version = subprocess.run([before["path"], "--version"], capture_output=True, timeout=3, check=False)
                evidence["version"] = {"exit_code": version.returncode,
                                        "stdout": version.stdout[:4096].decode(errors="replace"),
                                        "stderr": version.stderr[:4096].decode(errors="replace"),
                                        "truncated": len(version.stdout) > 4096 or len(version.stderr) > 4096}
            else:
                evidence["version"] = not_run("cleanup could not be confirmed")
            if Path(before["path"]).resolve() != path or file_stat(path) != before["stat"] or not evidence["stable"]:
                raise ValueError("tool identity drift during inspection")
            records[name] = {"status": "OBSERVED", **evidence}
        except Exception as error:
            records[name] = {"status": "UNKNOWN", "error": type(error).__name__}
    return records


def run_experiment(helper, root, out, tools, result):
    build = out / "build"
    build.mkdir()
    object_path = build / "adc_scale.c.o"
    adc = root / "examples/embedded-test-matrix"
    include = adc / "src"
    flags = [tools["cc"]["path"], "-I" + str(include), "-pedantic-errors", "-O3", "-DNDEBUG"]
    result.update({"status": "RUNNING", "compile": not_run("not reached"),
                   "arms": {name: not_run("not reached") for name in ("generic", "matched")},
                   "artifacts": {}, "safe_to_continue": False})
    result["compile"] = execute(helper, "compile", build,
                                [*flags, "-std=c11", "-c", include / "adc_scale.c", "-o", object_path])
    result["safe_to_continue"] = safe_to_continue(result["compile"])
    if succeeded(result["compile"]):
        result["object_before"] = file_evidence(object_path)
    with tempfile.TemporaryDirectory(prefix="adk-archive-selection-private-") as temporary:
        for name in ("generic", "matched"):
            if not result["safe_to_continue"] or not succeeded(result["compile"]):
                result["arms"][name] = not_run("compile failed or cleanup was not confirmed")
                continue
            before = file_evidence(object_path)
            if before != result["object_before"]:
                result["safe_to_continue"] = False
                result["arms"][name] = not_run("shared object changed")
                continue
            observed = {"status": "RUNNING"}
            result["arms"][name] = observed
            arm(helper, name, tools, build / name, object_path, Path(temporary) / name, build, observed)
            result["safe_to_continue"] = safe_to_continue(observed)
            observed["object_after"] = file_evidence(object_path)
            if observed["object_after"] != result["object_before"]:
                result["safe_to_continue"] = False
        # Only begin consumers after both arms have had their fixed opportunity.
        for name in ("generic", "matched"):
            observed = result["arms"][name]
            observed["link"] = not_run("arm failed or cleanup was not confirmed")
            observed["consumer"] = not_run("link not completed")
            if not result["safe_to_continue"] or not succeeded(observed):
                continue
            archive = build / name / "libadc_scale.a"
            executable = build / name / "test_adc_scale"
            result["artifacts"][name + "/libadc_scale.a"] = file_evidence(archive)
            observed["link"] = execute(helper, name + "/link", build / name,
                                       [*flags, "-std=c90", adc / "tests/test_adc_scale.c", archive, "-o", executable])
            result["safe_to_continue"] = safe_to_continue(observed["link"])
            if succeeded(observed["link"]) and result["safe_to_continue"]:
                result["artifacts"][name + "/test_adc_scale"] = file_evidence(executable)
                observed["consumer"] = execute(helper, name + "/consumer", build / name, [executable])
                result["safe_to_continue"] = safe_to_continue(observed["consumer"])
    result["all_commands_succeeded"] = succeeded(result["compile"]) and all(
        succeeded(item) and succeeded(item["link"]) and succeeded(item["consumer"]) for item in result["arms"].values())
    archives = [result["artifacts"].get(name + "/libadc_scale.a", {}).get("sha256") for name in ("generic", "matched")]
    result["archive_bytes_equal"] = archives[0] == archives[1] if all(archives) else None
    result["trace_comparison_complete"] = all(
        item.get("traces") and all(trace["capture_and_parse_complete"] for trace in item["traces"].values())
        for item in result["arms"].values())
    result["status"] = "OBSERVED"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    created = False
    tools = {}
    report = {"started": now(), "qualification": "DIAGNOSTIC_ONLY_NONE", "historical_root_cause": "UNKNOWN",
              "scope": "method-level filtered openat and artifact semantics; no dlopen or timing-causality claim",
              "raw_trace_policy": "private temporary directory outside --out; full digest plus <=1MiB parsing",
              "trace_memory_disclosure": "strace decodes syscall arguments; this is not zero tracee-memory access",
              "experiment": not_run("preconditions not completed")}
    exit_code = 2
    try:
        fresh_output(arguments.out, root)
        created = True
        report["source_before"] = source_guard(root)
        if sys.version_info[:2] != (3, 12) or sys.platform != "linux":
            raise ValueError("registered experiment requires Linux and Python 3.12")
        tools, report["gnu_selection"] = select_tools()
        report["tools_before"] = tools
        spec = importlib.util.spec_from_file_location("archive_original_helper", root / "tests/test_skill_command_examples.py")
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        report["helper_sha256"] = digest((root / "tests/test_skill_command_examples.py").read_bytes())
        report["experiment"] = {"status": "RUNNING"}
        run_experiment(original.run_example, root, arguments.out, tools, report["experiment"])
        exit_code = 0 if report["experiment"]["all_commands_succeeded"] else 1
    except Exception as error:
        report["error"] = type(error).__name__
        exit_code = 1 if report["experiment"].get("status") != "NOT_RUN" else 2
        if exit_code == 1:
            report["experiment"]["status"] = "ERROR"
            report["experiment"]["safe_to_continue"] = False
    finally:
        if created:
            for item in report["experiment"].get("arms", {}).values():
                item.setdefault("link", not_run("experiment stopped before this stage"))
                item.setdefault("consumer", not_run("experiment stopped before this stage"))
            try:
                report["tools_after"] = tools_after(tools, report["experiment"].get("safe_to_continue", False))
            except Exception as error:
                report["tool_post_error"] = type(error).__name__
            try:
                report["source_after"] = source_guard(root)
                report["source_unchanged"] = report["source_before"] == report["source_after"]
                if not report["source_unchanged"]:
                    exit_code = 1
            except Exception as error:
                report["post_error"] = type(error).__name__
                report["source_unchanged"] = False
                exit_code = 1
            report["finished"] = now()
            report["actual_exit_code"] = exit_code
            with (arguments.out / "report.json").open("x", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2, sort_keys=True)
                stream.write("\n")
    print(json.dumps({"qualification": "DIAGNOSTIC_ONLY_NONE", "actual_exit_code": exit_code,
                      "outcome": "OBSERVED" if exit_code == 0 else "FAILED_OR_NOT_RUN"}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
