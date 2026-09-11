#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from __future__ import annotations

from datetime import datetime, timezone

from agent_dev_kit.evidence import (
    EvidenceBridgeContext,
    envelope_agent_value_receipt,
    envelope_run_evidence,
    envelope_trace_summary,
    validate_evidence_envelope,
)
from agent_dev_kit.model import canonical_json_bytes, sha256_bytes

REF_A = "ref:" + "a" * 64
REF_B = "ref:" + "b" * 64
REF_C = "ref:" + "c" * 64
REF_D = "ref:" + "d" * 64

runtime_context = EvidenceBridgeContext(
    commit="1" * 40,
    tree="2" * 40,
    producer_version="5.0.0-rc.2",
    generated_at=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
    evidence_class="runtime",
    provenance_refs=(REF_D,),
)
test_context = EvidenceBridgeContext(
    commit="1" * 40,
    tree="2" * 40,
    producer_version="5.0.0-rc.2",
    generated_at=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
    evidence_class="test",
)

trace = {
    "schema_version": "adk-workflow-trace-summary/v2",
    "run_id": "run-001",
    "task_id": "task-001",
    "runtime_target": "runtime-a",
    "outcome": {"status": "succeeded", "category": "completed"},
    "verification": [{"name": "test", "status": "passed", "evidence_ref": REF_A}],
    "raw_content_stored": False,
}
trace_envelope = envelope_trace_summary(trace, runtime_context)
assert validate_evidence_envelope(trace_envelope)["status"] == "pass"
assert trace_envelope["verdict"] == "pass"
assert trace_envelope["evidence_class"] == "runtime"
assert trace_envelope["inputs"] == [REF_A]
assert trace_envelope["outputs"] == ["sha256:" + sha256_bytes(canonical_json_bytes(trace))]
assert "trace_summary" not in trace_envelope
assert REF_D in trace_envelope["provenance"]["refs"]

composition = {
    "schema_version": "adk-run-evidence-composition/v1",
    "trace_ref": REF_B,
    "trace_summary": trace,
    "receipts": [{"receipt_id": REF_C}],
    "measurement": {"schema_version": "adk-asset-value-measurement/v1"},
    "raw_content_stored": False,
}
run_envelope = envelope_run_evidence(composition, test_context)
assert validate_evidence_envelope(run_envelope)["status"] == "pass"
assert run_envelope["evidence_class"] == "test"
assert run_envelope["inputs"] == sorted([REF_B, REF_C])
assert run_envelope["claims"][1]["status"] == "supported"
assert "trace_summary" not in run_envelope
assert "receipts" not in run_envelope

receipt = {
    "schema_version": "adk-asset-invocation-receipt/v1",
    "receipt_id": REF_C,
    "evidence_layer": "runtime",
    "source_trace_ref": REF_B,
    "manifest_ref": REF_A,
    "evidence_refs": [REF_D],
    "asset_id": "skill-a",
    "runtime_target": "runtime-a",
    "outcome": "succeeded",
    "raw_content_stored": False,
}
receipt_envelope = envelope_agent_value_receipt(receipt, runtime_context)
assert validate_evidence_envelope(receipt_envelope)["status"] == "pass"
assert receipt_envelope["evidence_class"] == "runtime"
assert receipt_envelope["inputs"] == sorted([REF_A, REF_B, REF_D])
assert receipt_envelope["subjects"] == sorted([REF_C, "runtime-a", "skill-a"])
assert "evidence_refs" not in receipt_envelope

try:
    envelope_run_evidence(composition, runtime_context)
except ValueError as exc:
    assert "test-only" in str(exc)
else:
    raise AssertionError("run evidence bridge must reject runtime authority")

try:
    envelope_agent_value_receipt(receipt, test_context)
except ValueError as exc:
    assert "must match" in str(exc)
else:
    raise AssertionError("receipt bridge must reject evidence-layer mismatch")

unsafe_trace = dict(trace)
unsafe_trace["raw_prompt"] = "sensitive content"
try:
    envelope_trace_summary(unsafe_trace, runtime_context)
except ValueError as exc:
    assert "forbidden sensitive field" in str(exc)
else:
    raise AssertionError("bridge must reject raw sensitive payloads")

not_bounded = dict(trace)
not_bounded["raw_content_stored"] = True
try:
    envelope_trace_summary(not_bounded, runtime_context)
except ValueError as exc:
    assert "raw_content_stored=false" in str(exc)
else:
    raise AssertionError("bridge must require an explicit privacy boundary")

print("[PASS] evidence bridge is reference-only, authority-bounded and fail-closed")
PY
