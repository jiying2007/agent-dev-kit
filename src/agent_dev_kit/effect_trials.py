"""Task-clustered repetitions of the canonical single-trial comparison.

Test plans and control bindings are caller declarations, not attestations.
There is no executor, model client or lifecycle authority in this module.
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from . import effect_comparator as _effects
from .contracts.schema_loader import packaged_schema_bytes
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .privacy_ref import validate_no_secrets

INPUT_SCHEMA = "adk-effect-trials/v1"
OUTPUT_SCHEMA = "adk-effect-trial-comparison/v1"
MAX_INPUT_BYTES = 16 * 1024 * 1024
IDENTITY_FIELDS = ("runtime_target", "runtime_version", "model_version", "prompt_version", "orchestration_mode")


def _ref(value: Any) -> str:
    return "ref:" + sha256_bytes(canonical_json_bytes(value))


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ManifestError("trial timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ManifestError("trial input contains a non-finite number")
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite(item)


def _validate(document: Mapping[str, Any]) -> Mapping[str, Any]:
    _finite(document)
    validate_no_secrets(document, "effect trial input")
    validator = Draft202012Validator(
        json.loads(packaged_schema_bytes("effect-trials-v1.schema.json")), format_checker=FormatChecker()
    )
    error = next(validator.iter_errors(document), None)
    if error is not None:
        location = "/".join(map(str, error.absolute_path)) or "<root>"
        raise ManifestError("invalid trial input at " + location)
    plan = document["plan"]
    start, through, as_of = (_time(plan["window"][name]) for name in ("from", "through", "as_of"))
    if not _time(plan["registered_at"]) <= start <= through <= as_of <= datetime.now(timezone.utc):
        raise ManifestError("trial plan must precede its fixed observation window")
    tasks, trials = plan["task_ids"], plan["trial_ids"]
    if len(tasks) * len(trials) > 2000 or plan["policy"]["bootstrap_samples"] * len(tasks) > 2000000:
        raise ManifestError("trial campaign exceeds bounded evaluation budget")
    if plan["bundles"]["baseline"] == plan["bundles"]["candidate"]:
        raise ManifestError("trial conditions must use distinct asset bundles")
    policy = plan["policy"]
    for name in (policy["primary_metric"], *policy["guardrails"]):
        if name not in _effects.METRIC_SPECS or _effects.METRIC_SPECS[name][1] == "diagnostic":
            raise ManifestError("trial policy metric must be a supported directional metric")
    if not {"task-success-rate", "wrong-skill-rate"} <= set(policy["guardrails"]):
        raise ManifestError("trial policy must guard success and wrong-skill rates")
    return plan


def _quantile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _distribution(values: Sequence[float]) -> dict[str, Any]:
    return {
        "count": len(values), "mean": round(sum(values) / len(values), 6),
        "median": round(_quantile(values, 0.5), 6), "p95": round(_quantile(values, 0.95), 6),
        "minimum": min(values), "maximum": max(values),
    }


def _paired_metric(left: Sequence[float], right: Sequence[float], policy: Mapping[str, Any], direction: str) -> dict[str, Any]:
    differences = [b - a for a, b in zip(left, right)]
    generator = random.Random(policy["bootstrap_seed"])
    n = len(differences)
    sampled = [sum(differences[generator.randrange(n)] for _ in range(n)) / n
               for _ in range(policy["bootstrap_samples"])]
    family = len(set(policy["guardrails"]) | {policy["primary_metric"]})
    confidence = 1 - (1 - policy["confidence"]) / family
    tail = (1 - confidence) / 2
    low, high = _quantile(sampled, tail), _quantile(sampled, 1 - tail)
    benefit = (low, high) if direction == "higher" else (-high, -low)
    return {
        "status": "measured", "task_count": n, "sampling_unit": "task",
        "baseline": _distribution(left), "candidate": _distribution(right),
        "candidate_minus_baseline": round(sum(differences) / n, 6),
        "difference_interval": [low, high], "benefit_interval": list(benefit) if direction != "diagnostic" else None,
        "confidence": confidence, "method": "paired-task-percentile-bootstrap-bonferroni",
        "direction": direction,
    }


def _verdict(metrics: Mapping[str, Any], plan: Mapping[str, Any], *, infra_failed: bool, unsafe: bool) -> tuple[str, str]:
    if infra_failed:
        return "invalid", "infrastructure-failure-no-selective-exclusion"
    if unsafe:
        return "regressed", "observed-guardrail-failure"
    policy = plan["policy"]
    if plan["controls"]["model_identity"] != "revision-bound":
        return "inconclusive", "model-alias-not-an-immutable-identity"
    if len(plan["task_ids"]) < policy["minimum_tasks"] or len(plan["trial_ids"]) < policy["minimum_trials"]:
        return "inconclusive", "insufficient-independent-tasks-or-trials"
    required = set(policy["guardrails"]) | {policy["primary_metric"]}
    if any(metrics[name]["status"] != "measured" for name in required):
        return "inconclusive", "required-metric-unavailable"
    uncertain_guard = False
    for name, margin in policy["guardrails"].items():
        low, high = metrics[name]["benefit_interval"]
        if high < -margin:
            return "regressed", "guardrail-regression:" + name
        uncertain_guard |= low < -margin
    if uncertain_guard:
        return "inconclusive", "guardrail-non-inferiority-unproven"
    low, high = metrics[policy["primary_metric"]]["benefit_interval"]
    if high < -policy["noninferiority_margin"]:
        return "regressed", "primary-metric-regression"
    if low > policy["minimum_effect"]:
        return "improved", "primary-benefit-exceeds-declared-threshold"
    if low >= -policy["noninferiority_margin"]:
        return "non-inferior", "within-declared-non-inferiority-margin"
    return "inconclusive", "uncertainty-crosses-decision-boundary"


def compare_effect_trials(document: Mapping[str, Any], manifest: Manifest) -> dict[str, Any]:
    """Validate complete trials using existing Run Evidence and comparison authority."""
    plan = _validate(document)
    plan_ref, controls_ref = _ref(plan), _ref(plan["controls"])
    tasks = sorted(plan["task_ids"])
    expected_trials = set(plan["trial_ids"])
    observed_trials: set[str] = set()
    run_ids: set[str] = set()
    currencies: set[str] = set()
    grouped: dict[str, dict[str, list[Mapping[str, Any]]]] = {
        side: {task: [] for task in tasks} for side in ("baseline", "candidate")
    }
    trial_refs = []
    outcomes: dict[str, Counter[str]] = {side: Counter() for side in grouped}
    infra_failed = unsafe = False
    for trial in sorted(document["trials"], key=lambda item: item["trial_id"]):
        trial_id = trial["trial_id"]
        if trial_id in observed_trials or trial_id not in expected_trials:
            raise ManifestError("duplicate or unexpected trial identity")
        observed_trials.add(trial_id)
        infra_failed |= trial["infrastructure_status"] == "failed"
        conditions: dict[str, tuple[Mapping[str, Any], ...]] = {}
        for side in grouped:
            raw_runs = []
            for binding in trial[side]:
                if binding["plan_ref"] != plan_ref or binding["controls_ref"] != controls_ref:
                    raise ManifestError("trial binding differs from frozen plan or controls")
                raw_runs.append(binding["run"])
            conditions[side] = tuple(raw_runs)
        single = _effects.compare_effects(_effects.EffectCampaignInput(
            campaign_id=plan["campaign_id"], expected_task_ids=tuple(tasks),
            baseline=conditions["baseline"], candidate=conditions["candidate"],
            window_from=_time(plan["window"]["from"]), window_through=_time(plan["window"]["through"]),
            as_of=_time(plan["window"]["as_of"]),
        ), manifest)
        trial_refs.append({"trial_id": trial_id, "comparison_ref": _ref(single),
                           "infrastructure_status": trial["infrastructure_status"]})
        for side, runs in conditions.items():
            for raw in runs:
                summary = raw["trace_summary"]
                if summary["run_id"] in run_ids:
                    raise ManifestError("run identity reused across trials or conditions")
                run_ids.add(summary["run_id"])
                if any(summary[key] != plan["controls"][key] for key in IDENTITY_FIELDS):
                    raise ManifestError("observed run identity differs from frozen control variables")
                if summary["asset_bundle_sha256"] != plan["bundles"][side]:
                    raise ManifestError("observed bundle differs from declared intervention")
                if summary["cost"]["status"] == "available":
                    currencies.add(summary["cost"]["currency"])
                unsafe |= side == "candidate" and any(guard["status"] == "failed" for guard in summary["guardrails"])
                outcomes[side][summary["outcome"]["status"]] += 1
                grouped[side][summary["task_id"]].append(raw)
    if observed_trials != expected_trials:
        raise ManifestError("missing planned trials; incomplete campaigns cannot be compared")
    if len(currencies) > 1:
        raise ManifestError("cost currencies differ across trials")
    task_metrics = {
        side: {task: _effects._condition_metrics(runs) for task, runs in population.items()}
        for side, population in grouped.items()
    }
    metrics: dict[str, Any] = {}
    for name, (unit, direction) in _effects.METRIC_SPECS.items():
        cells = [task_metrics[side][task][name] for side in grouped for task in tasks]
        if any(cell["status"] != "measured" for cell in cells):
            metrics[name] = {"status": "not-comparable", "reason": "incomplete-task-metric-coverage"}
            continue
        left = [task_metrics["baseline"][task][name]["value"] for task in tasks]
        right = [task_metrics["candidate"][task][name]["value"] for task in tasks]
        metrics[name] = _paired_metric(left, right, plan["policy"], direction)
        metrics[name]["unit"] = unit
    verdict, reason = _verdict(metrics, plan, infra_failed=infra_failed, unsafe=unsafe)
    reliability = {}
    for side, population in grouped.items():
        states = [[raw["trace_summary"]["outcome"]["status"] for raw in population[task]] for task in tasks]
        if any("not-available" in task for task in states):
            reliability[side] = {"status": "not-measured", "reason": "outcome-unavailable"}
        else:
            reliability[side] = {
                "status": "measured", "task_count": len(tasks), "trials_per_task": len(expected_trials),
                "all_trials_succeeded_rate": sum(all(s == "succeeded" for s in task) for task in states) / len(tasks),
                "any_trial_succeeded_rate": sum(any(s == "succeeded" for s in task) for task in states) / len(tasks),
            }
    value = {
        "schema_version": OUTPUT_SCHEMA, "campaign_id": plan["campaign_id"],
        "plan_ref": plan_ref, "input_ref": _ref(document), "controls_ref": controls_ref,
        "verdict": verdict, "reason": reason, "task_count": len(tasks),
        "trials_per_task": len(expected_trials), "run_count": len(run_ids),
        "trial_comparisons": trial_refs, "metrics": metrics, "reliability": reliability,
        "outcome_counts": {side: dict(sorted(counter.items())) for side, counter in outcomes.items()},
        "evidence_scope": "test-only", "quality_evidence_eligible": False,
        "owner_review_required": True, "lifecycle_authority": "none-evidence-only", "release_authorized": False,
        "raw_content_stored": False, "control_authority": "caller-declared-test-bindings-not-attested",
        "limitations": ["plan timestamp is declared, not independently certified",
                        "bootstrap assumes representative independent tasks; small or degenerate samples can mislead",
                        "distributions summarize per-task trial means, not raw-run latency percentiles",
                        "family correction is within this campaign, not across adaptively selected candidates"],
    }
    _finite(value)
    validate_no_secrets(value, "effect trial comparison")
    validator = Draft202012Validator(json.loads(packaged_schema_bytes("effect-trial-comparison-v1.schema.json")))
    if next(validator.iter_errors(value), None) is not None:
        raise ManifestError("generated effect trial comparison violates its contract")
    return value


def compare_effect_trial_file(path: Path, manifest: Manifest) -> dict[str, Any]:
    """Read one bounded JSON document; never fetch references or execute tools."""
    with path.open("rb") as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ManifestError("effect trial input exceeds byte budget")
    try:
        document = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise ManifestError("invalid effect trial JSON") from exc
    return compare_effect_trials(document, manifest)