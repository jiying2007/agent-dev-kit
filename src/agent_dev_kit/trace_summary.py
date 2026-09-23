"""Strict validation for privacy-bounded ADK workflow trace summaries."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple, Union

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .model import ManifestError
from .privacy_ref import (
    validate_identifier,
    validate_no_secrets,
    validate_opaque_ref,
    validate_sha256,
)


TRACE_SUMMARY_SCHEMA = "adk-workflow-trace-summary/v2"
DEFAULT_SCHEMA_PACKAGE = "agent_dev_kit.schema_resources"
DEFAULT_SCHEMA_NAME = "adk-workflow-trace-summary-v2.schema.json"

_OUTCOME_CATEGORIES = {
    "succeeded": frozenset({"completed"}),
    "failed": frozenset({"validation-failure", "runtime-failure"}),
    "blocked": frozenset({"permission-blocked", "external-blocked"}),
    "cancelled": frozenset({"cancelled"}),
    "abstained": frozenset({"no-match"}),
}


@dataclass(frozen=True)
class MetricUnavailable:
    """Explicit absence of runtime evidence; never represented as a zero value."""

    reason: str


@dataclass(frozen=True)
class ToolUseFact:
    name: str
    call_count: int
    outcome: str


@dataclass(frozen=True)
class HandoffFact:
    target: str
    outcome: str


@dataclass(frozen=True)
class GuardrailFact:
    name: str
    status: str


@dataclass(frozen=True)
class VerificationFact:
    name: str
    status: str
    evidence_ref: Optional[str]


@dataclass(frozen=True)
class TokenUsageFact:
    input: int
    cached_input: int
    output: int


@dataclass(frozen=True)
class CostFact:
    amount: float
    currency: str


@dataclass(frozen=True)
class OutcomeFact:
    status: str
    category: str


@dataclass(frozen=True)
class TraceRunFacts:
    """Typed, privacy-bounded facts for exactly one workflow run.

    Token, cost, and outcome evidence are deliberately optional.  Absence is
    emitted as an explicit ``not-available`` reason rather than inferred as
    zero, failure, or success.
    """

    run_id: str
    task_id: str
    asset_bundle_sha256: str
    runtime_target: str
    runtime_version: str
    model_version: str
    goal_ref: str
    primary_skill: str
    prompt_version: str
    orchestration_mode: str
    tools_used: Tuple[ToolUseFact, ...]
    handoffs: Tuple[HandoffFact, ...]
    guardrails: Tuple[GuardrailFact, ...]
    verification: Tuple[VerificationFact, ...]
    elapsed_ms: int
    first_pass_success: bool
    human_interventions: int
    wrong_skill: bool
    abstained: bool
    privacy_status: str
    blockers: Tuple[str, ...]
    failure_pattern: str
    next_goal_ref: Optional[str]
    token_usage: Union[TokenUsageFact, MetricUnavailable, None] = None
    cost: Union[CostFact, MetricUnavailable, None] = None
    outcome: Union[OutcomeFact, MetricUnavailable, None] = None


def _unavailable_metric(value: Optional[MetricUnavailable], default_reason: str) -> Mapping[str, Any]:
    reason = value.reason if value is not None else default_reason
    return {"status": "not-available", "reason": reason}


def emit_trace_summary_v2(facts: TraceRunFacts) -> Mapping[str, Any]:
    """Emit one validated v2 summary from caller-observed facts.

    This is an explicit per-run library API.  It performs no runtime probing,
    persistence, pricing lookup, token estimation, or outcome inference.
    """

    if not isinstance(facts, TraceRunFacts):
        raise ManifestError("trace_emitter_invalid: facts must be TraceRunFacts")

    if facts.token_usage is None or isinstance(facts.token_usage, MetricUnavailable):
        token_usage: Mapping[str, Any] = _unavailable_metric(
            facts.token_usage,
            "runtime-token-usage-unavailable",
        )
    elif isinstance(facts.token_usage, TokenUsageFact):
        token_usage = {
            "input": facts.token_usage.input,
            "cached_input": facts.token_usage.cached_input,
            "output": facts.token_usage.output,
        }
    else:
        raise ManifestError("trace_emitter_invalid: token_usage has an unsupported typed fact")

    if facts.cost is None or isinstance(facts.cost, MetricUnavailable):
        cost: Mapping[str, Any] = _unavailable_metric(
            facts.cost,
            "runtime-pricing-unavailable",
        )
    elif isinstance(facts.cost, CostFact):
        cost = {"status": "available", "amount": facts.cost.amount, "currency": facts.cost.currency}
    else:
        raise ManifestError("trace_emitter_invalid: cost has an unsupported typed fact")

    if facts.outcome is None or isinstance(facts.outcome, MetricUnavailable):
        outcome: Mapping[str, Any] = _unavailable_metric(
            facts.outcome,
            "runtime-outcome-unavailable",
        )
    elif isinstance(facts.outcome, OutcomeFact):
        outcome = {"status": facts.outcome.status, "category": facts.outcome.category}
    else:
        raise ManifestError("trace_emitter_invalid: outcome has an unsupported typed fact")

    summary = {
        "schema_version": TRACE_SUMMARY_SCHEMA,
        "run_id": facts.run_id,
        "task_id": facts.task_id,
        "asset_bundle_sha256": facts.asset_bundle_sha256,
        "runtime_target": facts.runtime_target,
        "runtime_version": facts.runtime_version,
        "model_version": facts.model_version,
        "goal_ref": facts.goal_ref,
        "primary_skill": facts.primary_skill,
        "prompt_version": facts.prompt_version,
        "orchestration_mode": facts.orchestration_mode,
        "tool_calls": sum(item.call_count for item in facts.tools_used),
        "tools_used": [
            {"name": item.name, "call_count": item.call_count, "outcome": item.outcome}
            for item in facts.tools_used
        ],
        "handoffs": [
            {"target": item.target, "outcome": item.outcome}
            for item in facts.handoffs
        ],
        "guardrails": [
            {"name": item.name, "status": item.status}
            for item in facts.guardrails
        ],
        "verification": [
            {"name": item.name, "status": item.status, "evidence_ref": item.evidence_ref}
            for item in facts.verification
        ],
        "token_usage": token_usage,
        "cost": cost,
        "elapsed_ms": facts.elapsed_ms,
        "outcome": outcome,
        "first_pass_success": facts.first_pass_success,
        "human_interventions": facts.human_interventions,
        "wrong_skill": facts.wrong_skill,
        "abstained": facts.abstained,
        "privacy_status": facts.privacy_status,
        "raw_content_stored": False,
        "blockers": list(facts.blockers),
        "failure_pattern": facts.failure_pattern,
        "next_goal_ref": facts.next_goal_ref,
    }
    return validate_trace_summary(summary)


def load_trace_summary_schema(path: Optional[Path] = None) -> Mapping[str, Any]:
    """Load and meta-validate the version-pinned trace summary JSON Schema."""

    try:
        raw = (
            path.read_text(encoding="utf-8")
            if path is not None
            else resources.read_text(DEFAULT_SCHEMA_PACKAGE, DEFAULT_SCHEMA_NAME, encoding="utf-8")
        )
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(
            "trace summary schema is invalid JSON: {}".format(path or DEFAULT_SCHEMA_NAME)
        ) from exc
    if not isinstance(value, dict):
        raise ManifestError(
            "trace summary schema must be a JSON object: {}".format(path or DEFAULT_SCHEMA_NAME)
        )
    try:
        Draft202012Validator.check_schema(value)
    except SchemaError as exc:
        raise ManifestError("trace summary schema is not valid Draft 2020-12: {}".format(exc.message)) from exc
    return value


def _schema_failures(value: Any, schema: Mapping[str, Any]) -> Tuple[str, ...]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        failures.append("{}: {}".format(location, error.message))
    return tuple(failures)


def validate_trace_summary(
    value: Any,
    schema: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Validate schema shape, privacy boundary, and cross-field invariants.

    The function validates evidence supplied by a caller.  It does not emit a
    trace summary or infer unavailable runtime metrics.
    """

    validate_no_secrets(value, "trace summary")
    active_schema = schema if schema is not None else load_trace_summary_schema()
    failures = _schema_failures(value, active_schema)
    if failures:
        raise ManifestError("trace_summary_invalid: {}".format("; ".join(failures)))
    if not isinstance(value, dict):
        raise ManifestError("trace_summary_invalid: <root>: must be an object")
    validate_sha256(value["asset_bundle_sha256"], "trace asset_bundle_sha256")
    for field in (
        "run_id", "task_id", "runtime_target", "runtime_version", "model_version",
        "primary_skill", "prompt_version", "failure_pattern",
    ):
        validate_identifier(value[field], "trace {}".format(field))
    validate_opaque_ref(value["goal_ref"], "trace goal_ref")
    if value["next_goal_ref"] is not None:
        validate_opaque_ref(value["next_goal_ref"], "trace next_goal_ref")
    for item in value["tools_used"]:
        validate_identifier(item["name"], "trace tool name")
    for item in value["handoffs"]:
        validate_identifier(item["target"], "trace handoff target")
    for item in value["guardrails"]:
        validate_identifier(item["name"], "trace guardrail name")
    for item in value["verification"]:
        validate_identifier(item["name"], "trace verification name")
        if item["evidence_ref"] is not None:
            validate_opaque_ref(item["evidence_ref"], "trace verification evidence_ref")
    for blocker in value["blockers"]:
        validate_identifier(blocker, "trace blocker")
    if value["cost"]["status"] == "not-available":
        validate_identifier(value["cost"]["reason"], "trace cost reason")

    token_usage = value["token_usage"]
    if token_usage.get("status") == "not-available":
        validate_identifier(token_usage["reason"], "trace token_usage reason")
    elif token_usage["cached_input"] > token_usage["input"]:
        raise ManifestError("trace_summary_invalid: token_usage/cached_input must not exceed input")
    observed_tool_calls = sum(item["call_count"] for item in value["tools_used"])
    if value["tool_calls"] != observed_tool_calls:
        raise ManifestError("trace_summary_invalid: tool_calls must equal tools_used call_count total")

    cost = value["cost"]
    if cost["status"] == "available" and not math.isfinite(cost["amount"]):
        raise ManifestError("trace_summary_invalid: cost/amount must be finite")

    outcome_status = value["outcome"]["status"]
    if outcome_status == "not-available":
        validate_identifier(value["outcome"]["reason"], "trace outcome reason")
        if value["first_pass_success"] or value["abstained"]:
            raise ManifestError(
                "trace_summary_invalid: unavailable outcome excludes first_pass_success and abstained"
            )
    else:
        outcome_category = value["outcome"]["category"]
        if outcome_category not in _OUTCOME_CATEGORIES[outcome_status]:
            raise ManifestError("trace_summary_invalid: outcome/status and outcome/category do not match")
    abstained = value["abstained"]
    if outcome_status != "not-available" and abstained != (outcome_status == "abstained"):
        raise ManifestError("trace_summary_invalid: abstained must match outcome/status=abstained")
    if abstained and value["wrong_skill"]:
        raise ManifestError("trace_summary_invalid: abstained and wrong_skill cannot both be true")
    failed_verification = any(item["status"] in {"failed", "not-run"} for item in value["verification"])
    failed_guardrail = any(item["status"] == "failed" for item in value["guardrails"])
    if outcome_status == "succeeded":
        if failed_verification or failed_guardrail:
            raise ManifestError("trace_summary_invalid: succeeded outcome cannot contain failed checks")
        if value["blockers"] or value["failure_pattern"] != "none":
            raise ManifestError("trace_summary_invalid: succeeded outcome cannot contain blockers or failure pattern")
    if value["first_pass_success"]:
        if outcome_status != "succeeded":
            raise ManifestError("trace_summary_invalid: first_pass_success requires a succeeded outcome")
        if value["human_interventions"] != 0:
            raise ManifestError("trace_summary_invalid: first_pass_success requires zero human_interventions")
        if value["wrong_skill"] or abstained:
            raise ManifestError("trace_summary_invalid: first_pass_success excludes wrong_skill and abstained")
        if not value["verification"] or not any(item["status"] == "passed" for item in value["verification"]):
            raise ManifestError("trace_summary_invalid: first_pass_success requires passed verification evidence")

    return value
