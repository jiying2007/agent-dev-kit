"""Deterministic campaign domain model, persistence, and evidence projection."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

from .evaluation import BASELINE_CATEGORIES
from .evaluation_runtime import load_tasks
from .model import Manifest, ManifestError, ensure_within

CONTRACT_SCHEMA = "adk-runtime-eval-campaign/v1"
PLAN_SCHEMA = "adk-runtime-eval-campaign-plan/v1"
RESULT_SCHEMA = "adk-runtime-eval-campaign-result/v1"
TASK_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
MODEL_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _load_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("invalid {} JSON: {}".format(label, path)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} JSON root must be an object".format(label))
    return value


def load_campaign_contract(
    manifest: Manifest, contract_path: Path
) -> Tuple[Dict[str, Any], Path, List[Mapping[str, Any]]]:
    contract_path = ensure_within(contract_path.resolve(), manifest.root, "campaign contract")
    contract = _load_json_object(contract_path, "campaign contract")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ManifestError("unsupported campaign contract schema")
    campaign_id = contract.get("campaign_id")
    if not isinstance(campaign_id, str) or not TASK_ID_RE.fullmatch(campaign_id):
        raise ManifestError("campaign_id must be a stable identifier")
    tasks_value = contract.get("tasks")
    if not isinstance(tasks_value, str) or not tasks_value:
        raise ManifestError("campaign tasks path is required")
    tasks_path = ensure_within(manifest.root / tasks_value, manifest.root, "campaign tasks")
    tasks = load_tasks(tasks_path)
    task_ids = [str(task.get("id", "")) for task in tasks]
    if any(not TASK_ID_RE.fullmatch(task_id) for task_id in task_ids):
        raise ManifestError("campaign task IDs must be stable identifiers")
    if len(set(task_ids)) != len(task_ids):
        raise ManifestError("campaign task IDs must be unique")
    managed_skills = {
        str(item.get("name"))
        for item in manifest.data.get("skills", [])
        if isinstance(item, dict) and item.get("name")
    }
    for task in tasks:
        if task["category"] not in BASELINE_CATEGORIES:
            raise ManifestError("campaign task has unsupported baseline category: {}".format(task["id"]))
        if task["expected_skill"] not in managed_skills:
            raise ManifestError("campaign task has unmanaged expected_skill: {}".format(task["id"]))

    runtimes = contract.get("runtimes")
    conditions = contract.get("conditions")
    trials = contract.get("trials")
    if runtimes != ["codex", "claude"]:
        raise ManifestError("M5 campaign runtimes must be [codex, claude]")
    runtime_models = contract.get("runtime_models")
    if not isinstance(runtime_models, dict) or set(runtime_models) != set(runtimes):
        raise ManifestError("campaign runtime_models must name every runtime exactly once")
    if any(
        not isinstance(runtime_models[runtime], str)
        or not MODEL_ID_RE.fullmatch(runtime_models[runtime])
        for runtime in runtimes
    ):
        raise ManifestError("campaign runtime model names must be non-empty strings")
    if conditions != ["baseline", "adk"]:
        raise ManifestError("M5 campaign conditions must be [baseline, adk]")
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 1 or trials > 10:
        raise ManifestError("campaign trials must be between 1 and 10")
    minimum_tasks = contract.get("minimum_tasks")
    if isinstance(minimum_tasks, bool) or not isinstance(minimum_tasks, int) or minimum_tasks < 1:
        raise ManifestError("campaign minimum_tasks must be a positive integer")
    if len(tasks) < minimum_tasks:
        raise ManifestError("campaign task set is below minimum_tasks")
    budget = contract.get("max_budget_usd")
    per_call = contract.get("max_claude_call_usd")
    if (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(float(budget))
        or budget <= 0
        or budget > 150
    ):
        raise ManifestError("campaign max_budget_usd must be between 0 and 150")
    if (
        isinstance(per_call, bool)
        or not isinstance(per_call, (int, float))
        or not math.isfinite(float(per_call))
        or per_call <= 0
        or per_call > 0.25
    ):
        raise ManifestError("max_claude_call_usd must be between 0 and 0.25")
    retry_limit = contract.get("retry_limit")
    if isinstance(retry_limit, bool) or not isinstance(retry_limit, int) or retry_limit < 0 or retry_limit > 1:
        raise ManifestError("campaign retry_limit must be 0 or 1")
    thresholds = contract.get("thresholds")
    required_thresholds = (
        "candidate_success_rate",
        "candidate_route_accuracy",
        "candidate_safety_accuracy",
        "minimum_success_delta",
        "latency_ratio_max",
        "usage_ratio_max",
        "required_non_regression_trials",
    )
    if not isinstance(thresholds, dict) or set(thresholds) != set(required_thresholds):
        raise ManifestError("campaign thresholds are incomplete")
    rate_thresholds = (
        "candidate_success_rate",
        "candidate_route_accuracy",
        "candidate_safety_accuracy",
        "minimum_success_delta",
    )
    if any(
        isinstance(thresholds[name], bool)
        or not isinstance(thresholds[name], (int, float))
        or not math.isfinite(float(thresholds[name]))
        or float(thresholds[name]) < 0
        or float(thresholds[name]) > 1
        for name in rate_thresholds
    ):
        raise ManifestError("campaign rate thresholds must be between 0 and 1")
    for name in ("latency_ratio_max", "usage_ratio_max"):
        value = thresholds[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            raise ManifestError("campaign {} must be a positive number".format(name))
    required_trials = thresholds["required_non_regression_trials"]
    if (
        isinstance(required_trials, bool)
        or not isinstance(required_trials, int)
        or required_trials < 1
        or required_trials > trials
    ):
        raise ManifestError("required_non_regression_trials must be between 1 and trials")
    return contract, tasks_path, tasks


def _validate_plan_integrity(plan: Mapping[str, Any]) -> None:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ManifestError("unsupported campaign plan schema")
    stored_digest = plan.get("plan_sha256")
    without_digest = dict(plan)
    without_digest.pop("plan_sha256", None)
    if stored_digest != _digest(without_digest):
        raise ManifestError("campaign plan digest does not match content")


def _runtime_entry(plan: Mapping[str, Any], runtime: str) -> Mapping[str, Any]:
    entries = plan.get("runtimes")
    if not isinstance(entries, list):
        raise ManifestError("campaign plan runtimes are invalid")
    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("runtime") == runtime]
    if len(matches) != 1:
        raise ManifestError("campaign plan runtime entry is missing or duplicated: {}".format(runtime))
    return matches[0]


def _result_path(state_dir: Path, runtime: str, condition: str, trial: int, task_id: str) -> Path:
    return state_dir / "results" / runtime / condition / ("trial-{:02d}".format(trial)) / (task_id + ".json")


def _attempt_from_report(report: Mapping[str, Any], attempt: int) -> Dict[str, Any]:
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
        raise ManifestError("single-task runtime report has an invalid result")
    item = results[0]
    return {
        "attempt": attempt,
        "runtime_version": report.get("runtime_version"),
        "requested_model": report.get("requested_model"),
        "reported_models": report.get("reported_models") if isinstance(report.get("reported_models"), list) else [],
        "status": item.get("status"),
        "actual_skill": item.get("actual_skill"),
        "actual_safe": item.get("actual_safe"),
        "route_ok": item.get("route_ok"),
        "safe_ok": item.get("safe_ok"),
        "elapsed_ms": item.get("elapsed_ms"),
        "usage": item.get("usage") if isinstance(item.get("usage"), dict) else {},
        "cost_usd": item.get("cost_usd"),
        "error": item.get("error"),
    }


def _expected_result_entries(
    state_dir: Path,
    contract: Mapping[str, Any],
    tasks: Sequence[Mapping[str, Any]],
) -> List[Tuple[Path, str, str, int, Mapping[str, Any]]]:
    entries: List[Tuple[Path, str, str, int, Mapping[str, Any]]] = []
    for runtime in contract["runtimes"]:
        for condition in contract["conditions"]:
            for trial in range(1, int(contract["trials"]) + 1):
                for task in tasks:
                    entries.append(
                        (
                            _result_path(state_dir, runtime, condition, trial, str(task["id"])),
                            runtime,
                            condition,
                            trial,
                            task,
                        )
                    )
    return entries


def _validated_existing_state(
    state_dir: Path,
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    tasks: Sequence[Mapping[str, Any]],
    validate_result: Callable[..., Dict[str, Any]],
) -> Tuple[set, float]:
    entries = _expected_result_entries(state_dir, contract, tasks)
    expected_paths = {entry[0] for entry in entries}
    results_root = state_dir / "results"
    actual_paths = set(results_root.rglob("*.json")) if results_root.is_dir() else set()
    unexpected = sorted(actual_paths.difference(expected_paths))
    if unexpected:
        raise ManifestError("campaign state contains unexpected result: {}".format(unexpected[0]))

    existing = set()
    spent = 0.0
    for path, runtime, condition, trial, task in entries:
        if not path.is_file():
            continue
        record = _load_json_object(path, "campaign result")
        validate_result(
            record,
            plan,
            task,
            runtime,
            condition,
            trial,
            int(contract["retry_limit"]),
            float(contract["max_claude_call_usd"]),
        )
        if runtime == "claude":
            spent += sum(float(attempt["cost_usd"]) for attempt in record["attempts"])
        existing.add(path)
    return existing, round(spent, 6)


def campaign_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Runtime Evaluation Campaign",
        "",
        "- campaign_id: {}".format(report.get("campaign_id")),
        "- status: {}".format(report.get("status")),
        "- certified: {}".format(str(bool(report.get("certified"))).lower()),
        "- validated_results: {}/{}".format(report.get("validated_results"), report.get("expected_results")),
        "",
        "## Runtime Metrics",
        "",
        "| Runtime | Baseline success | ADK success | Route delta | Safety | P95 gate | Usage gate |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    metrics = report.get("metrics", {})
    if isinstance(metrics, dict):
        for runtime in sorted(metrics):
            value = metrics[runtime]
            gates = value.get("gates", {})
            lines.append(
                "| {} | {:.4f} | {:.4f} | {:+.4f} | {:.4f} | {} | {} |".format(
                    runtime,
                    float(value.get("baseline", {}).get("success_rate", 0)),
                    float(value.get("adk", {}).get("success_rate", 0)),
                    float(value.get("comparison", {}).get("route_delta", 0)),
                    float(value.get("adk", {}).get("safety_accuracy", 0)),
                    "PASS" if gates.get("latency_non_regression") else "FAIL",
                    "PASS" if gates.get("usage_non_regression") else "FAIL",
                )
            )
    lines.extend(["", "## Gate Failures", ""])
    failed = [name for name, value in report.get("gates", {}).items() if value is not True]
    lines.extend(["- {}".format(name) for name in failed] or ["- None"])
    return "\n".join(lines) + "\n"
