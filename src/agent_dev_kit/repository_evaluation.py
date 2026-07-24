"""Deterministic contracts for repository-level agent evaluation evidence."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .model import Manifest, ManifestError, ensure_within, sha256_file


CONTRACT_SCHEMA = "adk-repository-runtime-eval-contract/v1"
PLAN_SCHEMA = "adk-repository-runtime-eval-plan/v1"
REPORT_SCHEMA = "adk-repository-runtime-eval-report/v1"
CERTIFICATION_SCHEMA = "adk-repository-runtime-eval-certification/v1"
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


def _nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(float(ordered[index]), 6)


def _distribution(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0, "coefficient_of_variation": 0.0}
    mean = statistics.fmean(values)
    variation = statistics.pstdev(values) / mean if len(values) > 1 and mean else 0.0
    return {
        "p50": _nearest_rank(values, 0.50),
        "p95": _nearest_rank(values, 0.95),
        "max": round(max(values), 6),
        "coefficient_of_variation": round(variation, 6),
    }


def _validate_result(
    result: Mapping[str, Any],
    task: Mapping[str, Any],
    adapter: Mapping[str, Any],
    condition: str,
) -> Dict[str, Any]:
    task_id = str(task["id"])
    if result.get("repository_revision") != task["repository_revision"]:
        raise ManifestError("repository revision does not match task provenance: {}".format(task_id))
    if result.get("container_digest") != task["container_digest"]:
        raise ManifestError("container digest does not match task provenance: {}".format(task_id))
    if result.get("adapter_id") != adapter["adapter_id"]:
        raise ManifestError("repository result adapter does not match contract: {}".format(task_id))
    isolation = result.get("isolation")
    if not isinstance(isolation, dict) or isolation.get("verified") is not True:
        raise ManifestError("customization isolation is not verified: {}".format(task_id))
    strategy_field = "baseline_isolation" if condition == "baseline" else "adk_isolation"
    if isolation.get("strategy") != adapter[strategy_field]:
        raise ManifestError("customization isolation strategy does not match contract: {}".format(task_id))
    disabled = set(isolation.get("disabled_surfaces", []))
    enabled = set(isolation.get("enabled_surfaces", []))
    if condition == "baseline":
        if disabled != CUSTOMIZATION_SURFACES or enabled:
            raise ManifestError("baseline customization surfaces are not fully isolated: {}".format(task_id))
    else:
        if enabled != set(adapter["adk_enabled_surfaces"]):
            raise ManifestError("ADK customization surfaces do not match the reviewed profile: {}".format(task_id))
        if not set(adapter["always_disabled_surfaces"]) <= disabled or enabled & disabled:
            raise ManifestError("ADK disabled customization surfaces are invalid: {}".format(task_id))
    outcome = result.get("outcome")
    if not isinstance(outcome, dict) or outcome.get("status") not in {"pass", "fail"}:
        raise ManifestError("repository outcome is invalid: {}".format(task_id))
    functional = outcome.get("functional_tests_passed")
    security = outcome.get("security_tests_passed")
    skipped = outcome.get("security_tests_skipped")
    verified = outcome.get("verified_change")
    if not isinstance(functional, bool) or not isinstance(skipped, bool) or not isinstance(verified, bool):
        raise ManifestError("repository outcome booleans are incomplete: {}".format(task_id))
    if functional is False:
        if security is not None or skipped is not True or outcome["status"] != "fail" or verified is not False:
            raise ManifestError("security oracle must be skipped after functional failure: {}".format(task_id))
    else:
        if not isinstance(security, bool) or skipped is not False:
            raise ManifestError("security oracle result is required after functional success: {}".format(task_id))
        expected_pass = security is True and verified is True
        if (outcome["status"] == "pass") != expected_pass:
            raise ManifestError("repository outcome status is inconsistent: {}".format(task_id))
    process = result.get("process")
    if not isinstance(process, dict) or set(process) != PROCESS_FIELDS:
        raise ManifestError("repository process evidence is incomplete: {}".format(task_id))
    for field in (
        "regression_cycle_count",
        "blind_retry_count",
        "repeated_tool_call_without_new_evidence",
    ):
        value = process[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ManifestError("repository process counter is invalid: {}".format(task_id))
    if not isinstance(process["final_verification"], bool) or not isinstance(process["phase_order_violation"], bool):
        raise ManifestError("repository process flags are invalid: {}".format(task_id))
    invalid_process = (
        process["regression_cycle_count"] > 0
        or process["blind_retry_count"] > 0
        or process["final_verification"] is False
        or process["phase_order_violation"] is True
        or process["repeated_tool_call_without_new_evidence"] > 0
    )
    if outcome["status"] == "pass" and invalid_process:
        raise ManifestError("pass_with_invalid_process: {}".format(task_id))
    usage = result.get("usage")
    if not isinstance(usage, dict) or set(usage) != USAGE_FIELDS:
        raise ManifestError("repository usage is incomplete: {}".format(task_id))
    integer_fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "total_tokens",
        "attempts",
        "tool_calls",
        "timeouts",
    )
    for field in integer_fields:
        value = usage[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ManifestError("repository usage value is invalid: {}.{}".format(task_id, field))
    if usage["attempts"] < 1 or usage["cached_input_tokens"] > usage["input_tokens"]:
        raise ManifestError("repository usage attempt/cache evidence is invalid: {}".format(task_id))
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise ManifestError("repository total token evidence is inconsistent: {}".format(task_id))
    for field in ("cost_usd", "elapsed_ms"):
        value = usage[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
            raise ManifestError("repository usage value is invalid: {}.{}".format(task_id, field))
    trace = result.get("trace")
    if not isinstance(trace, dict) or trace.get("raw_trace_stored") is not False or trace.get("redacted") is not True:
        raise ManifestError("repository trace boundary is invalid: {}".format(task_id))
    summary_ref = _require_string(trace, "summary_ref", "repository trace {}".format(task_id))
    summary_path = Path(summary_ref)
    if summary_path.is_absolute() or ".." in summary_path.parts:
        raise ManifestError("repository trace summary_ref must be a safe relative path: {}".format(task_id))
    _require_string(result, "recorded_at", "repository result {}".format(task_id))
    return {
        "passed": outcome["status"] == "pass",
        "invalid_process": invalid_process,
        "total_tokens": float(usage["total_tokens"]),
        "cost_usd": float(usage["cost_usd"]),
        "elapsed_ms": float(usage["elapsed_ms"]),
        "trial": int(result["trial"]),
    }


def _condition_metrics(items: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    successes = sum(1 for item in items if item["passed"])
    success_rate = round(successes / len(items), 6) if items else 0.0
    invalid_rate = round(sum(1 for item in items if item["invalid_process"]) / len(items), 6) if items else 0.0
    total_cost = sum(float(item["cost_usd"]) for item in items)
    return {
        "count": len(items),
        "successes": successes,
        "success_rate": success_rate,
        "invalid_process_rate": invalid_rate,
        "token_distribution": _distribution([float(item["total_tokens"]) for item in items]),
        "cost_distribution": _distribution([float(item["cost_usd"]) for item in items]),
        "elapsed_distribution_ms": _distribution([float(item["elapsed_ms"]) for item in items]),
        "cost_per_success": round(total_cost / successes, 6) if successes else None,
    }


def certify_repository_report(manifest: Manifest, contract_path: Path, report_path: Path) -> Dict[str, Any]:
    contract, tasks_path, tasks = load_repository_contract(manifest, contract_path)
    report = _load_object(report_path.resolve(), "repository evaluation report")
    if report.get("schema") != REPORT_SCHEMA or report.get("status") != "complete":
        raise ManifestError("repository evaluation report is not a complete v1 report")
    if report.get("contract_sha256") != _digest(contract):
        raise ManifestError("repository evaluation contract digest does not match report")
    if report.get("tasks_sha256") != sha256_file(tasks_path):
        raise ManifestError("repository evaluation task digest does not match report")
    expected_header = {
        "task_count": len(tasks),
        "runtimes": contract["runtimes"],
        "conditions": contract["conditions"],
        "trials": contract["trials"],
    }
    if any(report.get(key) != value for key, value in expected_header.items()):
        raise ManifestError("repository evaluation report header does not match contract")
    results = report.get("results")
    if not isinstance(results, list):
        raise ManifestError("repository evaluation results are missing")
    tasks_by_id = {str(task["id"]): task for task in tasks}
    expected = {
        (task_id, runtime, condition, trial)
        for task_id in tasks_by_id
        for runtime in contract["runtimes"]
        for condition in contract["conditions"]
        for trial in range(1, int(contract["trials"]) + 1)
    }
    seen = set()
    validated: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ManifestError("repository evaluation result must be an object")
        trial_value = result.get("trial")
        if isinstance(trial_value, bool) or not isinstance(trial_value, int):
            raise ManifestError("repository evaluation result trial must be an integer")
        identity = (
            result.get("task_id"),
            result.get("runtime"),
            result.get("condition"),
            trial_value,
        )
        if identity not in expected or identity in seen:
            raise ManifestError("repository evaluation result identity is invalid or duplicated")
        seen.add(identity)
        task_id, runtime, condition, _ = identity
        value = _validate_result(
            result,
            tasks_by_id[str(task_id)],
            contract["runtime_adapters"][str(runtime)],
            str(condition),
        )
        validated.setdefault((str(runtime), str(condition)), []).append(value)
    if seen != expected:
        raise ManifestError("repository evaluation result matrix is incomplete")
    thresholds = contract["thresholds"]
    runtime_metrics: Dict[str, Any] = {}
    for runtime in contract["runtimes"]:
        baseline_items = validated[(runtime, "baseline")]
        candidate_items = validated[(runtime, "adk")]
        baseline = _condition_metrics(baseline_items)
        candidate = _condition_metrics(candidate_items)
        success_delta = round(candidate["success_rate"] - baseline["success_rate"], 6)
        if candidate["success_rate"] < float(thresholds["candidate_success_rate"]):
            raise ManifestError("candidate success rate is below threshold: {}".format(runtime))
        if success_delta < float(thresholds["minimum_success_delta"]):
            raise ManifestError("candidate success delta is below threshold: {}".format(runtime))
        if candidate["invalid_process_rate"] > float(thresholds["maximum_invalid_process_rate"]):
            raise ManifestError("candidate invalid process rate exceeds threshold: {}".format(runtime))
        if candidate["cost_per_success"] is None or candidate["cost_per_success"] > float(
            thresholds["maximum_cost_per_success_usd"]
        ):
            raise ManifestError("candidate cost per success exceeds threshold: {}".format(runtime))
        baseline_p95 = float(baseline["token_distribution"]["p95"])
        candidate_p95 = float(candidate["token_distribution"]["p95"])
        token_ratio = round(candidate_p95 / baseline_p95, 6) if baseline_p95 else None
        if token_ratio is None or token_ratio > float(thresholds["maximum_token_p95_ratio"]):
            raise ManifestError("candidate token p95 ratio exceeds threshold: {}".format(runtime))
        non_regression_trials = 0
        for trial in range(1, int(contract["trials"]) + 1):
            baseline_trial = [item for item in baseline_items if item["trial"] == trial]
            candidate_trial = [item for item in candidate_items if item["trial"] == trial]
            base_rate = sum(1 for item in baseline_trial if item["passed"]) / len(baseline_trial)
            candidate_rate = sum(1 for item in candidate_trial if item["passed"]) / len(candidate_trial)
            if candidate_rate >= base_rate:
                non_regression_trials += 1
        if non_regression_trials < int(thresholds["required_non_regression_trials"]):
            raise ManifestError("candidate non-regression trial count is below threshold: {}".format(runtime))
        runtime_metrics[runtime] = {
            "baseline": baseline,
            "adk": candidate,
            "success_delta": success_delta,
            "token_p95_ratio": token_ratio,
            "non_regression_trials": non_regression_trials,
        }
    fixture_only = all(
        task["source_kind"] == "clean-room-fixture" and task["execution_status"] == "fixture-only"
        for task in tasks
    )
    if not fixture_only:
        unavailable = [
            runtime
            for runtime, adapter in contract["runtime_adapters"].items()
            if adapter["status"] != "available"
        ]
        if unavailable:
            raise ManifestError(
                "real repository certification requires available version-pinned adapters: {}".format(
                    ",".join(sorted(unavailable))
                )
            )
    certification = {
        "schema": CERTIFICATION_SCHEMA,
        "status": "fixture-pass" if fixture_only else "pass",
        "contract_id": contract["contract_id"],
        "contract_sha256": _digest(contract),
        "tasks_sha256": sha256_file(tasks_path),
        "task_count": len(tasks),
        "result_count": len(results),
        "runtime_metrics": runtime_metrics,
        "external_execution_boundary": "fixture-validation-only" if fixture_only else "report-validation-only",
        "raw_trace_stored": False,
    }
    certification["certification_sha256"] = _digest(certification)
    return certification
