#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from agent_dev_kit.evidence.envelope import bind_evidence_envelope, validate_evidence_envelope

base = {
    "schema": "adk-evidence-envelope/v1",
    "artifact_id": "run:fixture:1",
    "producer": {"component": "test", "version": "1"},
    "source": {"commit": "1" * 40, "tree": "2" * 40, "policy_sha256": None},
    "evidence_class": "test",
    "run": {"run_id": "fixture-1", "environment": "ci", "toolchain": "python"},
    "subjects": ["asset:fixture"],
    "claims": [{"id": "claim-1", "statement": "fixture contract passed", "status": "supported"}],
    "inputs": ["sha256:" + "3" * 64],
    "outputs": ["receipt:fixture"],
    "verdict": "pass",
    "freshness": {"generated_at": "2026-09-11T00:00:00Z", "expires_at": None},
    "privacy": {
        "raw_content_stored": False,
        "sensitivity": "internal",
        "forbidden_payloads": ["prompt", "messages", "raw-log", "tool-payload"]
    },
    "provenance": {"refs": ["test-contract"], "content_sha256": None}
}

bound = bind_evidence_envelope(base)
assert validate_evidence_envelope(bound)["status"] == "pass", bound
assert len(bound["provenance"]["content_sha256"]) == 64

tampered = dict(bound)
tampered["verdict"] = "fail"
result = validate_evidence_envelope(tampered)
assert result["status"] == "fail", result
assert any("content_sha256" in failure for failure in result["failures"]), result

leaky = dict(base)
leaky["claims"] = [{"id": "claim-1", "statement": "bad", "status": "supported", "prompt": "secret"}]
result = validate_evidence_envelope(leaky)
assert result["status"] == "fail", result
assert any("forbidden raw payload key" in failure for failure in result["failures"]), result

bad_time = dict(base)
bad_time["freshness"] = {"generated_at": "not-a-timestamp", "expires_at": None}
result = validate_evidence_envelope(bad_time)
assert result["status"] == "fail", result
assert any("freshness/generated_at" in failure and "date-time" in failure for failure in result["failures"]), result
PY

echo '[PASS] evidence envelope is content-addressed, privacy-safe, RFC3339-valid and tamper-evident'
