"""Read-only import of caller-observed task evidence into existing RunEvidence.

The v1 observation envelope has closed fields: schema_version, provenance, run,
input_snapshot, workspace_snapshot, events, acceptance, artifacts and
skill_exposure. File references are {path, sha256}, relative to the envelope's
directory. Snapshots are opaque bytes; events and acceptance are strict JSON.
Nothing in an imported file is executed. Digests bind supplied observations,
not the historical truth of a host or the independence of a claimed grader.
run.source_sha identifies the TASK repository's initial commit. It is not the
ADK revision: asset_bundle_sha256 and assigned Skill bytes identify that input.
"""

from __future__ import annotations

import math
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from .agent_value_contracts import load_contract
from .atomic_io import encode_json_document, validate_document_outputs, write_texts_atomic
from .model import Manifest, ManifestError, sha256_bytes
from .privacy_ref import validate_identifier, validate_sha256
from .run_evidence import RunEvidenceObservation, emit_run_evidence
from .strict_json import loads
from .trace_summary import (
    CostFact, GuardrailFact, HandoffFact, MetricUnavailable, OutcomeFact,
    TokenUsageFact, ToolUseFact, TraceRunFacts, VerificationFact,
)

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_FILES = 128
MAX_EVENTS = 4096
_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,511}")
_TOOL_OUTCOMES = {"succeeded", "partial", "failed", "blocked", "cancelled", "not-available"}


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ManifestError(f"task evidence: invalid {label} fields")
    return value


def _list(value: Any, maximum: int, label: str) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ManifestError(f"task evidence: invalid {label} count")
    return value


def _choice(value: Any, choices: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ManifestError(f"task evidence: invalid {label}")
    return value


def _integer(value: Any, label: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**53 - 1:
        raise ManifestError(f"task evidence: invalid {label}")
    return value


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ManifestError("task evidence: invalid timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("task evidence: invalid timestamp") from exc
    if result.tzinfo is None:
        raise ManifestError("task evidence: timestamp needs timezone")
    return result


def _relative(value: Any) -> str:
    if (not isinstance(value, str) or _PATH.fullmatch(value) is None
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ManifestError("task evidence: unsafe relative path")
    return value


def _reference(value: Any) -> tuple[str, str]:
    item = _object(value, {"path", "sha256"}, "file reference")
    return _relative(item["path"]), validate_sha256(item["sha256"], "task file digest")


class _Package:
    """Descriptor-relative, no-follow reads, including every root ancestor."""

    def __init__(self, path: Path):
        if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
                or os.open not in os.supports_dir_fd):
            raise ManifestError("task evidence: safe local reading unavailable")
        absolute = Path(os.path.abspath(path))
        self.name = _relative(absolute.name)
        self.directory = absolute.parent
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open(absolute.anchor, flags)
        try:
            for part in absolute.parent.parts[1:]:
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
        except BaseException:
            os.close(descriptor)
            raise
        self.root_fd = descriptor
        self.cache: dict[str, bytes] = {}
        self.total = 0

    def close(self) -> None:
        os.close(self.root_fd)

    def read(self, path: str) -> bytes:
        path = _relative(path)
        if path in self.cache:
            return self.cache[path]
        if len(self.cache) >= MAX_FILES:
            raise ManifestError("task evidence: file count limit")
        descriptor = os.dup(self.root_fd)
        try:
            for part in path.split("/")[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            leaf = os.open(path.split("/")[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
            try:
                before = os.fstat(leaf)
                if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
                    raise ManifestError("task evidence: unsafe or oversized file")
                with os.fdopen(leaf, "rb", closefd=False) as stream:
                    data = stream.read(MAX_FILE_BYTES + 1)
                after = os.fstat(leaf)
                if (len(data) > MAX_FILE_BYTES or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                        != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                    raise ManifestError("task evidence: file changed or exceeded bound")
            finally:
                os.close(leaf)
        finally:
            os.close(descriptor)
        self.total += len(data)
        if self.total > MAX_TOTAL_BYTES:
            raise ManifestError("task evidence: total byte limit")
        self.cache[path] = data
        return data

    def checked(self, reference: Any) -> tuple[bytes, str]:
        path, digest = _reference(reference)
        data = self.read(path)
        if sha256_bytes(data) != digest:
            raise ManifestError("task evidence: file digest mismatch")
        return data, "ref:" + digest


@dataclass
class _Ledger:
    tools: dict[str, list[str]] = field(default_factory=dict)
    handoffs: list[HandoffFact] = field(default_factory=list)
    guardrails: list[GuardrailFact] = field(default_factory=list)
    verification: list[VerificationFact] = field(default_factory=list)
    attempts: set[str] = field(default_factory=set)
    model_ids: set[str] = field(default_factory=set)
    skills: list[tuple[str, str, bool]] = field(default_factory=list)
    interventions: int = 0
    tokens: list[TokenUsageFact] = field(default_factory=list)
    costs: list[CostFact] = field(default_factory=list)
    tokens_complete: bool = True
    cost_complete: bool = True
    termination: OutcomeFact | None = None
    termination_reason: str = "none"


def _model_call(event: Mapping[str, Any], ledger: _Ledger) -> None:
    call_id = validate_identifier(event["call_id"], "model call id")
    if call_id in ledger.model_ids or event["accounting"] != "exclusive-call":
        raise ManifestError("task evidence: duplicate or nonexclusive model call")
    ledger.model_ids.add(call_id)
    for name in ("usage_source", "cost_source"):
        _choice(event[name], {"runtime-reported", "provider-reported", "estimated", "unavailable"}, name)
    usage = event["usage"]
    if usage is not None:
        item = _object(usage, {"input", "cached_input", "output"}, "token usage")
        tokens = TokenUsageFact(*(_integer(item[key], "token count") for key in ("input", "cached_input", "output")))
        if tokens.cached_input > tokens.input:
            raise ManifestError("task evidence: cached tokens exceed input")
        if event["usage_source"] in {"runtime-reported", "provider-reported"}:
            ledger.tokens.append(tokens)
        else:
            ledger.tokens_complete = False
    else:
        ledger.tokens_complete = False
    cost = event["cost"]
    if cost is not None:
        item = _object(cost, {"amount", "currency"}, "cost")
        amount, currency = item["amount"], item["currency"]
        if (type(amount) not in (int, float) or not 0 <= amount <= 2**53 - 1 or not math.isfinite(amount)
                or not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None):
            raise ManifestError("task evidence: invalid observed cost")
        if event["cost_source"] in {"runtime-reported", "provider-reported"}:
            ledger.costs.append(CostFact(amount, currency))
        else:
            ledger.cost_complete = False
    else:
        ledger.cost_complete = False


def _events(value: Any, package: _Package, run_id: str) -> _Ledger:
    data = _object(value, {"schema_version", "run_id", "coverage", "events"}, "event ledger")
    if data["schema_version"] != "adk-task-events/v1" or data["run_id"] != run_id:
        raise ManifestError("task evidence: event ledger identity mismatch")
    coverage = _object(data["coverage"], {
        "tools", "human_interventions", "skill_loads", "attempts", "handoffs", "guardrails", "model_calls",
    }, "event coverage")
    if any(value is not True for key, value in coverage.items() if key != "model_calls"):
        raise ManifestError("task evidence: incomplete event coverage")
    if type(coverage["model_calls"]) is not bool:
        raise ManifestError("task evidence: invalid model coverage")
    ledger = _Ledger(tokens_complete=coverage["model_calls"], cost_complete=coverage["model_calls"])
    ids: set[str] = set()
    guardrail_names: set[str] = set()
    fields = {
        "attempt": {"attempt_id"},
        "skill-load": {"skill", "content_sha256", "primary"},
        "tool-call": {"attempt_id", "tool", "outcome"},
        "model-call": {"attempt_id", "call_id", "accounting", "usage", "usage_source", "cost", "cost_source"},
        "human-intervention": {"category"},
        "handoff": {"target", "outcome"},
        "guardrail": {"name", "status", "evidence"},
        "termination": {"status", "category", "evidence"},
    }
    for sequence, raw in enumerate(_list(data["events"], MAX_EVENTS, "events"), 1):
        if not isinstance(raw, dict):
            raise ManifestError("task evidence: invalid event")
        kind = _choice(raw.get("kind"), set(fields), "event kind")
        event = _object(raw, fields[kind] | {"event_id", "seq", "kind"}, "event")
        ident = validate_identifier(event["event_id"], "event id")
        if ident in ids or _integer(event["seq"], "event sequence") != sequence:
            raise ManifestError("task evidence: duplicate or unordered event")
        ids.add(ident)
        if kind in {"attempt", "tool-call", "model-call"}:
            attempt_id = validate_identifier(event["attempt_id"], "attempt id")
            if (kind == "attempt") == (attempt_id in ledger.attempts):
                raise ManifestError("task evidence: duplicate or missing attempt")
            if kind == "attempt":
                ledger.attempts.add(attempt_id)
        if kind == "tool-call":
            name = validate_identifier(event["tool"], "tool name")
            ledger.tools.setdefault(name, []).append(_choice(event["outcome"], _TOOL_OUTCOMES, "tool outcome"))
        elif kind == "model-call":
            _model_call(event, ledger)
        elif kind == "skill-load":
            name = validate_identifier(event["skill"], "loaded skill")
            digest = validate_sha256(event["content_sha256"], "loaded skill digest")
            if type(event["primary"]) is not bool or any(skill == name for skill, _, _ in ledger.skills):
                raise ManifestError("task evidence: duplicate or invalid skill exposure")
            ledger.skills.append((name, digest, event["primary"]))
        elif kind == "human-intervention":
            _choice(event["category"], {"correction", "approval", "clarification"}, "intervention category")
            ledger.interventions += 1
        elif kind == "handoff":
            ledger.handoffs.append(HandoffFact(
                validate_identifier(event["target"], "handoff target"),
                _choice(event["outcome"], {"succeeded", "failed", "blocked", "cancelled"}, "handoff outcome"),
            ))
        elif kind == "guardrail":
            name = validate_identifier(event["name"], "process guardrail")
            if name in guardrail_names:
                raise ManifestError("task evidence: duplicate process guardrail")
            guardrail_names.add(name)
            status = _choice(event["status"], {"passed", "failed", "not-applicable"}, "guardrail status")
            _, reference = package.checked(event["evidence"])
            ledger.guardrails.append(GuardrailFact("process/" + name, status))
            ledger.verification.append(VerificationFact("process/" + name, status, reference))
        elif kind == "termination":
            status = _choice(event["status"], {"failed", "blocked", "cancelled"}, "termination status")
            categories = {"failed": {"timeout", "runtime-failure"},
                          "blocked": {"permission-blocked", "external-blocked"}, "cancelled": {"cancelled"}}
            category = _choice(event["category"], categories[status], "termination category")
            if ledger.termination is not None:
                raise ManifestError("task evidence: duplicate runtime termination")
            _, reference = package.checked(event["evidence"])
            ledger.termination = OutcomeFact(status, "runtime-failure" if category == "timeout" else category)
            ledger.termination_reason = "runtime-" + category
            ledger.verification.append(VerificationFact("runtime-termination", "failed" if status == "failed"
                                                        else "not-run", reference))
    if not ledger.attempts:
        raise ManifestError("task evidence: missing attempts")
    if not ledger.model_ids:
        # An empty ledger does not prove a model incurred exactly zero usage.
        ledger.tokens_complete = ledger.cost_complete = False
    if len({item.currency for item in ledger.costs}) > 1:
        raise ManifestError("task evidence: mixed cost currencies")
    if sum(primary for _, _, primary in ledger.skills) > 1:
        raise ManifestError("task evidence: ambiguous primary skill")
    return ledger


def _artifacts(value: Any, package: _Package) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in _list(value, 48, "artifacts"):
        path, digest = _reference(raw)
        if path in result:
            raise ManifestError("task evidence: duplicate artifact")
        package.checked(raw)
        result[path] = digest
    return result


def _acceptance(value: Any, package: _Package, run: Mapping[str, Any],
                artifacts: dict[str, str], ledger: _Ledger) -> tuple[str, str]:
    data = _object(value, {"schema_version", "run_id", "task_id", "executor_id", "grader_id", "status",
                          "artifacts", "checks", "guardrails", "trust", "evidence_scope", "raw_content_stored"},
                   "acceptance")
    if (data["schema_version"] != "adk-task-acceptance/v1" or data["trust"] != "caller-observed"
            or data["evidence_scope"] != "test-only" or data["raw_content_stored"] is not False):
        raise ManifestError("task evidence: unsupported acceptance trust")
    for key in ("run_id", "task_id", "executor_id"):
        if data[key] != run[key]:
            raise ManifestError("task evidence: acceptance identity mismatch")
    grader = validate_identifier(data["grader_id"], "grader id")
    if grader == run["executor_id"]:
        raise ManifestError("task evidence: grader must differ from executor")
    status = _choice(data["status"], {"passed", "failed", "blocked", "not-run"}, "acceptance status")
    if _artifacts(data["artifacts"], package) != artifacts:
        raise ManifestError("task evidence: acceptance artifact mismatch")
    checks = _list(data["checks"], 48, "acceptance checks")
    check_statuses: list[str] = []
    for category in ("checks", "guardrails"):
        names: set[str] = set()
        for raw in _list(data[category], 48, "acceptance results"):
            item = _object(raw, {"name", "status", "evidence"}, "acceptance result")
            name = validate_identifier(item["name"], "acceptance result name")
            if name in names:
                raise ManifestError("task evidence: duplicate acceptance result")
            names.add(name)
            choices = {"passed", "failed", "not-run"} if category == "checks" else {"passed", "failed", "not-applicable"}
            result = _choice(item["status"], choices, "acceptance result status")
            _, reference = package.checked(item["evidence"])
            prefix = "acceptance/" if category == "checks" else "artifact/"
            ledger.verification.append(VerificationFact(prefix + name, result, reference))
            if category == "guardrails":
                ledger.guardrails.append(GuardrailFact("artifact/" + name, result))
            else:
                check_statuses.append(result)
    if status == "passed" and (not artifacts or not checks or any(item != "passed" for item in check_statuses)
                               or any(item.status == "failed" and item.name.startswith("artifact/")
                                      for item in ledger.guardrails)):
        raise ManifestError("task evidence: success lacks passing independent artifact acceptance")
    if (status == "failed" and "failed" not in check_statuses
            and not any(item.status == "failed" and item.name.startswith("artifact/") for item in ledger.guardrails)):
        raise ManifestError("task evidence: failed acceptance needs failed check")
    return status, grader


def _import(package: _Package, manifest: Manifest) -> dict[str, Any]:
    raw = package.read(package.name)
    data = _object(loads(raw), {"schema_version", "provenance", "run", "input_snapshot", "workspace_snapshot",
                               "events", "acceptance", "artifacts", "skill_exposure"}, "observation")
    if data["schema_version"] != "adk-task-observation/v1":
        raise ManifestError("task evidence: unsupported observation schema")
    provenance = _choice(data["provenance"], {"recorded-task", "synthetic-fixture"}, "provenance")
    run = _object(data["run"], {"run_id", "task_id", "executor_id", "source_sha", "asset_bundle_sha256",
                              "runtime_target", "runtime_version", "model_version", "prompt_version",
                              "orchestration_mode", "started_at", "finished_at", "privacy_status"}, "run")
    for key in ("run_id", "task_id", "executor_id", "runtime_target", "runtime_version", "model_version", "prompt_version"):
        validate_identifier(run[key], "run identity")
    if not isinstance(run["source_sha"], str) or re.fullmatch(r"[0-9a-f]{40}", run["source_sha"]) is None:
        raise ManifestError("task evidence: invalid source SHA")
    validate_sha256(run["asset_bundle_sha256"], "asset bundle digest")
    started, finished = _timestamp(run["started_at"]), _timestamp(run["finished_at"])
    if finished < started:
        raise ManifestError("task evidence: finish precedes start")
    input_bytes, input_ref = package.checked(data["input_snapshot"])
    _, workspace_ref = package.checked(data["workspace_snapshot"])
    event_bytes, events_ref = package.checked(data["events"])
    acceptance_bytes, acceptance_ref = package.checked(data["acceptance"])
    ledger = _events(loads(event_bytes), package, run["run_id"])
    artifacts = _artifacts(data["artifacts"], package)
    acceptance_status, grader = _acceptance(loads(acceptance_bytes), package, run, artifacts, ledger)
    exposure = _object(data["skill_exposure"], {"target_skill", "expected", "content"}, "skill exposure")
    target = validate_identifier(exposure["target_skill"], "target skill")
    expected = _choice(exposure["expected"], {"loaded", "absent"}, "expected skill exposure")
    _, skill_ref = package.checked(exposure["content"])
    loaded = [(name, digest, primary) for name, digest, primary in ledger.skills if name == target]
    if loaded and (loaded[0][1] != skill_ref[4:] or expected == "absent"):
        raise ManifestError("task evidence: loaded skill differs from declared intervention")
    primary_skill = next((name for name, _, primary in ledger.skills if primary), "no-skill")
    wrong_skill = primary_skill != target if expected == "loaded" else primary_skill != "no-skill"
    process_failed = any(item.status == "failed" and item.name.startswith("process/") for item in ledger.guardrails)
    artifact_failed = any(item.status == "failed" and item.name.startswith("artifact/") for item in ledger.guardrails)
    if process_failed or artifact_failed or acceptance_status == "failed":
        outcome: OutcomeFact | MetricUnavailable = OutcomeFact("failed", "validation-failure")
        failure_pattern = "process-guardrail-failed" if process_failed else "artifact-acceptance-failed"
    elif ledger.termination is not None:
        outcome = ledger.termination
        failure_pattern = ledger.termination_reason
    elif acceptance_status == "passed":
        outcome = OutcomeFact("succeeded", "completed")
        failure_pattern = "none"
    elif acceptance_status == "blocked":
        outcome = OutcomeFact("blocked", "external-blocked")
        failure_pattern = "artifact-acceptance-blocked"
    else:
        outcome = MetricUnavailable("artifact-acceptance-not-observed")
        failure_pattern = "artifact-acceptance-unavailable"
    success = isinstance(outcome, OutcomeFact) and outcome.status == "succeeded"
    token_usage: TokenUsageFact | MetricUnavailable = MetricUnavailable("complete-runtime-token-usage-unavailable")
    if ledger.tokens_complete:
        token_usage = TokenUsageFact(*(sum(getattr(item, key) for item in ledger.tokens)
                                      for key in ("input", "cached_input", "output")))
    cost: CostFact | MetricUnavailable = MetricUnavailable("complete-runtime-cost-unavailable")
    if ledger.cost_complete:
        cost = CostFact(sum(item.amount for item in ledger.costs), ledger.costs[0].currency)
    evidence = [VerificationFact(name, "passed", reference) for name, reference in (
        ("observation-binding", "ref:" + sha256_bytes(raw)), ("input-snapshot", input_ref),
        ("workspace-snapshot", workspace_ref), ("event-ledger", events_ref),
        ("acceptance-binding", acceptance_ref), ("skill-content-binding", skill_ref),
    )]
    evidence.extend(VerificationFact(f"artifact-{index}", "passed", "ref:" + digest)
                    for index, digest in enumerate(artifacts.values()))
    facts = TraceRunFacts(
        run_id=run["run_id"], task_id=run["task_id"], asset_bundle_sha256=run["asset_bundle_sha256"],
        runtime_target=run["runtime_target"], runtime_version=run["runtime_version"], model_version=run["model_version"],
        goal_ref="ref:" + sha256_bytes(input_bytes), primary_skill=primary_skill, prompt_version=run["prompt_version"],
        orchestration_mode=run["orchestration_mode"],
        tools_used=tuple(ToolUseFact(name, len(results), results[0] if len(set(results)) == 1 else "partial")
                         for name, results in sorted(ledger.tools.items())), handoffs=tuple(ledger.handoffs),
        guardrails=tuple(ledger.guardrails), verification=tuple(evidence + ledger.verification),
        elapsed_ms=(finished - started) // timedelta(milliseconds=1),
        first_pass_success=success and len(ledger.attempts) == 1 and ledger.interventions == 0 and not wrong_skill,
        human_interventions=ledger.interventions, wrong_skill=wrong_skill, abstained=False,
        privacy_status=run["privacy_status"], blockers=("task-blocked",)
        if isinstance(outcome, OutcomeFact) and outcome.status == "blocked" else (),
        failure_pattern=failure_pattern, next_goal_ref=None, token_usage=token_usage, cost=cost, outcome=outcome,
    )
    contract = load_contract(manifest.root / "manifests/agent_value_contracts.json")
    result = emit_run_evidence(RunEvidenceObservation(facts, finished), manifest, contract)
    return {
        "schema_version": "adk-task-evidence-import/v1", "status": "imported", "provenance": provenance,
        "acceptance_status": acceptance_status,
        "trust": "caller-observed", "evidence_scope": "test-only", "quality_evidence_eligible": False,
        "pairing_authority": "none-single-observation",
        "lifecycle_authority": "none-evidence-only", "release_authorized": False, "raw_content_stored": False,
        "bindings": {"observation_ref": "ref:" + sha256_bytes(raw), "input_snapshot_ref": input_ref,
                     "workspace_snapshot_ref": workspace_ref, "events_ref": events_ref,
                     "acceptance_ref": acceptance_ref, "skill_content_ref": skill_ref,
                     "source_sha": run["source_sha"], "executor_id": run["executor_id"], "grader_id": grader},
        "assigned_exposure": {"target_skill": target, "expected": expected, "content_sha256": skill_ref[4:]},
        "run_evidence": result,
    }


@dataclass(frozen=True)
class ImportedTaskEvidence:
    """Report plus read-set, retained for safe campaign/report publication."""

    report: dict[str, Any]
    inputs: tuple[Path, ...]
    bytes_read: int


def read_task_evidence(input_path: Path, manifest: Manifest) -> ImportedTaskEvidence:
    """Read a local package without scanning, writing, executing or networking."""
    package = _Package(input_path)
    try:
        report = _import(package, manifest)
        return ImportedTaskEvidence(report, tuple(package.directory / name for name in package.cache), package.total)
    finally:
        package.close()


def publish_task_report(report: dict[str, Any], output_path: Path, inputs: tuple[Path, ...]) -> None:
    """Use existing atomic publication after checking every input/output alias.

    Output directories remain caller-owned, as in the existing atomic I/O
    contract; this does not claim isolation from concurrent hostile writers.
    """
    validate_document_outputs([output_path], inputs)
    write_texts_atomic([(output_path, encode_json_document(report, "task evidence report"))])


def import_task_evidence(input_path: Path, manifest: Manifest, *, output_path: Path | None = None) -> dict[str, Any]:
    """Import one local package, optionally publishing a separate safe report.

    All required process-counter coverage must be explicit. Partial model
    accounting becomes unavailable, including estimates and omitted calls.
    The returned report retains provenance; its run_evidence member is the
    unchanged composition accepted by compare-trials. No asset receipts or
    production qualification are issued.
    """
    imported = read_task_evidence(input_path, manifest)
    if output_path is not None:
        publish_task_report(imported.report, output_path, imported.inputs + (
            manifest.root / "manifest.json", manifest.root / "manifests/agent_value_contracts.json",
        ))
    return imported.report
