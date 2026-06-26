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
    "temporal",
    "pydantic-ai",
    "langfuse",
    "aider",
    "mastra",
    "semantic-kernel",
    "haystack",
    "ragas",
    "crewai",
    "continue",
    "inspect-evals",
    "terminal-bench",
    "mini-swe-agent",
    "swe-rex",
    "dagger",
    "argo-workflows",
    "tau-bench",
    "agentbench",
    "webarena",
    "osworld",
    "openai-evals",
    "simple-evals",
    "prefect",
    "dagster",
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
    "sandbox-terminal-harness-v1",
    "durable-execution-contract-v1",
    "durable-agent-loop-v1",
    "typed-hitl-graph-contract-v1",
    "coding-repair-loop-v1",
    "coding-agent-loop-v1",
    "workflow-state-contract-v1",
    "reproducible-execution-pipeline-v1",
    "sandbox-boundary-contract-v1",
    "trace-observability-contract-v1",
    "trace-eval-evidence-bundle-v1",
    "artifact-lineage-evidence-contract-v1",
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
    "sandbox-terminal-harness-v1": [
        "task_instruction",
        "sandbox_backend",
        "setup_command",
        "agent_command",
        "test_script",
        "oracle_solution",
        "timeout_policy",
        "resource_budget",
        "stdout_stderr_capture",
        "exit_code_policy",
        "cleanup_policy",
        "dataset_version",
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
    "durable-execution-contract-v1": [
        "workflow_id",
        "state_history",
        "deterministic_replay_policy",
        "activity_boundary",
        "retry_policy",
        "timeout_policy",
        "cancellation_policy",
        "idempotency_key",
        "failure_replay",
        "recovery_owner",
    ],
    "typed-hitl-graph-contract-v1": [
        "graph_node_id",
        "typed_input_schema",
        "typed_output_schema",
        "dependency_context",
        "tool_approval_request",
        "human_decision_record",
        "resume_point",
        "state_storage_policy",
        "validation_error_policy",
    ],
    "coding-repair-loop-v1": [
        "repo_map_evidence",
        "edit_scope",
        "patch_artifact",
        "lint_command",
        "test_command",
        "failure_observation",
        "repair_attempt_budget",
        "git_diff_review",
        "rollback_path",
        "completion_evidence",
    ],
    "reproducible-execution-pipeline-v1": [
        "pipeline_id",
        "local_ci_parity",
        "container_or_runtime_spec",
        "dag_or_step_graph",
        "artifact_inputs",
        "artifact_outputs",
        "cache_policy",
        "trace_export_policy",
        "schedule_policy",
        "retry_policy",
        "archive_policy",
        "rollback_path",
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
    "trace-eval-evidence-bundle-v1": [
        "trace_id",
        "dataset_id",
        "prompt_version",
        "eval_run_id",
        "score_schema",
        "metric_threshold",
        "production_feedback_source",
        "redaction_policy",
        "evidence_bundle_path",
        "regression_link",
    ],
    "artifact-lineage-evidence-contract-v1": [
        "artifact_id",
        "source_input",
        "producer_step",
        "consumer_step",
        "version_or_digest",
        "materialization_time",
        "metadata_schema",
        "quality_check",
        "retention_policy",
        "supersedes",
        "evidence_path",
    ],
}
for contract_id, fields in required_fields.items():
    contract = contract_by_id.get(contract_id, {})
    present = set(contract.get("required_fields", []))
    for field in fields:
        check(field in present, f"contract {contract_id} missing field: {field}")

fixtures = manifest.get("fixtures", [])
check(isinstance(fixtures, list) and fixtures, "fixtures must include at least one local method-only example")
fixture_by_id = {fixture.get("id"): fixture for fixture in fixtures if isinstance(fixture, dict)}
fixture = fixture_by_id.get("harness-loop-local-fixture-bundle-v1", {})
require_keys(
    fixture,
    ["id", "path", "mode", "runtime_enabled", "covers", "notes"],
    "fixture harness-loop-local-fixture-bundle-v1",
)
check(fixture.get("mode") == "method-only", "harness-loop fixture must be method-only")
check(fixture.get("runtime_enabled") is False, "harness-loop fixture must keep runtime_enabled=false")
for contract_id in (
    "sandbox-terminal-harness-v1",
    "reproducible-execution-pipeline-v1",
    "artifact-lineage-evidence-contract-v1",
):
    check(contract_id in fixture.get("covers", []), f"harness-loop fixture must cover: {contract_id}")

fixture_path = root / fixture.get("path", "")
if not fixture_path.is_file():
    fail(f"missing fixture file: {fixture.get('path')}")
    fixture_data = {}
else:
    try:
        fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid fixture json: {fixture.get('path')}: {exc}")
        fixture_data = {}

fixture_sections = {
    "sandbox-terminal-harness-v1": "sandbox_terminal_harness",
    "reproducible-execution-pipeline-v1": "reproducible_execution_pipeline",
    "artifact-lineage-evidence-contract-v1": "artifact_lineage_evidence",
}


def validate_fixture_data(data, selected_contracts=None):
    local_failures = []

    def local_check(condition, message):
        if not condition:
            local_failures.append(message)

    local_check(data.get("runtime_enabled") is False, "fixture data must keep runtime_enabled=false")
    local_check(data.get("fixture_mode") == "method-only", "fixture data must be method-only")
    contracts = selected_contracts or tuple(fixture_sections.keys())
    for contract_id in contracts:
        section_name = fixture_sections[contract_id]
        section = data.get(section_name, {})
        local_check(isinstance(section, dict), f"fixture section must be object: {section_name}")
        for field in required_fields[contract_id]:
            local_check(field in section and section[field] not in ("", None, []), f"fixture {section_name} missing field: {field}")
    return local_failures


for fixture_failure in validate_fixture_data(fixture_data):
    fail(fixture_failure)

negative_fixtures = manifest.get("negative_fixtures", [])
check(isinstance(negative_fixtures, list) and len(negative_fixtures) >= 3, "negative_fixtures must include at least three failure examples")
for negative_fixture in negative_fixtures if isinstance(negative_fixtures, list) else []:
    if not isinstance(negative_fixture, dict):
        fail("negative_fixtures item must be an object")
        continue
    require_keys(negative_fixture, ["id", "path", "expected_failure", "covers"], f"negative fixture {negative_fixture.get('id', '<missing>')}")
    rel_path = negative_fixture.get("path", "")
    selected_contracts = tuple(negative_fixture.get("covers", []))
    for contract_id in selected_contracts:
        check(contract_id in fixture_sections, f"negative fixture {rel_path} covers unknown contract: {contract_id}")
    path = root / rel_path
    if not path.is_file():
        fail(f"missing negative fixture file: {rel_path}")
        continue
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid negative fixture json: {rel_path}: {exc}")
        continue
    expected_failure = negative_fixture.get("expected_failure")
    check(data.get("expected_failure") == expected_failure, f"negative fixture {rel_path} expected_failure must match manifest")
    negative_failures = validate_fixture_data(data, selected_contracts)
    if not negative_failures:
        fail(f"negative fixture unexpectedly passed: {rel_path}")
        continue
    if expected_failure not in negative_failures:
        fail(f"negative fixture {rel_path} missing expected failure: {expected_failure}")

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
    "durable_execution_requires_replay_idempotency_timeout",
    "typed_hitl_graph_requires_schema_decision_resume",
    "coding_repair_requires_repo_map_lint_test_budget",
    "sandbox_terminal_requires_test_oracle_timeout",
    "reproducible_pipeline_requires_local_ci_parity_trace",
    "artifact_lineage_requires_digest_quality_retention",
    "trace_eval_bundle_requires_dataset_prompt_score",
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
