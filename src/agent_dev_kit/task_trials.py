"""Bind task input/state/assigned exposure before the existing trial comparator.

An adk-task-trials/v1 document extends a frozen effect plan with task_bindings
(task_id, input_snapshot_sha256, workspace_snapshot_sha256, source_sha), a
grader_id, provenance and two conditions mapping each task_id to its assigned
(target_skill, expected, content_sha256). Trials use digest-bound observation
references. The plan's dataset_ref binds all these controls. Registration
remains caller declared. source_sha is the initial TASK repository commit;
ADK old/new versions are identified by the existing asset bundle digests.
Missing actual Skill loads stay in the assigned population; wrong versions,
control contamination and state drift fail closed. No candidate is executed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .effect_trials import compare_effect_trials
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import validate_identifier, validate_sha256
from .strict_json import loads
from .task_evidence import (
    _Package, _choice, _list, _object, _reference, publish_task_report, read_task_evidence,
)

MAX_OBSERVATIONS = 120
MAX_CAMPAIGN_BYTES = 64 * 1024 * 1024


def _ref(value: Any) -> str:
    return "ref:" + sha256_bytes(canonical_json_bytes(value))


def task_trial_controls_ref(document: dict[str, Any]) -> str:
    """Bind the predeclared task population and assignment into dataset_ref."""
    return _ref({"schema_version": "adk-task-trial-controls/v1", **{key: document[key] for key in (
        "task_bindings", "conditions", "grader_id", "provenance",
    )}})


def _task_bindings(value: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw in _list(value, 128, "task bindings"):
        item = _object(raw, {"task_id", "input_snapshot_sha256", "workspace_snapshot_sha256", "source_sha"},
                       "task binding")
        task_id = validate_identifier(item["task_id"], "planned task id")
        if task_id in result:
            raise ManifestError("task trials: duplicate task binding")
        for key in ("input_snapshot_sha256", "workspace_snapshot_sha256"):
            validate_sha256(item[key], "planned snapshot digest")
        if not isinstance(item["source_sha"], str) or re.fullmatch(r"[0-9a-f]{40}", item["source_sha"]) is None:
            raise ManifestError("task trials: invalid planned source SHA")
        result[task_id] = item
    if not result:
        raise ManifestError("task trials: missing task bindings")
    return result


def _conditions(value: Any, tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = _object(value, {"baseline", "candidate"}, "assigned conditions")
    for side in result:
        assigned = _object(result[side], set(tasks), "per-task assignments")
        for condition in assigned.values():
            item = _object(condition, {"target_skill", "expected", "content_sha256"}, "assigned exposure")
            validate_identifier(item["target_skill"], "planned skill")
            _choice(item["expected"], {"loaded", "absent"}, "planned exposure")
            validate_sha256(item["content_sha256"], "planned skill digest")
    if any(result["baseline"][task]["target_skill"] != result["candidate"][task]["target_skill"] for task in tasks):
        raise ManifestError("task trials: conditions must target the same skill for each task")
    return result


def _compare(package: _Package, manifest: Manifest) -> tuple[dict[str, Any], tuple[Path, ...]]:
    raw = package.read(package.name)
    data = _object(loads(raw), {"schema_version", "provenance", "plan", "task_bindings", "conditions",
                               "grader_id", "trials"}, "task trial input")
    if data["schema_version"] != "adk-task-trials/v1":
        raise ManifestError("task trials: unsupported schema")
    provenance = _choice(data["provenance"], {"recorded-task", "synthetic-fixture"}, "campaign provenance")
    tasks = _task_bindings(data["task_bindings"])
    conditions = _conditions(data["conditions"], tasks)
    grader = validate_identifier(data["grader_id"], "planned grader")
    plan = data["plan"]
    if (not isinstance(plan, dict) or not isinstance(plan.get("controls"), dict)
            or not isinstance(plan.get("task_ids"), list) or any(not isinstance(item, str) for item in plan["task_ids"])
            or set(plan["task_ids"]) != set(tasks)
            or plan["controls"].get("dataset_ref") != task_trial_controls_ref(data)):
        raise ManifestError("task trials: frozen plan must bind the complete task input/state population")
    plan_ref, controls_ref = _ref(plan), _ref(plan["controls"])
    trials: list[dict[str, Any]] = []
    inputs: list[Path] = []
    observations: set[str] = set()
    observation_refs: list[str] = []
    bytes_read = 0
    for raw_trial in _list(data["trials"], 64, "task trials"):
        trial = _object(raw_trial, {"trial_id", "infrastructure_status", "baseline", "candidate"}, "task trial")
        composed: dict[str, Any] = {"trial_id": trial["trial_id"], "infrastructure_status": trial["infrastructure_status"]}
        for side in ("baseline", "candidate"):
            runs = []
            for reference in _list(trial[side], 128, "task observations"):
                relative, digest = _reference(reference)
                if relative in observations or len(observations) >= MAX_OBSERVATIONS:
                    raise ManifestError("task trials: duplicate or excessive observations")
                observations.add(relative)
                # Descriptor-relative checking first, then the imported binding
                # must match these exact bytes even if the path changes later.
                _, observation_ref = package.checked(reference)
                imported = read_task_evidence(package.directory / relative, manifest)
                bytes_read += imported.bytes_read
                if bytes_read + package.total > MAX_CAMPAIGN_BYTES:
                    raise ManifestError("task trials: campaign byte limit")
                report = imported.report
                binding = report["bindings"]
                run = report["run_evidence"]
                task_id = run["trace_summary"]["task_id"]
                if binding["observation_ref"] != "ref:" + digest:
                    raise ManifestError("task trials: observation changed during import")
                if report["provenance"] != provenance:
                    raise ManifestError("task trials: synthetic and recorded provenance must not mix")
                if task_id not in tasks:
                    raise ManifestError("task trials: unexpected task")
                expected = tasks[task_id]
                if (binding["input_snapshot_ref"] != "ref:" + expected["input_snapshot_sha256"]
                        or binding["workspace_snapshot_ref"] != "ref:" + expected["workspace_snapshot_sha256"]
                        or binding["source_sha"] != expected["source_sha"]):
                    raise ManifestError("task trials: input or initial workspace/source drift")
                if report["assigned_exposure"] != conditions[side][task_id] or binding["grader_id"] != grader:
                    raise ManifestError("task trials: assignment or grader differs from frozen controls")
                # Do not filter by primary_skill, wrong_skill, task outcome or
                # whether a load happened. Compare the entire assigned group.
                runs.append({"run": run, "plan_ref": plan_ref, "controls_ref": controls_ref})
                inputs.extend(imported.inputs)
                observation_refs.append(observation_ref)
            composed[side] = runs
        trials.append(composed)
    comparison = compare_effect_trials({"schema_version": "adk-effect-trials/v1", "plan": plan, "trials": trials}, manifest)
    result = {
        "schema_version": "adk-task-trial-comparison/v1", "status": "compared", "verdict": comparison["verdict"],
        "provenance": provenance, "trust": "caller-observed", "evidence_scope": "test-only",
        "quality_evidence_eligible": False, "release_authorized": False, "raw_content_stored": False,
        "lifecycle_authority": "none-evidence-only", "pairing_authority": "caller-observed-state-and-assignment-checked",
        "population": "all-assigned-observations", "task_plan_ref": _ref({key: data[key] for key in (
            "plan", "task_bindings", "conditions", "grader_id", "provenance",
        )}), "input_ref": "ref:" + sha256_bytes(raw), "observation_refs": observation_refs,
        "comparison": comparison,
    }
    inputs.extend(package.directory / name for name in package.cache)
    return result, tuple(inputs)


def compare_task_trials(input_path: Path, manifest: Manifest, *, output_path: Path | None = None) -> dict[str, Any]:
    """Import complete assigned task populations and reuse existing statistics.

    Identity separation, chronology, native skill loading and capture completeness
    remain caller observations. This checks supplied bytes and consistency, not
    native attestation or production eligibility.
    """
    package = _Package(input_path)
    try:
        report, inputs = _compare(package, manifest)
        if output_path is not None:
            publish_task_report(report, output_path, inputs + (
                manifest.root / "manifest.json", manifest.root / "manifests/agent_value_contracts.json",
            ))
        return report
    finally:
        package.close()
