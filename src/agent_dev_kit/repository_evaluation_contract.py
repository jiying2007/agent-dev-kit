"""Repository-evaluation contract loading and deterministic planning."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

from .model import Manifest, ManifestError, ensure_within, sha256_file


CONTRACT_SCHEMA = "adk-repository-runtime-eval-contract/v1"
PLAN_SCHEMA = "adk-repository-runtime-eval-plan/v1"
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
CUSTOMIZATION_SURFACES = {
    "project-instructions",
    "skills",
    "hooks",
    "mcp",
    "plugins",
}
PROCESS_FIELDS = {
    "regression_cycle_count",
    "blind_retry_count",
    "final_verification",
    "phase_order_violation",
    "repeated_tool_call_without_new_evidence",
}
USAGE_FIELDS = {
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
    "cost_usd",
    "elapsed_ms",
    "attempts",
    "tool_calls",
    "timeouts",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("invalid {} JSON: {}".format(label, path)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} JSON root must be an object".format(label))
    return value


def _require_string(value: Mapping[str, Any], field: str, label: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item:
        raise ManifestError("{} {} must be a non-empty string".format(label, field))
    return item


def _load_tasks(path: Path) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ManifestError("cannot read repository evaluation tasks: {}".format(path)) from exc
    required = {
        "id",
        "task_family",
        "language",
        "os",
        "source_kind",
        "repository_revision",
        "container_digest",
        "retrieved_at",
        "expires_at",
        "license_review_status",
        "functional_oracle",
        "security_oracle",
        "execution_status",
        "freshness_class",
        "contamination_status",
    }
    seen = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise ManifestError("repository evaluation tasks contain a blank line at {}".format(line_number))
        try:
            task = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ManifestError("invalid repository evaluation task JSON at {}".format(line_number)) from exc
        if not isinstance(task, dict) or not required <= set(task):
            raise ManifestError("repository evaluation task fields are incomplete at {}".format(line_number))
        task_id = task.get("id")
        if not isinstance(task_id, str) or not ID_RE.fullmatch(task_id) or task_id in seen:
            raise ManifestError("repository evaluation task id is invalid or duplicated")
        seen.add(task_id)
        for field in required.difference({"id", "repository_revision", "container_digest"}):
            _require_string(task, field, "task {}".format(task_id))
        for field in ("repository_revision", "container_digest"):
            if not isinstance(task.get(field), str) or not DIGEST_RE.fullmatch(str(task[field])):
                raise ManifestError("task {} {} must be a sha256 digest".format(task_id, field))
        try:
            retrieved = date.fromisoformat(str(task["retrieved_at"]))
            expires = date.fromisoformat(str(task["expires_at"]))
        except ValueError as exc:
            raise ManifestError("task {} freshness date is invalid".format(task_id)) from exc
        if expires <= retrieved:
            raise ManifestError("task {} expires_at must be after retrieved_at".format(task_id))
        if task["source_kind"] not in {"clean-room-fixture", "approved-real-repository"}:
            raise ManifestError("task {} source_kind is invalid".format(task_id))
        if task["execution_status"] not in {"fixture-only", "owner-approved"}:
            raise ManifestError("task {} execution_status is invalid".format(task_id))
        expected_execution = (
            "fixture-only" if task["source_kind"] == "clean-room-fixture" else "owner-approved"
        )
        if task["execution_status"] != expected_execution:
            raise ManifestError("task {} source and execution status are inconsistent".format(task_id))
        tasks.append(task)
    if not tasks:
        raise ManifestError("repository evaluation task set is empty")
    return tasks


def load_repository_contract(
    manifest: Manifest, contract_path: Path
) -> Tuple[Dict[str, Any], Path, List[Dict[str, Any]]]:
    contract_path = ensure_within(contract_path.resolve(), manifest.root, "repository evaluation contract")
    contract = _load_object(contract_path, "repository evaluation contract")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ManifestError("unsupported repository evaluation contract schema")
    contract_id = contract.get("contract_id")
    if not isinstance(contract_id, str) or not ID_RE.fullmatch(contract_id):
        raise ManifestError("repository evaluation contract_id is invalid")
    tasks_value = _require_string(contract, "tasks", "repository evaluation contract")
    tasks_path = ensure_within(manifest.root / tasks_value, manifest.root, "repository evaluation tasks")
    tasks = _load_tasks(tasks_path)
    minimum_tasks = contract.get("minimum_tasks")
    if isinstance(minimum_tasks, bool) or not isinstance(minimum_tasks, int) or minimum_tasks < 1:
        raise ManifestError("repository evaluation minimum_tasks must be positive")
    if len(tasks) < minimum_tasks:
        raise ManifestError("repository evaluation task set is below minimum_tasks")
    runtimes = contract.get("runtimes")
    if not isinstance(runtimes, list) or len(runtimes) < 2 or len(set(runtimes)) != len(runtimes):
        raise ManifestError("repository evaluation requires at least two unique runtimes")
    if any(not isinstance(runtime, str) or not ID_RE.fullmatch(runtime) for runtime in runtimes):
        raise ManifestError("repository evaluation runtime id is invalid")
    if contract.get("conditions") != ["baseline", "adk"]:
        raise ManifestError("repository evaluation conditions must be [baseline, adk]")
    trials = contract.get("trials")
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 3 or trials > 10:
        raise ManifestError("repository evaluation trials must be between 3 and 10")
    adapters = contract.get("runtime_adapters")
    if not isinstance(adapters, dict) or set(adapters) != set(runtimes):
        raise ManifestError("repository evaluation runtime_adapters must cover every runtime")
    for runtime in runtimes:
        adapter = adapters[runtime]
        if not isinstance(adapter, dict):
            raise ManifestError("repository evaluation adapter must be an object")
        for field in (
            "adapter_id",
            "status",
            "version_pin",
            "baseline_isolation",
            "adk_isolation",
            "rollback",
        ):
            _require_string(adapter, field, "adapter {}".format(runtime))
        if adapter["status"] not in {"contract-only", "available"}:
            raise ManifestError("repository evaluation adapter status is invalid")
        if adapter["status"] == "available" and not DIGEST_RE.fullmatch(adapter["version_pin"]):
            raise ManifestError("available repository adapter must use a sha256 version pin")
        if adapter.get("enabled_default") is not False:
            raise ManifestError("repository evaluation adapters must be disabled by default")
        if adapter.get("optional_dependency") is not True:
            raise ManifestError("repository evaluation adapters must remain optional dependencies")
        if set(adapter.get("baseline_disabled_surfaces", [])) != CUSTOMIZATION_SURFACES:
            raise ManifestError("baseline adapter must disable every customization surface")
        enabled = set(adapter.get("adk_enabled_surfaces", []))
        always_disabled = set(adapter.get("always_disabled_surfaces", []))
        if not enabled or not enabled < CUSTOMIZATION_SURFACES:
            raise ManifestError("ADK adapter enabled surfaces are invalid")
        if not always_disabled or not always_disabled < CUSTOMIZATION_SURFACES or enabled & always_disabled:
            raise ManifestError("ADK adapter disabled surfaces are invalid")
    execution = contract.get("execution_policy")
    if not isinstance(execution, dict):
        raise ManifestError("repository evaluation execution_policy is missing")
    required_execution = {
        "execution_enabled_default": False,
        "external_network_default": "deny",
        "credential_mode": "ephemeral-explicit-only",
        "raw_trace_storage": False,
        "owner_approval_required": True,
    }
    if any(execution.get(key) != value for key, value in required_execution.items()):
        raise ManifestError("repository evaluation execution policy weakens the default boundary")
    process = contract.get("process_quality")
    if not isinstance(process, dict) or set(process.get("required_fields", [])) != PROCESS_FIELDS:
        raise ManifestError("repository evaluation process quality fields are incomplete")
    if process.get("pass_with_invalid_process") != "fail-closed":
        raise ManifestError("repository evaluation lucky pass policy must fail closed")
    resources = contract.get("resource_metrics")
    if not isinstance(resources, dict) or set(resources.get("required_fields", [])) != USAGE_FIELDS:
        raise ManifestError("repository evaluation resource fields are incomplete")
    thresholds = contract.get("thresholds")
    required_thresholds = {
        "candidate_success_rate",
        "minimum_success_delta",
        "maximum_invalid_process_rate",
        "maximum_cost_per_success_usd",
        "maximum_token_p95_ratio",
        "required_non_regression_trials",
    }
    if not isinstance(thresholds, dict) or set(thresholds) != required_thresholds:
        raise ManifestError("repository evaluation thresholds are incomplete")
    for field in ("candidate_success_rate", "minimum_success_delta", "maximum_invalid_process_rate"):
        value = thresholds[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise ManifestError("repository evaluation rate threshold is invalid: {}".format(field))
    for field in ("maximum_cost_per_success_usd", "maximum_token_p95_ratio"):
        value = thresholds[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0:
            raise ManifestError("repository evaluation resource threshold is invalid: {}".format(field))
    required_trials = thresholds["required_non_regression_trials"]
    if isinstance(required_trials, bool) or not isinstance(required_trials, int) or not 1 <= required_trials <= trials:
        raise ManifestError("repository evaluation non-regression trial threshold is invalid")
    return contract, tasks_path, tasks


def repository_plan(manifest: Manifest, contract_path: Path) -> Dict[str, Any]:
    contract, tasks_path, tasks = load_repository_contract(manifest, contract_path)
    statuses = {adapter["status"] for adapter in contract["runtime_adapters"].values()}
    plan = {
        "schema": PLAN_SCHEMA,
        "status": "ready",
        "contract_id": contract["contract_id"],
        "manifest_version": manifest.version,
        "contract_sha256": _digest(contract),
        "tasks": tasks_path.relative_to(manifest.root).as_posix(),
        "tasks_sha256": sha256_file(tasks_path),
        "task_count": len(tasks),
        "runtimes": list(contract["runtimes"]),
        "conditions": list(contract["conditions"]),
        "trials": contract["trials"],
        "expected_results": len(tasks) * len(contract["runtimes"]) * 2 * int(contract["trials"]),
        "adapter_status": "available" if statuses == {"available"} else "contract-only",
        "execution_enabled": False,
        "external_network": "deny",
        "owner_approval_required": True,
        "limitations": [
            "plan validates contracts and frozen metadata only",
            "fixture-only tasks do not satisfy real-repository certification",
            "external runtimes, containers, credentials and network remain disabled",
        ],
    }
    plan["plan_sha256"] = _digest(plan)
    return plan


