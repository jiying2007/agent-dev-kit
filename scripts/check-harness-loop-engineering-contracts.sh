#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-harness-loop-engineering-contracts.sh [--summary-json]

Checks ADK harness/loop engineering contracts:
  - external source refs remain method-only and runtime-disabled
  - harness, loop and observability contracts contain required fields
  - quality gates prevent unreviewed runtime adoption
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

rtk python3 - "$ROOT_DIR" "$SUMMARY_JSON" <<'PY'
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
summary_json = sys.argv[2] == "1"
manifest_path = root / "manifests/harness_loop_engineering_contracts.json"
failures = []
checked = 0


def fail(message):
    failures.append(message)


def check(condition, message):
    global checked
    checked += 1
    if not condition:
        fail(message)


def require_keys(obj, keys, label):
    for key in keys:
        check(key in obj and obj[key] not in ("", None, []), f"{label} missing key: {key}")


if not manifest_path.is_file():
    fail("missing manifest: manifests/harness_loop_engineering_contracts.json")
    manifest = {}
else:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json: {exc}")
        manifest = {}

check(manifest.get("status") == "report-only", "status must be report-only")
check(manifest.get("default_mode") == "method-only", "default_mode must be method-only")
check("does not clone" in manifest.get("reference_boundary", ""), "reference_boundary must reject runtime adoption")

required_sources = {
    "google-adk-python",
    "langgraph",
    "swe-bench",
    "inspect-ai",
    "promptfoo",
    "openai-agents-python",
    "openhands",
    "swe-agent",
    "smolagents",
    "deepeval",
    "phoenix",
    "lm-evaluation-harness",
}
sources = manifest.get("source_refs", [])
source_ids = {source.get("id") for source in sources if isinstance(source, dict)}
for source_id in sorted(required_sources):
    check(source_id in source_ids, f"missing source_ref: {source_id}")

for source in sources:
    if not isinstance(source, dict):
        fail("source_ref item must be an object")
        continue
    sid = source.get("id", "<missing-id>")
    require_keys(source, ["id", "title", "repo", "url", "retrieved_at", "priority", "track_mode", "decision", "runtime_enabled", "absorb_target"], f"source_ref {sid}")
    parsed = urlparse(source.get("url", ""))
    check(parsed.scheme in {"https", "http"} and bool(parsed.netloc), f"source_ref {sid} has invalid url")
    check(source.get("runtime_enabled") is False, f"source_ref {sid} must keep runtime_enabled=false")
    check(source.get("decision") in {"adopt-method-only", "observe-method-only"}, f"source_ref {sid} decision must remain method-only")
    check(source.get("track_mode") in {"adopt-contract", "observe-method-only", "historical-reference-only"}, f"source_ref {sid} has invalid track_mode")

def collect_contracts(section):
    values = manifest.get(section, [])
    check(isinstance(values, list), f"{section} must be an array")
    return values if isinstance(values, list) else []

contracts = (
    collect_contracts("harness_contracts")
    + collect_contracts("loop_contracts")
    + collect_contracts("observability_contracts")
)
contract_by_id = {contract.get("id"): contract for contract in contracts if isinstance(contract, dict)}
gate = manifest.get("quality_gate", {})

required_contracts = {
    "repo-task-evaluation-harness-v1",
    "agent-eval-ci-gate-v1",
    "model-eval-harness-v1",
    "durable-agent-loop-v1",
    "coding-agent-loop-v1",
    "workflow-state-contract-v1",
    "sandbox-boundary-contract-v1",
    "trace-observability-contract-v1",
    "guardrail-handoff-contract-v1",
}
for contract_id in sorted(required_contracts):
    check(contract_id in contract_by_id, f"missing contract: {contract_id}")

p0_sources = {
    source.get("id")
    for source in sources
    if isinstance(source, dict) and source.get("priority") == "P0"
}
for contract in contracts:
    if not isinstance(contract, dict):
        fail("contract item must be an object")
        continue
    cid = contract.get("id", "<missing-id>")
    require_keys(contract, ["id", "owner", "source_refs", "required_fields", "quality_gates", "must_not"], f"contract {cid}")
    for source_ref in contract.get("source_refs", []):
        check(source_ref in source_ids, f"contract {cid} references unknown source_ref: {source_ref}")
    if gate.get("each_contract_requires_at_least_one_p0_source") is True:
        check(bool(set(contract.get("source_refs", [])) & p0_sources), f"contract {cid} must include at least one P0 source")

required_fields = {
    "repo-task-evaluation-harness-v1": [
        "task_id",
        "source_repo",
        "pinned_revision",
        "environment_spec",
        "runner_command",
        "scorer",
        "expected_artifacts",
        "resource_budget",
        "reproducibility_evidence",
        "failure_replay",
    ],
    "agent-eval-ci-gate-v1": [
        "eval_suite_id",
        "positive_cases",
        "negative_cases",
        "judge_policy",
        "non_llm_assertions",
        "ci_mode",
        "threshold",
        "flaky_policy",
        "red_team_scope",
    ],
    "durable-agent-loop-v1": [
        "state_schema",
        "transition_edges",
        "checkpoint_policy",
        "resume_policy",
        "retry_budget",
        "stop_condition",
        "human_gate",
        "failure_replay",
    ],
    "coding-agent-loop-v1": [
        "workspace_boundary",
        "sandbox_policy",
        "action_format",
        "observation_capture",
        "patch_artifact",
        "test_command",
        "rollback_path",
        "approval_boundary",
    ],
    "trace-observability-contract-v1": [
        "trace_id",
        "span_kind",
        "agent_id",
        "tool_calls",
        "handoff",
        "guardrail_result",
        "session_id",
        "redaction_policy",
        "evidence_path",
    ],
}
for contract_id, fields in required_fields.items():
    contract = contract_by_id.get(contract_id, {})
    present = set(contract.get("required_fields", []))
    for field in fields:
        check(field in present, f"contract {contract_id} missing field: {field}")

for key in (
    "method_only_default",
    "runtime_enabled_default_must_be_false",
    "external_code_requires_supply_chain_review",
    "container_or_code_execution_requires_owner_approval",
    "source_mapping_requires_report",
    "source_mapping_requires_adoption_matrix_evidence",
    "each_contract_requires_at_least_one_p0_source",
    "eval_cases_require_positive_and_negative_examples",
    "durable_loop_requires_checkpoint_and_stop_condition",
    "trace_storage_requires_redaction_policy",
    "failure_replay_required_for_harness_and_loop_claims",
):
    check(gate.get(key) is True, f"quality_gate {key} must be true")

rejected = set(manifest.get("rejected_runtime_surfaces", []))
for surface in (
    "external_cli_install",
    "benchmark_container_execution_by_default",
    "daemon_or_background_worker",
    "hook_registration",
    "mcp_server_enablement",
    "unreviewed_code_execution_sandbox",
):
    check(surface in rejected, f"missing rejected runtime surface: {surface}")

status = "pass" if not failures else "fail"
if summary_json:
    print(json.dumps({"status": status, "checked": checked, "failures": len(failures)}, ensure_ascii=True))
else:
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}", file=sys.stderr)
    else:
        print("[PASS] harness/loop engineering contracts")

if failures:
    sys.exit(1)
PY
