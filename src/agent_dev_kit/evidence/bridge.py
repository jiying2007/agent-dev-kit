"""Reference-only adapters from existing ADK evidence artifacts to Evidence Envelope v1.

The bridge never embeds the source artifact. It validates the artifact privacy
boundary, binds a canonical content digest, and emits only identities/opaque
references plus normalized claims. Existing artifact schemas remain unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from agent_dev_kit.model import canonical_json_bytes, sha256_bytes
from agent_dev_kit.privacy_ref import validate_no_secrets

from .envelope import bind_evidence_envelope

EvidenceClass = Literal["source", "test", "runtime", "field", "release"]
Sensitivity = Literal["public", "internal", "restricted"]
EnvelopeVerdict = Literal["pass", "fail", "blocked", "unavailable", "not-measured"]
ClaimStatus = Literal["supported", "rejected", "blocked", "unavailable", "not-measured"]

_TRACE_SCHEMA = "adk-workflow-trace-summary/v2"
_RUN_SCHEMA = "adk-run-evidence-composition/v1"
_RECEIPT_SCHEMA = "adk-asset-invocation-receipt/v1"


@dataclass(frozen=True, slots=True)
class EvidenceBridgeContext:
    """Explicit source/provenance context unavailable inside legacy artifacts."""

    commit: str
    tree: str
    producer_version: str
    generated_at: datetime
    evidence_class: EvidenceClass
    policy_sha256: str | None = None
    expires_at: datetime | None = None
    sensitivity: Sensitivity = "internal"
    provenance_refs: tuple[str, ...] = ()


def _iso(value: datetime, label: str) -> str:
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _artifact_digest(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(dict(value)))


def _artifact_ref(value: Mapping[str, Any]) -> str:
    return f"sha256:{_artifact_digest(value)}"


def _strings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({item for item in values if isinstance(item, str) and item})


def _refs(*values: str | None) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value})


def _outcome_verdict(status: object) -> EnvelopeVerdict:
    if status == "succeeded":
        return "pass"
    if status in {"failed", "cancelled"}:
        return "fail"
    if status == "blocked":
        return "blocked"
    if status == "not-available":
        return "unavailable"
    return "not-measured"


def _source(context: EvidenceBridgeContext) -> dict[str, str | None]:
    return {
        "commit": context.commit,
        "tree": context.tree,
        "policy_sha256": context.policy_sha256,
    }


def _freshness(context: EvidenceBridgeContext) -> dict[str, str | None]:
    return {
        "generated_at": _iso(context.generated_at, "generated_at"),
        "expires_at": _iso(context.expires_at, "expires_at") if context.expires_at is not None else None,
    }


def _privacy(context: EvidenceBridgeContext) -> dict[str, object]:
    return {
        "raw_content_stored": False,
        "sensitivity": context.sensitivity,
        "forbidden_payloads": ["prompt", "messages", "raw-log", "tool-payload"],
    }


def _claim(claim_id: str, statement: str, status: ClaimStatus) -> dict[str, str]:
    return {"id": claim_id, "statement": statement, "status": status}


def _envelope(
    *,
    kind: str,
    artifact: Mapping[str, Any],
    context: EvidenceBridgeContext,
    subjects: list[str],
    inputs: list[str],
    claims: list[dict[str, str]],
    verdict: EnvelopeVerdict,
) -> dict[str, Any]:
    validate_no_secrets(artifact, f"{kind} evidence bridge input")
    if artifact.get("raw_content_stored") is not False:
        raise ValueError(f"{kind} must explicitly declare raw_content_stored=false")
    artifact_ref = _artifact_ref(artifact)
    digest = artifact_ref.split(":", 1)[1]
    payload: dict[str, Any] = {
        "schema": "adk-evidence-envelope/v1",
        "artifact_id": f"{kind}:{digest[:32]}",
        "producer": {
            "component": "agent_dev_kit.evidence.bridge",
            "version": context.producer_version,
        },
        "source": _source(context),
        "evidence_class": context.evidence_class,
        "subjects": sorted(set(subjects)),
        "claims": claims,
        "inputs": sorted(set(inputs)),
        "outputs": [artifact_ref],
        "verdict": verdict,
        "freshness": _freshness(context),
        "privacy": _privacy(context),
        "provenance": {
            "refs": sorted({artifact_ref, *context.provenance_refs}),
            "content_sha256": None,
        },
    }
    return bind_evidence_envelope(payload)


def envelope_trace_summary(
    summary: Mapping[str, Any],
    context: EvidenceBridgeContext,
) -> dict[str, Any]:
    """Wrap a privacy-bounded workflow trace summary without copying its payload."""

    if summary.get("schema_version") != _TRACE_SCHEMA:
        raise ValueError("unsupported trace summary schema")
    outcome = summary.get("outcome")
    status = outcome.get("status") if isinstance(outcome, Mapping) else None
    verification = summary.get("verification")
    evidence_refs: list[str] = []
    if isinstance(verification, list):
        for item in verification:
            if isinstance(item, Mapping):
                ref = item.get("evidence_ref")
                if isinstance(ref, str) and ref:
                    evidence_refs.append(ref)
    subjects = _refs(
        str(summary.get("run_id")) if summary.get("run_id") else None,
        str(summary.get("task_id")) if summary.get("task_id") else None,
        str(summary.get("runtime_target")) if summary.get("runtime_target") else None,
    )
    return _envelope(
        kind="trace-summary",
        artifact=summary,
        context=context,
        subjects=subjects,
        inputs=sorted(set(evidence_refs)),
        claims=[
            _claim(
                "trace-outcome-recorded",
                f"workflow trace records outcome {status or 'not-available'}",
                "supported" if status is not None else "not-measured",
            )
        ],
        verdict=_outcome_verdict(status),
    )


def envelope_run_evidence(
    composition: Mapping[str, Any],
    context: EvidenceBridgeContext,
) -> dict[str, Any]:
    """Wrap run-evidence composition while preserving its test-only authority."""

    if composition.get("schema_version") != _RUN_SCHEMA:
        raise ValueError("unsupported run evidence schema")
    if context.evidence_class != "test":
        raise ValueError("run evidence composition is test-only and must use evidence_class=test")
    trace_summary = composition.get("trace_summary")
    if not isinstance(trace_summary, Mapping):
        raise ValueError("run evidence composition is missing trace_summary")
    outcome = trace_summary.get("outcome")
    status = outcome.get("status") if isinstance(outcome, Mapping) else None
    receipts = composition.get("receipts")
    receipt_refs: list[str] = []
    if isinstance(receipts, list):
        for receipt in receipts:
            if isinstance(receipt, Mapping):
                receipt_id = receipt.get("receipt_id")
                if isinstance(receipt_id, str) and receipt_id:
                    receipt_refs.append(receipt_id)
    trace_ref = composition.get("trace_ref")
    trace_ref_text = trace_ref if isinstance(trace_ref, str) else None
    inputs = sorted(set([*receipt_refs, *_refs(trace_ref_text)]))
    measured = composition.get("measurement") is not None
    return _envelope(
        kind="run-evidence",
        artifact=composition,
        context=context,
        subjects=_refs(trace_ref_text),
        inputs=inputs,
        claims=[
            _claim(
                "test-evidence-composed",
                "test-layer trace and asset evidence are linked without runtime or field authority",
                "supported",
            ),
            _claim(
                "asset-measurement-present",
                "asset value measurement is present in the test composition",
                "supported" if measured else "not-measured",
            ),
        ],
        verdict=_outcome_verdict(status),
    )


def envelope_agent_value_receipt(
    receipt: Mapping[str, Any],
    context: EvidenceBridgeContext,
) -> dict[str, Any]:
    """Wrap one existing Agent Value invocation receipt by reference."""

    if receipt.get("schema_version") != _RECEIPT_SCHEMA:
        raise ValueError("unsupported agent value receipt schema")
    layer = receipt.get("evidence_layer")
    if layer not in {"test", "runtime", "field"}:
        raise ValueError("agent value receipt has invalid evidence_layer")
    if context.evidence_class != layer:
        raise ValueError("evidence envelope class must match receipt evidence_layer")
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id:
        raise ValueError("agent value receipt is missing receipt_id")
    source_trace_ref = receipt.get("source_trace_ref")
    manifest_ref = receipt.get("manifest_ref")
    inputs = [
        *_strings(receipt.get("evidence_refs")),
        *_refs(
            source_trace_ref if isinstance(source_trace_ref, str) else None,
            manifest_ref if isinstance(manifest_ref, str) else None,
        ),
    ]
    outcome = receipt.get("outcome")
    return _envelope(
        kind="agent-value-receipt",
        artifact=receipt,
        context=context,
        subjects=_refs(
            receipt_id,
            str(receipt.get("asset_id")) if receipt.get("asset_id") else None,
            str(receipt.get("runtime_target")) if receipt.get("runtime_target") else None,
        ),
        inputs=sorted(set(inputs)),
        claims=[
            _claim(
                "asset-invocation-measured",
                f"asset invocation receipt records {layer} evidence",
                "supported",
            )
        ],
        verdict=_outcome_verdict(outcome),
    )
