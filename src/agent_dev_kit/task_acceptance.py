"""Bounded development-artifact grading; never execute the candidate or its commands.

The caller keeps the case/reference directory outside the executor's write scope.
This checks final bytes and structured answers, not execution, permissions, native
Skill loading, real devices, or model effectiveness. Caller-owned directories must
remain stable during grading; this is not a sandbox for concurrent hostile writers.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from .atomic_io import encode_json_document, validate_document_outputs, write_texts_atomic
from .model import ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import EVIDENCE_PATH_PATTERN, validate_identifier
from .strict_json import StrictJSONError, loads, read_bytes

MAX_FILE_BYTES = 65536
MAX_CHECKS = 32
MAX_ENTRIES = 128
_CASE_KEYS = {"schema_version", "task_id", "family", "evidence_scope", "initial_dir", "checks"}


def _identifier(value: Any, label: str) -> str:
    return validate_identifier(value, label)


def _relative(value: Any) -> str:
    if (not isinstance(value, str) or not value or len(value) > 240
            or re.fullmatch(EVIDENCE_PATH_PATTERN, value) is None):
        raise ManifestError("task path must be a bounded relative path")
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or path.as_posix() != value or "\\" in value
            or any(part in {".", ".."} for part in path.parts)
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ManifestError("task path must be canonical and relative")
    return value


def _safe_path(path: Path) -> Path:
    """Reject existing links and non-directory ancestors before bounded I/O."""
    path = Path(os.path.abspath(path))
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ManifestError("task paths must not contain symlinks")
        if component != path and not stat.S_ISDIR(info.st_mode):
            raise ManifestError("task path parent must be a directory")
    return path


def _read(path: Path) -> bytes:
    try:
        return read_bytes(_safe_path(path), max_bytes=MAX_FILE_BYTES, regular_only=True)
    except StrictJSONError as exc:
        raise ManifestError("task artifact must be a bounded readable regular file") from exc


def _files(directory: Path) -> set[str]:
    """Enumerate a small final tree without following links or special files."""
    root = _safe_path(directory)
    if not root.is_dir():
        raise ManifestError("task work directory is missing")
    found: set[str] = set()
    pending = [root]
    count = 0
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                count += 1
                relative = Path(entry.path).relative_to(root).as_posix()
                if count > MAX_ENTRIES or len(PurePosixPath(relative).parts) > 16:
                    raise ManifestError("task tree exceeds enumeration budget")
                _relative(relative)
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    found.add(relative)
                else:
                    raise ManifestError("task tree must contain only regular files and directories")
    return found


def _case(case_path: Path) -> tuple[dict[str, Any], bytes, Path]:
    raw = _read(case_path)
    try:
        case = loads(raw, max_bytes=MAX_FILE_BYTES)
    except StrictJSONError as exc:
        raise ManifestError("task case must be strict JSON") from exc
    if (not isinstance(case, dict) or set(case) != _CASE_KEYS
            or case.get("schema_version") != "adk-development-task/v1"
            or case.get("evidence_scope") != "test-only"
            or case.get("initial_dir") != "initial"):
        raise ManifestError("unsupported development task case")
    _identifier(case["task_id"], "task_id")
    _identifier(case["family"], "family")
    checks = case["checks"]
    if not isinstance(checks, list) or not 1 <= len(checks) <= MAX_CHECKS:
        raise ManifestError("task case requires a bounded nonempty check list")
    names: set[str] = set()
    paths: set[str] = set()
    initial = _safe_path(case_path.parent / "initial")
    for check in checks:
        if not isinstance(check, dict):
            raise ManifestError("task check must be an object")
        name = _identifier(check.get("name"), "check name")
        path = _relative(check.get("path"))
        if not path.startswith("work/") or path == "work/":
            raise ManifestError("task artifacts must be inside work/")
        if name in names or path in paths:
            raise ManifestError("task check names and artifact paths must be unique")
        names.add(name)
        paths.add(path)
        common = {"name", "kind", "path"}
        kind = check.get("kind")
        if kind == "json-equals" and set(check) == common | {"expected"}:
            continue
        if kind == "unchanged" and set(check) == common | {"source"}:
            pass
        elif kind == "text-replace-once" and set(check) == common | {"source", "before", "after"}:
            if (not isinstance(check["before"], str) or not check["before"]
                    or not isinstance(check["after"], str) or check["before"] == check["after"]):
                raise ManifestError("replacement check must describe one actual edit")
        else:
            raise ManifestError("unsupported task check; commands are never accepted")
        source = _relative(check["source"])
        if path != "work/" + source:
            raise ManifestError("reference input must correspond to the same work path")
        reference = _read(initial / source)
        if kind == "text-replace-once":
            try:
                text = reference.decode("utf-8")
            except UnicodeError as exc:
                raise ManifestError("replacement reference must be UTF-8") from exc
            if text.count(check["before"]) != 1:
                raise ManifestError("replacement reference must contain exactly one old span")
    if not {"work/" + item for item in _files(initial)} <= paths:
        raise ManifestError("task contract must account for every initial file")
    return case, raw, initial


def _expected(check: dict[str, Any], initial: Path) -> bytes:
    if check["kind"] == "json-equals":
        return canonical_json_bytes(check["expected"])
    raw = _read(initial / check["source"])
    if check["kind"] == "text-replace-once":
        return raw.decode("utf-8").replace(check["before"], check["after"], 1).encode("utf-8")
    return raw


def grade_task_artifacts(
    case_path: Path, workspace: Path, output_path: Path, *, run_id: str,
    executor_id: str, grader_id: str,
) -> dict[str, Any]:
    """Grade one owner-frozen development case and publish digest-bound evidence.

    ``workspace/work`` contains the executor's copied input and resulting files.
    ``output_path`` must be in the evidence package, outside ``work``. The sibling
    ``<output name>.checks.json`` stores actual grader results, without raw content.
    Identity separation is caller declared, not independently authenticated.
    """
    for name, value in (("run_id", run_id), ("executor_id", executor_id), ("grader_id", grader_id)):
        _identifier(value, name)
    if executor_id == grader_id:
        raise ManifestError("executor and grader must be different identities")
    workspace = _safe_path(workspace)
    if not workspace.is_dir():
        raise ManifestError("evidence workspace must already exist")
    case_path = _safe_path(case_path)
    if case_path.is_relative_to(workspace):
        raise ManifestError("owner-frozen case must be outside the executor evidence package")
    output = _safe_path(output_path if output_path.is_absolute() else workspace / output_path)
    try:
        output_relative = _relative(output.relative_to(workspace).as_posix())
    except ValueError as exc:
        raise ManifestError("acceptance output must stay inside the evidence package") from exc
    if output_relative == "work" or output_relative.startswith("work/"):
        raise ManifestError("acceptance output must be outside the graded work tree")
    report_path = output.with_name(output.name + ".checks.json")
    report_relative = report_path.relative_to(workspace).as_posix()
    case, case_raw, initial = _case(case_path)
    artifacts: list[dict[str, str]] = []
    results: list[dict[str, Any]] = []
    for check in case["checks"]:
        desired = _expected(check, initial)
        result: dict[str, Any] = {
            "name": check["name"], "kind": check["kind"], "path": check["path"],
            "status": "failed", "reason": "artifact-mismatch",
            "expected_sha256": sha256_bytes(desired),
        }
        try:
            raw = _read(workspace / check["path"])
            digest = sha256_bytes(raw)
            artifacts.append({"path": check["path"], "sha256": digest})
            result["observed_sha256"] = digest
            actual = canonical_json_bytes(loads(raw)) if check["kind"] == "json-equals" else raw
            if actual == desired:
                result.update(status="passed", reason="artifact-conforms")
        except StrictJSONError:
            result["reason"] = "invalid-json"
        except ManifestError:
            result["reason"] = "missing-or-unsafe-artifact"
        results.append(result)
    expected_paths = {item["path"][len("work/"):] for item in case["checks"]}
    try:
        observed_paths = _files(workspace / "work")
        boundary = observed_paths == expected_paths
        boundary_reason = "final-tree-conforms" if boundary else "missing-or-unexpected-final-files"
    except (ManifestError, OSError):
        boundary, boundary_reason = False, "unsafe-or-unreadable-final-tree"
    report = {
        "schema_version": "adk-task-check-report/v1", "task_id": case["task_id"],
        "run_id": run_id, "case_sha256": sha256_bytes(case_raw),
        "scope": "final-artifact-conformance-only", "evidence_scope": "test-only",
        "raw_content_stored": False, "checks": results,
        "artifact_boundary": {"status": "passed" if boundary else "failed", "reason": boundary_reason},
        "unverified": ["tool-permissions", "intermediate-side-effects", "skill-loading",
                       "test-execution", "device-outcomes", "model-effectiveness"],
    }
    report_text = encode_json_document(report, "task check report")
    evidence = {"path": report_relative, "sha256": sha256_bytes(report_text.encode("utf-8"))}
    success = bool(artifacts) and boundary and all(item["status"] == "passed" for item in results)
    acceptance: dict[str, Any] = {
        "schema_version": "adk-task-acceptance/v1", "run_id": run_id, "task_id": case["task_id"],
        "executor_id": executor_id, "grader_id": grader_id, "status": "passed" if success else "failed",
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "checks": [{"name": item["name"], "status": item["status"], "evidence": evidence} for item in results],
        "guardrails": [{"name": "artifact-boundary", "status": "passed" if boundary else "failed", "evidence": evidence}],
        "trust": "caller-observed", "evidence_scope": "test-only", "raw_content_stored": False,
    }
    outputs = [report_path, output]
    inputs = [case_path, *(workspace / item["path"] for item in artifacts)]
    validate_document_outputs(outputs, inputs)
    write_texts_atomic([(report_path, report_text), (output, encode_json_document(acceptance, "task acceptance"))])
    return acceptance
