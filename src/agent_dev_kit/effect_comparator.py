"""Deterministic baseline/ADK comparison over complete test Run Evidence sets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker

from .agent_value import load_contract
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import opaque_ref_for_sha256, validate_identifier, validate_no_secrets
from .run_evidence import validate_run_evidence


COMPARISON_SCHEMA = "adk-effect-comparison/v1"
DEFAULT_SCHEMA_PACKAGE = "agent_dev_kit.schema_resources"
DEFAULT_SCHEMA_NAME = "effect-comparison-v1.schema.json"
METRIC_SPECS = {
    "task-success-rate": ("ratio", "higher"),
    "first-pass-success-rate": ("ratio", "higher"),
    "human-interventions-per-task": ("count-per-task", "lower"),
    "latency-per-task-ms": ("milliseconds", "lower"),
    "cost-per-task": ("currency-amount", "lower"),
    "token-usage-per-task": ("tokens", "lower"),
    "wrong-skill-rate": ("ratio", "lower"),
    "abstain-rate": ("ratio", "diagnostic"),
}


@dataclass(frozen=True)
class EffectCampaignInput:
    campaign_id: str
    expected_task_ids: Tuple[str, ...]
    baseline: Tuple[Mapping[str, Any], ...]
    candidate: Tuple[Mapping[str, Any], ...]
    window_from: datetime
    window_through: datetime
    as_of: datetime


def load_effect_comparison_schema(path: Optional[Path] = None) -> Mapping[str, Any]:
    try:
        raw = (
            path.read_text(encoding="utf-8")
            if path is not None
            else resources.read_text(DEFAULT_SCHEMA_PACKAGE, DEFAULT_SCHEMA_NAME, encoding="utf-8")
        )
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("effect comparison schema is invalid") from exc
    if not isinstance(value, dict):
        raise ManifestError("effect comparison schema must be an object")
    Draft202012Validator.check_schema(value)
    return value


def _iso(value: datetime, label: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ManifestError("{} must be a timezone-aware datetime".format(label))
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ManifestError("{} must be an RFC3339 timestamp".format(label))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("{} must be an RFC3339 timestamp".format(label)) from exc
    if parsed.tzinfo is None:
        raise ManifestError("{} must include a timezone".format(label))
    return parsed.astimezone(timezone.utc)


def _population_digest(task_ids: Sequence[str]) -> str:
    return sha256_bytes(canonical_json_bytes(sorted(task_ids)))


def _measured(values: Sequence[float], applicable: int, unit: str) -> Mapping[str, Any]:
    if applicable == 0:
        return {
            "status": "not-measured",
            "reason": "no-applicable-runs",
            "applicable_sample_size": 0,
            "observed_sample_size": 0,
            "coverage": None,
        }
    if len(values) != applicable:
        return {
            "status": "not-measured",
            "reason": "incomplete-coverage",
            "applicable_sample_size": applicable,
            "observed_sample_size": len(values),
            "coverage": round(len(values) / applicable, 6) if applicable else None,
        }
    return {
        "status": "measured",
        "value": round(sum(values) / applicable, 6),
        "sample_size": applicable,
        "applicable_sample_size": applicable,
        "observed_sample_size": applicable,
        "coverage": 1.0,
        "unit": unit,
    }


def _condition_metrics(runs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    summaries = [item["trace_summary"] for item in runs]
    outcomes = [item["outcome"] for item in summaries]
    success_values = [
        1.0 if item["status"] == "succeeded" else 0.0
        for item in outcomes if item["status"] != "not-available"
    ]
    non_abstain = [item for item in summaries if not item["abstained"]]
    first_pass_values = [
        1.0 if item["first_pass_success"] else 0.0
        for item in non_abstain if item["outcome"]["status"] != "not-available"
    ]
    cost_values = [
        float(item["cost"]["amount"])
        for item in summaries if item["cost"]["status"] == "available"
    ]
    token_values = [
        float(item["token_usage"]["input"] + item["token_usage"]["output"])
        for item in summaries if item["token_usage"].get("status") != "not-available"
    ]
    return {
        "task-success-rate": _measured(success_values, len(summaries), "ratio"),
        "first-pass-success-rate": _measured(first_pass_values, len(non_abstain), "ratio"),
        "human-interventions-per-task": _measured(
            [float(item["human_interventions"]) for item in summaries], len(summaries), "count-per-task"
        ),
        "latency-per-task-ms": _measured(
            [float(item["elapsed_ms"]) for item in summaries], len(summaries), "milliseconds"
        ),
        "cost-per-task": _measured(cost_values, len(summaries), "currency-amount"),
        "token-usage-per-task": _measured(token_values, len(summaries), "tokens"),
        "wrong-skill-rate": _measured(
            [1.0 if item["wrong_skill"] else 0.0 for item in summaries], len(summaries), "ratio"
        ),
        "abstain-rate": _measured(
            [1.0 if item["abstained"] else 0.0 for item in summaries], len(summaries), "ratio"
        ),
    }


def _condition_report(label: str, runs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    summaries = [item["trace_summary"] for item in runs]
    identities = {
        (item["runtime_target"], item["runtime_version"], item["model_version"])
        for item in summaries
    }
    if len(identities) != 1:
        raise ManifestError("{} condition mixes runtime or model identities".format(label))
    bundles = {item["asset_bundle_sha256"] for item in summaries}
    if len(bundles) != 1:
        raise ManifestError("{} condition mixes asset bundles".format(label))
    runtime_target, runtime_version, model_version = next(iter(identities))
    currencies = {
        item["cost"]["currency"]
        for item in summaries if item["cost"]["status"] == "available"
    }
    if len(currencies) > 1:
        raise ManifestError("{} condition mixes cost currencies".format(label))
    return {
        "condition": label,
        "task_count": len(runs),
        "asset_bundle_sha256": next(iter(bundles)),
        "runtime_target": runtime_target,
        "runtime_version": runtime_version,
        "model_version": model_version,
        "cost_currency": next(iter(currencies)) if currencies else None,
        "prompt_versions": sorted({item["prompt_version"] for item in summaries}),
        "run_evidence_refs": sorted(
            opaque_ref_for_sha256(sha256_bytes(canonical_json_bytes(item))) for item in runs
        ),
        "observation_window": {
            "from": min(_parse_time(item["observed_at"], "condition observed_at") for item in runs)
            .isoformat().replace("+00:00", "Z"),
            "through": max(_parse_time(item["observed_at"], "condition observed_at") for item in runs)
            .isoformat().replace("+00:00", "Z"),
        },
        "metrics": _condition_metrics(runs),
    }


def _deltas(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    result = {}
    for name, (_, direction) in METRIC_SPECS.items():
        left = baseline["metrics"][name]
        right = candidate["metrics"][name]
        if left["status"] != "measured" or right["status"] != "measured":
            result[name] = {
                "status": "not-comparable",
                "reason": "incomplete-condition-coverage",
                "direction": direction,
            }
        else:
            result[name] = {
                "status": "measured",
                "candidate_minus_baseline": round(right["value"] - left["value"], 6),
                "direction": direction,
                "unit": left["unit"],
            }
    return result


def _validate_output(value: Mapping[str, Any], schema_path: Optional[Path]) -> None:
    validate_no_secrets(value, "effect comparison")
    errors = sorted(
        Draft202012Validator(
            load_effect_comparison_schema(schema_path), format_checker=FormatChecker()
        ).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ManifestError("effect_comparison_invalid: {}: {}".format(location, errors[0].message))


def compare_effects(
    campaign: EffectCampaignInput,
    manifest: Manifest,
    agent_value_contract: Optional[Mapping[str, Any]] = None,
    schema_path: Optional[Path] = None,
) -> Mapping[str, Any]:
    if not isinstance(campaign, EffectCampaignInput):
        raise ManifestError("effect campaign input must be typed")
    validate_identifier(campaign.campaign_id, "effect campaign_id")
    expected = list(campaign.expected_task_ids)
    if not expected or len(expected) != len(set(expected)):
        raise ManifestError("effect campaign task population must be non-empty and unique")
    for task_id in expected:
        validate_identifier(task_id, "effect task_id")
    window_from = _parse_time(_iso(campaign.window_from, "window_from"), "window_from")
    window_through = _parse_time(_iso(campaign.window_through, "window_through"), "window_through")
    as_of = _parse_time(_iso(campaign.as_of, "as_of"), "as_of")
    if not window_from <= window_through <= as_of <= datetime.now(timezone.utc):
        raise ManifestError("effect campaign window must satisfy from <= through <= as_of <= now")
    contract = agent_value_contract or load_contract(
        manifest.root / "manifests" / "agent_value_contracts.json"
    )

    indexed = {}
    for label, condition in (("baseline", campaign.baseline), ("candidate", campaign.candidate)):
        if not isinstance(condition, tuple):
            raise ManifestError("{} condition must be an immutable tuple".format(label))
        by_task = {}
        run_ids = set()
        for raw in condition:
            value = validate_run_evidence(raw, manifest, contract)
            summary = value["trace_summary"]
            task_id = summary["task_id"]
            if task_id in by_task or summary["run_id"] in run_ids:
                raise ManifestError("{} condition contains duplicate task or run".format(label))
            observed_at = _parse_time(value["observed_at"], "effect observed_at")
            if not window_from <= observed_at <= window_through:
                raise ManifestError("{} run is outside the fixed campaign window".format(label))
            by_task[task_id] = value
            run_ids.add(summary["run_id"])
        if set(by_task) != set(expected):
            raise ManifestError("{} condition does not cover the complete task population".format(label))
        indexed[label] = by_task

    for task_id in expected:
        left = indexed["baseline"][task_id]["trace_summary"]
        right = indexed["candidate"][task_id]["trace_summary"]
        left_identity = (left["runtime_target"], left["runtime_version"], left["model_version"])
        right_identity = (right["runtime_target"], right["runtime_version"], right["model_version"])
        if left_identity != right_identity:
            raise ManifestError("effect conditions differ in runtime/model identity for a task")

    baseline_run_ids = {
        item["trace_summary"]["run_id"] for item in indexed["baseline"].values()
    }
    candidate_run_ids = {
        item["trace_summary"]["run_id"] for item in indexed["candidate"].values()
    }
    if baseline_run_ids & candidate_run_ids:
        raise ManifestError("effect conditions must use independent run identities")

    baseline_runs = [indexed["baseline"][task_id] for task_id in sorted(expected)]
    candidate_runs = [indexed["candidate"][task_id] for task_id in sorted(expected)]
    baseline_report = _condition_report("baseline", baseline_runs)
    candidate_report = _condition_report("candidate", candidate_runs)
    if baseline_report["asset_bundle_sha256"] == candidate_report["asset_bundle_sha256"]:
        raise ManifestError("effect conditions must bind distinct baseline and candidate bundles")
    if (
        baseline_report["metrics"]["cost-per-task"]["status"] == "measured"
        and candidate_report["metrics"]["cost-per-task"]["status"] == "measured"
        and baseline_report["cost_currency"] != candidate_report["cost_currency"]
    ):
        raise ManifestError("effect conditions use different cost currencies")
    value = {
        "schema_version": COMPARISON_SCHEMA,
        "campaign_id": campaign.campaign_id,
        "task_population": {
            "count": len(expected),
            "digest": _population_digest(expected),
            "coverage": "complete",
        },
        "window": {
            "from": _iso(window_from, "window_from"),
            "through": _iso(window_through, "window_through"),
            "as_of": _iso(as_of, "as_of"),
        },
        "baseline": baseline_report,
        "candidate": candidate_report,
        "deltas": _deltas(baseline_report, candidate_report),
        "evidence_scope": "test-only",
        "quality_evidence_eligible": False,
        "owner_review_required": True,
        "lifecycle_authority": "none-evidence-only",
        "raw_content_stored": False,
    }
    _validate_output(value, schema_path)
    return value
