#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-openai-developers-governance.sh [--summary-json]

Checks OpenAI Developers reference governance:
  - official source freshness records
  - routing/governance/completion eval suite coverage
  - trace evidence contract fields
  - MCP/tool hint audits
  - slash command runtime audit risk fields
  - subagent ownership and handoff contract fields
  - ADK runtime policy and sandbox gates
  - ADK command rule contracts
  - ADK runtime API risk groups
  - context state and session memory contracts
  - OpenAI Docs MCP cross-tool setup contracts
  - hooks runtime audit contracts
  - ADK runner contracts
  - plugin marketplace packaging contracts
  - CI/PR review governance contracts
  - skill reproducibility and version pin contracts
  - model selection decision records
  - data retention and prompt cache policy contracts
  - Codex runtime config, permission, memory and surface-term contracts
  - workflow, agent and skill execution-layer absorption of Codex evidence practices
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

python3 - "$ROOT_DIR" "$SUMMARY_JSON" <<'PY'
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
summary_json = sys.argv[2] == "1"
failures = []

def fail(message):
    failures.append(message)

def load_json(rel):
    path = root / rel
    if not path.is_file():
        fail(f"missing file: {rel}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json: {rel}: {exc}")
        return {}

def require_keys(obj, keys, label):
    for key in keys:
        if key not in obj or obj[key] in ("", None, []):
            fail(f"{label} missing key: {key}")

def require_file_contains(rel, markers, label):
    path = root / rel
    if not path.is_file():
        fail(f"missing file: {rel}")
        return
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            fail(f"{label} missing marker: {marker}")

official = load_json("manifests/official_docs_freshness_gates.json")
evals = load_json("manifests/eval_suites.json")
trace = load_json("manifests/trace_eval_contracts.json")
mcp = load_json("manifests/skill_mcp_dependencies.json")
slash = load_json("manifests/slash_command_runtime_audits.json")
subagents = load_json("manifests/subagent_contracts.json")
runtime_policy = load_json("manifests/adk_runtime_policy_gates.json")
rules = load_json("manifests/adk_rules_contracts.json")
runtime_api = load_json("manifests/adk_runtime_api_contracts.json")
context_state = load_json("manifests/context_state_contracts.json")
docs_mcp_tooling = load_json("manifests/official_docs_mcp_tooling.json")
hooks = load_json("manifests/hooks_runtime_audits.json")
adk_runner = load_json("manifests/adk_runner_contracts.json")
plugins = load_json("manifests/plugin_marketplace_contracts.json")
structured_outputs = load_json("manifests/structured_output_contracts.json")
tool_search = load_json("manifests/tool_search_contracts.json")
automation_worktree = load_json("manifests/automation_worktree_contracts.json")
improvement_loop = load_json("manifests/agent_improvement_loop_contracts.json")
pr_review = load_json("manifests/pr_review_governance_contracts.json")
skill_repro = load_json("manifests/skill_reproducibility_contracts.json")
model_selection = load_json("manifests/model_selection_decision_records.json")
data_retention = load_json("manifests/data_retention_state_contracts.json")
prompt_cache = load_json("manifests/prompt_cache_policy_contracts.json")
codex_surface_terms = load_json("manifests/codex_surface_terms.json")

doc = root / "docs/reference/openai-developers-reference.md"
runbook = root / "docs/runbooks/openai-developers-governance.md"
for rel_path in (doc, runbook):
    if not rel_path.is_file():
        fail(f"missing doc: {rel_path.relative_to(root)}")

execution_layer_markers = {
    "workflows/adk-delivery-gate/WORKFLOW.md": [
        "done-when",
        "replayable-evidence-bundle.md",
        "source-to-live-evidence.md",
        "negative-results",
    ],
    "skills/adk-verification-before-completion/SKILL.md": [
        "Replayable Evidence Bundle",
        "Appshots / UI Evidence Boundary",
        "Runner Smoke Contract",
        "Runtime Control Plane Audit",
        "runtime_config_diff",
        "Trace Eval Regression Evidence",
    ],
    "skills/adk-commit-pr-quality-gate/SKILL.md": [
        "Runtime Control Plane",
        "permission_profile_decision",
        "deny-path test",
    ],
    "skills/adk-requirements-triage/SKILL.md": [
        "Done-when",
        "Required Evidence",
        "Artifact Paths",
        "Blocker Policy",
    ],
    "skills/adk-parallel-agent-governance/SKILL.md": [
        "context_noise_budget",
        "raw_output_retention_decision",
        "parent_merge_policy",
    ],
    "skills/adk-worktree-governance/SKILL.md": [
        "Dirty Worktree Decision",
        "Automation Risk Decision",
        "Heartbeat / Staleness Threshold",
    ],
    "agents/requirements-analyst/AGENTS.md": [
        "done-when",
        "required evidence",
        "artifact paths",
        "blocker policy",
    ],
    "agents/code-review-governor/AGENTS.md": [
        "Completion Claim Audit",
        "Replayable Evidence Bundle",
        "context_noise_budget",
    ],
    "agents/test-validation-engineer/AGENTS.md": [
        "Replayable Evidence Bundle",
        "Appshots/UI evidence boundary",
        "runner smoke contract",
    ],
    "skills/adk-task-breakdown/SKILL.md": [
        "structured_output_schema",
        "strict_schema_decision",
        "adk-task-package-schema-v1",
    ],
    "skills/adk-interface-contract-design/SKILL.md": [
        "strict schema",
        "additionalProperties=false",
        "refusal handling",
    ],
    "skills/adk-after-action-review/SKILL.md": [
        "trace-feedback-eval-handoff",
        "sanitized trace",
        "trace_eval_regression_case",
        "human approval",
    ],
    "skills/adk-engineering-growth-review/SKILL.md": [
        "trace-feedback-eval-handoff",
        "eval candidate",
        "human approval",
    ],
    "skills/adk-code-review-loop/SKILL.md": [
        "schema-backed findings",
        "untrusted PR",
        "trace-feedback-eval-handoff",
    ],
    "workflows/skill-curation-delivery/WORKFLOW.md": [
        "plugin-packaging-review.md",
        "hooks: {}",
        "source path containment",
    ],
    "skills/adk-runtime-router/SKILL.md": [
        "skill-catalog-lazy-loading-v1",
        "namespace_summary",
        "loaded_tools",
    ],
    "skills/adk-token-context-governance/SKILL.md": [
        "tool_search_context_contract",
        "deferred_surface",
        "trusted_inventory",
    ],
    "optional-skills/adk-skill-composition-governance/SKILL.md": [
        "skill-catalog-lazy-loading-v1",
        "initial_surface",
        "deferred_surface",
    ],
    "optional-skills/adk-security-supply-chain/SKILL.md": [
        "Runtime Control Plane Audit",
        "mcp_runtime_contract",
        "permission_profile_decision",
    ],
    "workflows/runtime-routing/WORKFLOW.md": [
        "runtime-control-plane-audit",
        "slash_command_runtime_audit",
        "loaded_tools",
    ],
}
for rel, markers in execution_layer_markers.items():
    require_file_contains(rel, markers, f"execution-layer contract {rel}")

today = dt.date.today()
allowed_domains = set(official.get("review_policy", {}).get("allowed_domains", []))
adoption_review_policy = official.get("adoption_review_policy", {})
require_keys(
    adoption_review_policy,
    [
        "linked_matrices",
        "source_expiry_action",
        "missing_review_status_action",
        "missing_target_evidence_action",
        "review_queue_output",
        "required_target_evidence_prefixes",
        "quality_gates",
    ],
    "official docs adoption_review_policy",
)
for linked_matrix in (
    "agent-dev-kit/docs/reference-adoption-matrix.md",
    "subrepos/adoption-matrix.jsonl",
):
    if linked_matrix not in adoption_review_policy.get("linked_matrices", []):
        fail(f"official docs adoption_review_policy missing linked matrix: {linked_matrix}")
if adoption_review_policy.get("source_expiry_action") != "needs-review":
    fail("official docs adoption_review_policy source_expiry_action must be needs-review")
if adoption_review_policy.get("missing_review_status_action") != "fail":
    fail("official docs adoption_review_policy missing_review_status_action must be fail")
if adoption_review_policy.get("missing_target_evidence_action") != "fail":
    fail("official docs adoption_review_policy missing_target_evidence_action must be fail")
if adoption_review_policy.get("review_queue_output") != "stdout":
    fail("official docs adoption_review_policy review_queue_output must be stdout")
if "agent-dev-kit/" not in adoption_review_policy.get("required_target_evidence_prefixes", []):
    fail("official docs adoption_review_policy must require agent-dev-kit/ evidence")
quality_gates = " ".join(adoption_review_policy.get("quality_gates", [])).lower()
for marker in ("expired official sources", "targeting agent-dev-kit", "review queue"):
    if marker not in quality_gates:
        fail(f"official docs adoption_review_policy quality_gates missing marker: {marker}")
sources = official.get("sources", [])
if not sources:
    fail("official docs source list is empty")

scopes = set()
source_ids = set()
review_status_values = set(official.get("review_policy", {}).get("review_status_values", []))
for source in sources:
    sid = source.get("id", "<missing-id>")
    require_keys(
        source,
        ["id", "title", "url", "retrieved_at", "expires_at", "review_status", "adoption_scope", "owner", "decision", "required_checks"],
        f"official source {sid}",
    )
    source_ids.add(sid)
    url = source.get("url", "")
    domain = urlparse(url).netloc
    if domain not in allowed_domains:
        fail(f"official source {sid} uses non-official domain: {domain}")
    if source.get("review_status") not in review_status_values:
        fail(f"official source {sid} has invalid review_status: {source.get('review_status')}")
    scopes.add(source.get("adoption_scope"))
    try:
        expires_at = dt.date.fromisoformat(source.get("expires_at", ""))
        if expires_at < today:
            fail(f"official source {sid} expired at {expires_at.isoformat()}")
    except ValueError:
        fail(f"official source {sid} has invalid expires_at")
    try:
        dt.date.fromisoformat(source.get("retrieved_at", ""))
    except ValueError:
        fail(f"official source {sid} has invalid retrieved_at")

for scope in ("P0", "P1", "P2"):
    if scope not in scopes:
        fail(f"official docs adoption scope missing: {scope}")
for required_sid in (
    "openai-codex-best-practices",
    "openai-codex-agent-skills",
    "openai-tools-guide",
    "openai-chatgpt-developer-mode",
    "openai-mcp-chatgpt-api-integrations",
    "openai-agentic-macro-evals",
    "openai-structured-model-outputs",
    "openai-function-calling-strict",
    "openai-tool-search",
    "openai-file-search-retrieval",
    "openai-codex-app-automations",
    "openai-codex-app-worktrees",
    "openai-agent-improvement-loop",
    "openai-codex-github-action",
    "openai-codex-code-review-sdk",
    "openai-skills-api-operational-practices",
    "openai-optimizing-llm-accuracy",
    "openai-codex-agents-sdk-multi-agent-workflows",
    "openai-model-optimization-workflow",
    "openai-prompt-engineering-roles",
    "openai-prompt-engineering-formatting",
    "openai-stored-completion-monitoring",
    "openai-agentic-governance-test-dataset",
    "openai-eval-driven-system-design",
    "openai-model-selection-guide",
    "openai-ai-native-engineering-team-docs",
    "openai-data-controls-responses",
    "openai-responses-migration-statefulness",
    "openai-prompt-cache-retention",
    "openai-codex-glossary",
    "openai-codex-permissions",
    "openai-codex-memories",
    "openai-codex-subagents-runtime",
    "openai-codex-record-and-replay",
    "openai-codex-appshots",
    "openai-codex-noninteractive",
):
    if required_sid not in source_ids:
        fail(f"official docs source missing: {required_sid}")

def require_source_refs(manifest, rel):
    for sid in manifest.get("source_docs", []):
        if sid not in source_ids:
            fail(f"{rel} references unknown official source: {sid}")

for manifest, rel in (
    (evals, "manifests/eval_suites.json"),
    (trace, "manifests/trace_eval_contracts.json"),
    (mcp, "manifests/skill_mcp_dependencies.json"),
    (slash, "manifests/slash_command_runtime_audits.json"),
    (subagents, "manifests/subagent_contracts.json"),
    (runtime_policy, "manifests/adk_runtime_policy_gates.json"),
    (rules, "manifests/adk_rules_contracts.json"),
    (runtime_api, "manifests/adk_runtime_api_contracts.json"),
    (context_state, "manifests/context_state_contracts.json"),
    (docs_mcp_tooling, "manifests/official_docs_mcp_tooling.json"),
    (hooks, "manifests/hooks_runtime_audits.json"),
    (adk_runner, "manifests/adk_runner_contracts.json"),
    (plugins, "manifests/plugin_marketplace_contracts.json"),
    (structured_outputs, "manifests/structured_output_contracts.json"),
    (tool_search, "manifests/tool_search_contracts.json"),
    (automation_worktree, "manifests/automation_worktree_contracts.json"),
    (improvement_loop, "manifests/agent_improvement_loop_contracts.json"),
    (pr_review, "manifests/pr_review_governance_contracts.json"),
    (skill_repro, "manifests/skill_reproducibility_contracts.json"),
    (model_selection, "manifests/model_selection_decision_records.json"),
    (data_retention, "manifests/data_retention_state_contracts.json"),
    (prompt_cache, "manifests/prompt_cache_policy_contracts.json"),
    (codex_surface_terms, "manifests/codex_surface_terms.json"),
):
    require_source_refs(manifest, rel)

for forbidden_manifest in (
    "manifests/codex_runtime_policy_gates.json",
    "manifests/codex_rules_contracts.json",
    "manifests/codex_runtime_api_contracts.json",
    "manifests/codex_mcp_runner_contracts.json",
):
    if (root / forbidden_manifest).exists():
        fail(f"stale Codex-bound manifest must be removed: {forbidden_manifest}")

for manifest, rel in (
    (runtime_policy, "manifests/adk_runtime_policy_gates.json"),
    (rules, "manifests/adk_rules_contracts.json"),
    (runtime_api, "manifests/adk_runtime_api_contracts.json"),
    (adk_runner, "manifests/adk_runner_contracts.json"),
):
    if "platform_bindings" in manifest:
        fail(f"{rel} must not define platform_bindings")
    if not manifest.get("reference_boundary"):
        fail(f"{rel} missing reference_boundary")
    if not str(manifest.get("scope_model", "")).startswith("platform-neutral-adk-"):
        fail(f"{rel} must use a platform-neutral ADK scope_model")

suite_categories = {suite.get("category") for suite in evals.get("suites", [])}
for category in ("routing", "governance", "completion", "macro-eval"):
    if category not in suite_categories:
        fail(f"eval suite category missing: {category}")
for suite in evals.get("suites", []):
    require_keys(suite, ["id", "category", "owner", "goal", "dataset_path", "fixtures", "graders", "minimum_gate"], f"eval suite {suite.get('id')}")
suite_ids = {suite.get("id") for suite in evals.get("suites", [])}
for expected_suite in (
    "governance-eval-guardrail-regression-dataset",
    "macro-eval-stored-session-regression-monitoring",
    "completion-eval-goal-done-when-negative-fixtures",
):
    if expected_suite not in suite_ids:
        fail(f"eval suite missing: {expected_suite}")
for suite in evals.get("suites", []):
    if suite.get("id") == "governance-eval-guardrail-regression-dataset":
        expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
        for expected in ("trigger", "do-not-trigger", "analyze-with-boundary"):
            if expected not in expected_values:
                fail(f"guardrail regression suite missing expected case: {expected}")
    if suite.get("id") == "macro-eval-stored-session-regression-monitoring":
        expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
        for expected in ("reject", "accept", "promote-to-regression-candidate"):
            if expected not in expected_values:
                fail(f"stored-session monitoring suite missing expected case: {expected}")
        grader_names = {grader.get("name") for grader in suite.get("graders", [])}
        if "regression_link_present" not in grader_names:
            fail("stored-session monitoring suite missing regression_link_present grader")
    if suite.get("id") == "completion-eval-goal-done-when-negative-fixtures":
        expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
        for expected in ("needs-fix", "pass"):
            if expected not in expected_values:
                fail(f"goal done-when suite missing expected case: {expected}")
        if not any("done-when" in fixture.get("id", "") for fixture in suite.get("fixtures", [])):
            fail("goal done-when suite missing explicit done-when negative fixture")

trace_contracts = trace.get("contracts", [])
if not trace_contracts:
    fail("trace contracts are empty")
required_trace_fields = {
    "run_id",
    "task_id",
    "goal",
    "primary_skill",
    "model_version",
    "prompt_version",
    "orchestration_mode",
    "tool_calls",
    "tools_used",
    "handoffs",
    "guardrails",
    "verification",
    "blockers",
    "failure_pattern",
    "next_goal",
}
for contract in trace_contracts:
    fields = set(contract.get("required_fields", []))
    missing = sorted(required_trace_fields - fields)
    if missing:
        fail(f"trace contract {contract.get('id')} missing fields: {', '.join(missing)}")
    require_keys(contract, ["id", "owner", "applies_to", "evidence_policy", "eval_use"], f"trace contract {contract.get('id')}")
    macro_policy = contract.get("macro_eval_policy", {})
    if macro_policy:
        require_keys(macro_policy, ["group_by", "promotion_rule", "must_not"], f"trace macro_eval_policy {contract.get('id')}")
        for field in ("model_version", "prompt_version", "orchestration_mode", "primary_skill", "failure_pattern"):
            if field not in macro_policy.get("group_by", []):
                fail(f"trace macro_eval_policy {contract.get('id')} missing group_by field: {field}")
    stored_policy = contract.get("stored_session_monitoring_policy", {})
    if stored_policy:
        require_keys(stored_policy, ["enabled_default", "allowed_sources", "required_fields", "must_not"], f"stored_session_monitoring_policy {contract.get('id')}")
        if stored_policy.get("enabled_default") is not False:
            fail(f"stored_session_monitoring_policy {contract.get('id')} must be disabled by default")
        for field in ("source_id", "retention_policy", "redaction_status", "prompt_version", "owner_approval"):
            if field not in stored_policy.get("required_fields", []):
                fail(f"stored_session_monitoring_policy {contract.get('id')} missing required field: {field}")
        if not any("raw user prompts" in item for item in stored_policy.get("must_not", [])):
            fail(f"stored_session_monitoring_policy {contract.get('id')} must reject raw user prompts")
    regression_policy = contract.get("regression_case_policy", {})
    if regression_policy:
        require_keys(regression_policy, ["enabled_default", "required_fields", "promotion_rule", "must_not"], f"regression_case_policy {contract.get('id')}")
        if regression_policy.get("enabled_default") is not False:
            fail(f"regression_case_policy {contract.get('id')} must be disabled by default")
        for field in ("dataset_id", "case_id", "source_trace_id", "prompt_version", "candidate_prompt_version", "expected_regression_signal", "grader", "score_threshold", "regression_link", "retention_policy", "redaction_status", "owner_approval"):
            if field not in regression_policy.get("required_fields", []):
                fail(f"regression_case_policy {contract.get('id')} missing required field: {field}")
        if not any("raw sessions" in item.lower() or "unredacted traces" in item.lower() for item in regression_policy.get("must_not", [])):
            fail(f"regression_case_policy {contract.get('id')} must reject raw sessions or unredacted traces")
    replay_policy = contract.get("replay_policy", {})
    if contract.get("id") == "replayable-run-evidence-bundle-v1":
        fields = set(contract.get("required_fields", []))
        for field in (
            "input_snapshot",
            "environment_snapshot",
            "tool_transcript_digest",
            "artifact_hashes",
            "expected_assertions",
            "replay_safety_boundary",
            "sensitive_data_review",
            "manual_replay_notes",
            "non_replayable_reason",
        ):
            if field not in fields:
                fail(f"replayable run evidence contract missing field: {field}")
        require_keys(replay_policy, ["enabled_default", "promotion_rule", "required_assertions", "must_not"], "replayable run evidence policy")
        if replay_policy.get("enabled_default") is not False:
            fail("replayable run evidence policy must be disabled by default")
        if not any("sensitive" in item.lower() for item in replay_policy.get("required_assertions", [])):
            fail("replayable run evidence policy must require sensitive-data assertion")
        if not any("unattended automation" in item.lower() for item in replay_policy.get("must_not", [])):
            fail("replayable run evidence policy must not promote unattended automation from one demonstration")
if "replayable-run-evidence-bundle-v1" not in {contract.get("id") for contract in trace_contracts}:
    fail("trace contracts missing replayable-run-evidence-bundle-v1")
if not any(contract.get("regression_case_policy") for contract in trace_contracts):
    fail("trace contracts missing regression_case_policy")

tool_description_policy = mcp.get("tool_description_policy", {})
require_keys(tool_description_policy, ["required_elements", "review_payloads", "remembered_approvals"], "mcp tool_description_policy")
for element in ("Use this when guidance", "disallowed or edge cases", "parameter descriptions and enums when applicable", "side-effect and approval class"):
    if element not in tool_description_policy.get("required_elements", []):
        fail(f"mcp tool_description_policy missing required element: {element}")

data_only_mcp = mcp.get("data_only_mcp_compatibility", {})
require_keys(data_only_mcp, ["preferred_tools", "search_required_output", "fetch_required_output", "compatibility_note", "risk_review"], "mcp data_only_mcp_compatibility")
for tool in ("search", "fetch"):
    if tool not in data_only_mcp.get("preferred_tools", []):
        fail(f"mcp data_only_mcp_compatibility missing preferred tool: {tool}")
for field in ("structuredContent.results[].id", "structuredContent.results[].title", "structuredContent.results[].url"):
    if field not in data_only_mcp.get("search_required_output", []):
        fail(f"mcp data_only_mcp_compatibility missing search field: {field}")
for field in ("structuredContent.id", "structuredContent.title", "structuredContent.text", "structuredContent.url"):
    if field not in data_only_mcp.get("fetch_required_output", []):
        fail(f"mcp data_only_mcp_compatibility missing fetch field: {field}")

mcp_runtime_policy = mcp.get("runtime_config_policy", {})
require_keys(
    mcp_runtime_policy,
    [
        "required_server_fields",
        "required_http_fields",
        "required_oauth_fields",
        "approval_modes",
        "quality_gates",
        "must_not",
    ],
    "mcp runtime_config_policy",
)
for field in ("enabled", "required", "startup_timeout_sec", "tool_timeout_sec", "enabled_tools", "disabled_tools", "default_tools_approval_mode"):
    if field not in mcp_runtime_policy.get("required_server_fields", []):
        fail(f"mcp runtime_config_policy missing server field: {field}")
for field in ("bearer_token_env_var", "env_http_headers"):
    if field not in mcp_runtime_policy.get("required_http_fields", []):
        fail(f"mcp runtime_config_policy missing HTTP field: {field}")
for field in ("mcp_oauth_credentials_store", "mcp_oauth_callback_port", "mcp_oauth_callback_url", "scopes"):
    if field not in mcp_runtime_policy.get("required_oauth_fields", []):
        fail(f"mcp runtime_config_policy missing OAuth field: {field}")
for mode in ("auto", "prompt", "approve"):
    if mode not in mcp_runtime_policy.get("approval_modes", []):
        fail(f"mcp runtime_config_policy missing approval mode: {mode}")
if not any("destructive" in item.lower() and "prompt" in item.lower() for item in mcp_runtime_policy.get("quality_gates", [])):
    fail("mcp runtime_config_policy must require prompt mode for write-capable/open-world tools")
if not any("bearer tokens" in item.lower() for item in mcp_runtime_policy.get("must_not", [])):
    fail("mcp runtime_config_policy must forbid bearer tokens in manifests or project config")

for dep in mcp.get("dependencies", []):
    require_keys(
        dep,
        [
            "skill",
            "mcp_server",
            "purpose",
            "transport",
            "required",
            "startup_timeout_sec",
            "tool_timeout_sec",
            "default_tools_approval_mode",
            "per_tool_approval_mode",
            "oauth",
            "tool_hints",
            "auth_boundary",
            "pii_policy",
            "dry_run",
            "fallback",
        ],
        f"mcp dependency {dep.get('skill')}",
    )
    for key in ("enabled_tools", "disabled_tools"):
        if key not in dep or not isinstance(dep[key], list):
            fail(f"mcp dependency {dep.get('skill')} missing list key: {key}")
    hints = dep.get("tool_hints", {})
    for key in ("readOnlyHint", "destructiveHint", "openWorldHint"):
        if key not in hints or not isinstance(hints[key], bool):
            fail(f"mcp dependency {dep.get('skill')} missing boolean tool_hints.{key}")
    if dep.get("startup_timeout_sec", 0) <= 0:
        fail(f"mcp dependency {dep.get('skill')} startup_timeout_sec must be positive")
    if dep.get("tool_timeout_sec", 0) <= 0:
        fail(f"mcp dependency {dep.get('skill')} tool_timeout_sec must be positive")
    if dep.get("default_tools_approval_mode") not in {"auto", "prompt", "approve"}:
        fail(f"mcp dependency {dep.get('skill')} has invalid default_tools_approval_mode")
    oauth = dep.get("oauth", {})
    for key in ("callback_port", "callback_url", "scopes"):
        if key not in oauth:
            fail(f"mcp dependency {dep.get('skill')} missing oauth.{key}")
if not mcp.get("dependencies"):
    fail("mcp dependencies are empty")

for audit in slash.get("audits", []):
    require_keys(audit, ["command_id", "command", "owner", "mode", "read_only", "destructive", "open_world", "approval", "evidence_required"], f"slash audit {audit.get('command_id')}")
    if audit.get("destructive") and audit.get("mode") in {"approved", "auto-approved"}:
        fail(f"slash audit {audit.get('command_id')} destructive command cannot default to approved mode")
if not slash.get("audits"):
    fail("slash command audits are empty")

for contract in subagents.get("contracts", []):
    require_keys(contract, ["id", "owner", "scope_read", "scope_write", "must_not_touch", "handoff_condition", "reply_owner", "stop_condition", "report_schema", "conflict_policy"], f"subagent contract {contract.get('id')}")
    stop_condition = contract.get("stop_condition", "")
    for token in ("pass", "replan", "split", "blocked", "abort"):
        if token not in stop_condition:
            fail(f"subagent contract {contract.get('id')} stop_condition missing {token}")
    report_schema = contract.get("report_schema", [])
    for field in ("summary", "evidence_refs", "raw_output_policy"):
        if field not in report_schema:
            fail(f"subagent contract {contract.get('id')} report_schema missing {field}")
if not subagents.get("contracts"):
    fail("subagent contracts are empty")

subagent_runtime_limits = subagents.get("runtime_limits", {})
require_keys(
    subagent_runtime_limits,
    [
        "max_threads_default",
        "max_depth_default",
        "job_max_runtime_seconds_fallback",
        "nested_subagents_default_allowed",
        "must_record",
        "must_not",
    ],
    "subagent runtime_limits",
)
if subagent_runtime_limits.get("max_threads_default") != 6:
    fail("subagent runtime_limits max_threads_default must be 6")
if subagent_runtime_limits.get("max_depth_default") != 1:
    fail("subagent runtime_limits max_depth_default must be 1")
if subagent_runtime_limits.get("job_max_runtime_seconds_fallback") != 1800:
    fail("subagent runtime_limits job_max_runtime_seconds_fallback must be 1800")
if subagent_runtime_limits.get("nested_subagents_default_allowed") is not False:
    fail("subagent runtime_limits nested subagents must be disabled by default")
for field in (
    "features.multi_agent",
    "agents.max_threads",
    "agents.max_depth",
    "agents.job_max_runtime_seconds",
    "scope_write",
    "subagent_result.summary",
    "subagent_result.evidence_refs",
    "subagent_result.raw_output_retention_decision",
):
    if field not in subagent_runtime_limits.get("must_record", []):
        fail(f"subagent runtime_limits missing must_record field: {field}")
if not any("nested" in item.lower() for item in subagent_runtime_limits.get("must_not", [])):
    fail("subagent runtime_limits must forbid implicit nested subagents")
if not any("raw logs" in item.lower() or "command transcripts" in item.lower() for item in subagent_runtime_limits.get("must_not", [])):
    fail("subagent runtime_limits must forbid raw noisy output by default")

subagent_noise_budget = subagents.get("context_noise_budget", {})
require_keys(
    subagent_noise_budget,
    [
        "enabled_default",
        "required_fields",
        "summary_token_budget",
        "raw_output_policy",
        "quality_gates",
        "must_not",
    ],
    "subagent context_noise_budget",
)
if subagent_noise_budget.get("enabled_default") is not True:
    fail("subagent context_noise_budget must be enabled by default")
for field in (
    "summary_token_budget",
    "evidence_ref_count",
    "raw_output_retention_decision",
    "redaction_status",
    "parent_context_merge_policy",
    "noise_rejection_reason",
):
    if field not in subagent_noise_budget.get("required_fields", []):
        fail(f"subagent context_noise_budget missing required field: {field}")
if subagent_noise_budget.get("summary_token_budget", {}).get("default_soft_limit", 0) <= 0:
    fail("subagent context_noise_budget summary soft limit must be positive")
if not any("raw output" in gate.lower() and "retention" in gate.lower() for gate in subagent_noise_budget.get("quality_gates", [])):
    fail("subagent context_noise_budget must require raw output retention decision")
if not any("raw command transcripts" in item.lower() for item in subagent_noise_budget.get("must_not", [])):
    fail("subagent context_noise_budget must forbid raw command transcripts by default")

runtime_layers = runtime_policy.get("policy_layers", [])
if not runtime_layers:
    fail("runtime policy layers are empty")
layer_ids = {layer.get("id") for layer in runtime_layers}
for expected in ("managed-runtime-requirements", "project-runtime-boundary"):
    if expected not in layer_ids:
        fail(f"runtime policy layer missing: {expected}")
for layer in runtime_layers:
    lid = layer.get("id")
    require_keys(layer, ["id", "owner", "config_file", "precedence", "user_override_allowed", "required_controls", "verification"], f"runtime policy layer {lid}")
    if lid == "managed-runtime-requirements" and layer.get("user_override_allowed") is not False:
        fail("managed runtime requirements must not allow user override")
    if lid == "project-runtime-boundary":
        must_not_override = set(layer.get("must_not_override", []))
        for key in ("openai_base_url", "chatgpt_base_url", "apps_mcp_product_sku", "model_provider", "model_providers", "notify", "profile", "profiles", "experimental_realtime_ws_base_url", "otel"):
            if key not in must_not_override:
                fail(f"project config boundary missing must_not_override: {key}")
    network = layer.get("network_policy")
    if network:
        if network.get("deny_wins") is not True:
            fail(f"runtime policy layer {lid} must enforce deny-wins network policy")
        if network.get("global_allow_allowed") is not False:
            fail(f"runtime policy layer {lid} must forbid global network allow by default")
        if network.get("network_proxy_required_when_network_enabled") is not True:
            fail(f"runtime policy layer {lid} must require network_proxy when command network is enabled")
        if network.get("allow_local_binding_default") is not False:
            fail(f"runtime policy layer {lid} must keep allow_local_binding disabled by default")
        if network.get("dangerously_allow_non_loopback_proxy_default") is not False:
            fail(f"runtime policy layer {lid} must forbid non-loopback proxy by default")
        if network.get("dangerously_allow_all_unix_sockets_default") is not False:
            fail(f"runtime policy layer {lid} must forbid all Unix sockets by default")
        if network.get("unix_sockets_allowlist_required") is not True:
            fail(f"runtime policy layer {lid} must require Unix socket allowlist")
    web_search = layer.get("web_search_policy")
    if web_search:
        allowed_modes = set(web_search.get("allowed_modes", []))
        if not {"disabled", "cached"}.issubset(allowed_modes):
            fail(f"runtime policy layer {lid} web_search_policy must allow disabled and cached modes")
        if web_search.get("live_requires_explicit_approval") is not True:
            fail(f"runtime policy layer {lid} live web search must require explicit approval")
        if web_search.get("treat_results_as_untrusted") is not True:
            fail(f"runtime policy layer {lid} must treat web results as untrusted")

sandbox_presets = runtime_policy.get("sandbox_presets", [])
if not sandbox_presets:
    fail("sandbox presets are empty")
preset_by_id = {preset.get("id"): preset for preset in sandbox_presets}
low_risk = preset_by_id.get("low-risk-local-automation", {})
if low_risk.get("sandbox_mode") != "workspace-write" or low_risk.get("approval_policy") != "on-request":
    fail("low-risk sandbox preset must be workspace-write + on-request")
full_access = preset_by_id.get("full-access", {})
if full_access.get("sandbox_mode") != "danger-full-access" or full_access.get("approval_policy") != "never":
    fail("full-access preset must explicitly model danger-full-access + never")
if full_access.get("default_allowed") is not False or full_access.get("risk") != "critical":
    fail("full-access preset must be critical and not default allowed")
for forbidden in runtime_policy.get("forbidden_defaults", []):
    require_keys(forbidden, ["id", "reason"], f"forbidden default {forbidden.get('id')}")
for forbidden_id in ("network-proxy-non-loopback", "all-unix-sockets", "web-search-live-default"):
    if forbidden_id not in {item.get("id") for item in runtime_policy.get("forbidden_defaults", [])}:
        fail(f"runtime forbidden default missing: {forbidden_id}")

config_boundaries = runtime_policy.get("config_key_boundaries", {})
require_keys(
    config_boundaries,
    [
        "project_local_must_not_override",
        "user_level_only",
        "project_local_allowed_when_trusted",
        "verification",
    ],
    "runtime config_key_boundaries",
)
for key in ("openai_base_url", "chatgpt_base_url", "apps_mcp_product_sku", "model_provider", "model_providers", "notify", "profile", "profiles", "experimental_realtime_ws_base_url", "otel"):
    if key not in config_boundaries.get("project_local_must_not_override", []):
        fail(f"runtime config_key_boundaries missing project-local deny key: {key}")
for key in ("provider", "auth", "telemetry_routing"):
    if key not in config_boundaries.get("user_level_only", []):
        fail(f"runtime config_key_boundaries missing user-level-only key: {key}")
if "trust_level" not in " ".join(config_boundaries.get("verification", [])):
    fail("runtime config_key_boundaries must record trust_level verification")

granular_approval = runtime_policy.get("granular_approval_policy", {})
require_keys(granular_approval, ["allowed_keys", "default_reviewer", "auto_review_requires_policy", "must_record", "must_not"], "runtime granular_approval_policy")
for key in ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval"):
    if key not in granular_approval.get("allowed_keys", []):
        fail(f"runtime granular_approval_policy missing key: {key}")
if granular_approval.get("auto_review_requires_policy") is not True:
    fail("runtime granular_approval_policy must require auto_review policy")
if not any("human approval" in item.lower() for item in granular_approval.get("must_not", [])):
    fail("runtime granular_approval_policy must not treat auto_review as human approval")

permission_policy = runtime_policy.get("permission_profile_policy", {})
require_keys(permission_policy, ["built_in_profiles", "custom_profile_required_fields", "deny_read_controls", "network_controls", "must_not"], "runtime permission_profile_policy")
for profile in (":read-only", ":workspace", ":danger-full-access"):
    if profile not in permission_policy.get("built_in_profiles", []):
        fail(f"runtime permission_profile_policy missing built-in profile: {profile}")
for field in ("description", "extends", "filesystem", "network", "workspace_roots"):
    if field not in permission_policy.get("custom_profile_required_fields", []):
        fail(f"runtime permission_profile_policy missing custom profile field: {field}")
if not any("deny" in item.lower() for item in permission_policy.get("deny_read_controls", [])):
    fail("runtime permission_profile_policy must include deny-read controls")
if not any("unix" in item.lower() for item in permission_policy.get("network_controls", [])):
    fail("runtime permission_profile_policy must include Unix socket controls")
if not any(":danger-full-access" in item for item in permission_policy.get("must_not", [])):
    fail("runtime permission_profile_policy must forbid extending :danger-full-access")

memory_runtime_policy = runtime_policy.get("memory_runtime_policy", {})
require_keys(memory_runtime_policy, ["feature_flag", "default_enabled", "required_fields", "external_context_controls", "quality_gates", "must_not"], "runtime memory_runtime_policy")
if memory_runtime_policy.get("feature_flag") != "features.memories":
    fail("runtime memory_runtime_policy feature_flag must be features.memories")
if memory_runtime_policy.get("default_enabled") is not False:
    fail("runtime memory_runtime_policy must be disabled by default")
for field in ("memories.generate_memories", "memories.use_memories", "memories.disable_on_external_context", "memories.max_rollout_age_days", "memories.min_rollout_idle_hours"):
    if field not in memory_runtime_policy.get("required_fields", []):
        fail(f"runtime memory_runtime_policy missing field: {field}")
for control in ("MCP", "web_search", "tool_search"):
    if control not in memory_runtime_policy.get("external_context_controls", []):
        fail(f"runtime memory_runtime_policy missing external context control: {control}")
if not any("owner approval" in item.lower() for item in memory_runtime_policy.get("quality_gates", [])):
    fail("runtime memory_runtime_policy must require owner approval")
if not any("raw session transcripts" in item.lower() for item in memory_runtime_policy.get("must_not", [])):
    fail("runtime memory_runtime_policy must forbid raw session transcript memory")

rule_contracts = rules.get("contracts", [])
if not rule_contracts:
    fail("ADK rules contracts are empty")
for contract in rule_contracts:
    cid = contract.get("id")
    require_keys(
        contract,
        [
            "id",
            "owner",
            "scope",
            "rules_file",
            "decision_values",
            "required_fields",
            "minimum_match_examples",
            "minimum_not_match_examples",
            "compound_shell_policy",
            "forbidden_prefix_examples",
            "verification",
            "promotion_gate",
        ],
        f"rules contract {cid}",
    )
    decisions = set(contract.get("decision_values", []))
    if not decisions.issubset({"allow", "prompt", "forbidden"}):
        fail(f"rules contract {cid} has invalid decision_values")
    fields = set(contract.get("required_fields", []))
    for field in ("pattern", "decision", "justification", "match", "not_match"):
        if field not in fields:
            fail(f"rules contract {cid} missing required_fields entry: {field}")
    if contract.get("minimum_match_examples", 0) < 1:
        fail(f"rules contract {cid} must require at least one match example")
    if contract.get("minimum_not_match_examples", 0) < 1:
        fail(f"rules contract {cid} must require at least one not_match example")

runtime_api_groups = runtime_api.get("method_groups", [])
if not runtime_api_groups:
    fail("ADK runtime API method groups are empty")
required_api_groups = {
    "thread-lifecycle-read",
    "thread-state-write",
    "thread-destructive-state",
    "process-and-shell-open-world",
    "sandboxed-command-exec",
    "fs-config-plugin-write",
    "mcp-app-tool-bridge",
}
api_group_ids = {group.get("id") for group in runtime_api_groups}
for group_id in required_api_groups:
    if group_id not in api_group_ids:
        fail(f"ADK runtime API group missing: {group_id}")
transport_policy = runtime_api.get("transport_policy", {})
require_keys(transport_policy, ["supported", "experimental", "forbidden_defaults", "required_auth_for_remote"], "ADK runtime API transport policy")
if "non-loopback unauthenticated websocket" not in transport_policy.get("forbidden_defaults", []):
    fail("ADK runtime API transport policy must forbid non-loopback unauthenticated websocket")
for group in runtime_api_groups:
    gid = group.get("id")
    require_keys(group, ["id", "owner", "methods", "risk", "classification", "required_evidence", "approval_boundary"], f"ADK runtime API group {gid}")
    classification = group.get("classification", {})
    for key in ("read_only", "destructive", "open_world", "sandbox_inherited"):
        if key not in classification or not isinstance(classification[key], bool):
            fail(f"ADK runtime API group {gid} missing boolean classification.{key}")
    if gid == "process-and-shell-open-world":
        if "thread/shellCommand" not in group.get("methods", []):
            fail("process-and-shell-open-world must include thread/shellCommand")
        if classification.get("sandbox_inherited") is not False or classification.get("open_world") is not True:
            fail("process-and-shell-open-world must be open-world and not inherit thread sandbox")
    if gid == "fs-config-plugin-write" and classification.get("destructive") is not True:
        fail("fs-config-plugin-write must be destructive")

context_contracts = context_state.get("contracts", [])
if not context_contracts:
    fail("context state contracts are empty")
context_ids = {contract.get("id") for contract in context_contracts}
if "instruction-hierarchy-context-boundary" not in context_ids:
    fail("context state contract missing: instruction-hierarchy-context-boundary")
for contract in context_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "required_fields", "quality_gates", "poisoning_controls", "verification"], f"context state contract {cid}")
    if "context_classes" in contract:
        classes = set(contract.get("context_classes", []))
        for context_class in ("stable", "dynamic", "evidence", "excluded"):
            if context_class not in classes:
                fail(f"context state contract {cid} missing context class: {context_class}")
    required_fields = set(contract.get("required_fields", []))
    if cid == "long-thread-session-summary":
        for field in ("latest_goal", "invalidated_goals", "raw_evidence", "next_goal", "fallback_condition"):
            if field not in required_fields:
                fail(f"context state contract {cid} missing field: {field}")
    if cid == "responses-state-handoff":
        for field in (
            "previous_response_id_policy",
            "phase_preservation",
            "prompt_cache_layout",
            "retention_mode",
            "encrypted_reasoning_policy",
            "store_false_policy",
            "call_id_correlation_policy",
            "state_retention_evidence",
        ):
            if field not in required_fields:
                fail(f"context state contract {cid} missing field: {field}")
    if cid == "instruction-hierarchy-context-boundary":
        require_keys(contract, ["authority_layers"], "instruction hierarchy context contract")
        for layer in ("system_developer_policy", "repo_agents_policy", "skill_contract", "user_goal", "dynamic_context", "tool_output"):
            if layer not in contract.get("authority_layers", []):
                fail(f"instruction hierarchy contract missing authority layer: {layer}")
        for field in ("authority_boundary", "dynamic_context_boundary", "tool_output_trust_level", "conflict_resolution"):
            if field not in required_fields:
                fail(f"instruction hierarchy contract missing required field: {field}")
        if not any("tool output" in item.lower() and "not policy" in item.lower() for item in contract.get("quality_gates", [])):
            fail("instruction hierarchy contract must state tool outputs are not policy")

docs_mcp_server = docs_mcp_tooling.get("server", {})
require_keys(docs_mcp_server, ["name", "url", "transport", "purpose"], "OpenAI Docs MCP server")
if docs_mcp_server.get("url") != "https://developers.openai.com/mcp":
    fail("OpenAI Docs MCP server URL must be https://developers.openai.com/mcp")
docs_tool_targets = docs_mcp_tooling.get("tooling_targets", [])
if not docs_tool_targets:
    fail("OpenAI Docs MCP tooling targets are empty")
target_ids = {target.get("id") for target in docs_tool_targets}
for target_id in ("generic-mcp-client", "vscode", "cursor", "claude-code"):
    if target_id not in target_ids:
        fail(f"OpenAI Docs MCP tooling target missing: {target_id}")
for target in docs_tool_targets:
    tid = target.get("id")
    require_keys(target, ["id", "config_files", "install_command", "verification", "agents_instruction"], f"OpenAI Docs MCP tooling target {tid}")
freshness_policy = docs_mcp_tooling.get("freshness_policy", {})
require_keys(freshness_policy, ["source_manifest", "max_age_days", "fallback_domains", "must_not"], "OpenAI Docs MCP freshness policy")
if "developers.openai.com" not in freshness_policy.get("fallback_domains", []):
    fail("OpenAI Docs MCP freshness policy must include developers.openai.com fallback domain")

hook_events = hooks.get("events", [])
if not hook_events:
    fail("hook runtime audits are empty")
required_hook_fields = set(hooks.get("required_audit_fields", []))
for field in ("event", "supports_matcher", "supported_output_fields", "must_not_rely_on", "trust_required"):
    if field not in required_hook_fields:
        fail(f"hook required_audit_fields missing: {field}")
hook_by_event = {event.get("event"): event for event in hook_events}
for event in ("PreToolUse", "PermissionRequest", "PostToolUse", "Stop"):
    if event not in hook_by_event:
        fail(f"hook event audit missing: {event}")
for event in hook_events:
    eid = event.get("event")
    require_keys(event, ["event", "supports_matcher", "supported_output_fields", "must_not_rely_on", "side_effect_policy", "trust_required", "concurrency_risk"], f"hook event {eid}")
    if not isinstance(event.get("supports_matcher"), bool):
        fail(f"hook event {eid} supports_matcher must be boolean")
    if event.get("trust_required") is not True:
        fail(f"hook event {eid} must require trust")
pre_tool = hook_by_event.get("PreToolUse", {})
if "continue" not in pre_tool.get("must_not_rely_on", []):
    fail("PreToolUse must not rely on continue")
stop_hook = hook_by_event.get("Stop", {})
if stop_hook.get("supports_matcher") is not False:
    fail("Stop hook matcher must be marked unsupported")
if "matcher" not in stop_hook.get("must_not_rely_on", []):
    fail("Stop hook must_not_rely_on must include matcher")
if not hooks.get("deny_path"):
    fail("hooks deny_path is empty")
if not hooks.get("log_redaction"):
    fail("hooks log_redaction is empty")

adk_runner_contracts = adk_runner.get("contracts", [])
if not adk_runner_contracts:
    fail("ADK runner contracts are empty")
runner_smoke = adk_runner.get("smoke_contract", {})
require_keys(runner_smoke, ["id", "owner", "applies_to", "required_evidence", "quality_gates", "must_not"], "ADK runner smoke_contract")
for field in (
    "client_info_or_adapter_id",
    "thread_start_result",
    "turn_start_result",
    "jsonl_or_structured_event_stream",
    "output_schema_validation",
    "sandbox_policy_record",
    "approval_policy_record",
    "cwd_record",
    "resume_or_reply_correlation",
    "failure_or_cancel_path",
):
    if field not in runner_smoke.get("required_evidence", []):
        fail(f"ADK runner smoke_contract missing evidence field: {field}")
if not any("JSONL" in gate or "strict output schema" in gate for gate in runner_smoke.get("quality_gates", [])):
    fail("ADK runner smoke_contract must require JSONL or strict schema output")
if not any("API keys" in item or "auth files" in item for item in runner_smoke.get("must_not", [])):
    fail("ADK runner smoke_contract must protect API keys or auth files")
adk_runner_tools = {contract.get("tool") for contract in adk_runner_contracts}
for tool in ("run-session", "reply-session"):
    if tool not in adk_runner_tools:
        fail(f"ADK runner contract missing tool: {tool}")
for contract in adk_runner_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "tool", "purpose", "required_inputs", "approval_boundary", "sandbox_boundary", "state_output", "must_record", "stop_condition"], f"ADK runner contract {cid}")
    if contract.get("tool") == "reply-session" and "threadId" not in contract.get("required_inputs", []):
        fail("reply-session contract must require threadId")
    for token in ("pass", "replan", "split", "blocked", "abort"):
        if token not in contract.get("stop_condition", ""):
            fail(f"ADK runner contract {cid} stop_condition missing {token}")

plugin_contracts = plugins.get("plugin_contracts", [])
marketplace_contracts = plugins.get("marketplace_contracts", [])
if not plugin_contracts:
    fail("plugin contracts are empty")
if not marketplace_contracts:
    fail("marketplace contracts are empty")
for contract in plugin_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "required_files", "naming", "allowed_extensions", "required_review"], f"plugin contract {cid}")
    files = set(contract.get("required_files", []))
    for required_file in (".adk-plugin/plugin.json", "skills/<skill-name>/SKILL.md"):
        if required_file not in files:
            fail(f"plugin contract {cid} missing required file: {required_file}")
    if "stable kebab-case" not in contract.get("naming", {}).get("plugin_name", ""):
        fail(f"plugin contract {cid} must require stable kebab-case plugin name")
for contract in marketplace_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "path", "required_fields", "source_path_policy", "install_policy_values", "failure_policy"], f"marketplace contract {cid}")
    required_fields = set(contract.get("required_fields", []))
    for field in ("plugins[].source.path", "plugins[].policy.installation", "plugins[].policy.authentication", "plugins[].category"):
        if field not in required_fields:
            fail(f"marketplace contract {cid} missing required field: {field}")
    for value in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"):
        if value not in contract.get("install_policy_values", []):
            fail(f"marketplace contract {cid} missing install policy value: {value}")

structured_contracts = structured_outputs.get("contracts", [])
if not structured_contracts:
    fail("structured output contracts are empty")
required_schema_targets = {"task_package", "evidence_index", "handoff_summary", "pr_review_findings"}
seen_schema_targets = {contract.get("schema_target") for contract in structured_contracts}
for target in required_schema_targets:
    if target not in seen_schema_targets:
        fail(f"structured output schema target missing: {target}")
for contract in structured_contracts:
    cid = contract.get("id")
    require_keys(
        contract,
        [
            "id",
            "owner",
            "applies_to",
            "schema_target",
            "schema_format",
            "strict",
            "required_fields",
            "additional_properties",
            "refusal_handling",
            "drift_controls",
        ],
        f"structured output contract {cid}",
    )
    if contract.get("schema_format") != "json_schema":
        fail(f"structured output contract {cid} must use json_schema")
    if contract.get("strict") is not True:
        fail(f"structured output contract {cid} must require strict mode")
    if contract.get("additional_properties") is not False:
        fail(f"structured output contract {cid} must deny additional properties")
    if len(contract.get("required_fields", [])) < 5:
        fail(f"structured output contract {cid} has too few required fields")
    if not contract.get("drift_controls"):
        fail(f"structured output contract {cid} missing drift controls")
structured_gate = structured_outputs.get("quality_gate", {})
require_keys(
    structured_gate,
    [
        "must_use_structured_outputs_over_json_mode",
        "json_mode_allowed_only_with_validation",
        "must_detect_refusals",
        "must_not",
    ],
    "structured output quality_gate",
)
if structured_gate.get("must_use_structured_outputs_over_json_mode") is not True:
    fail("structured output quality_gate must prefer structured outputs over JSON mode")
if structured_gate.get("must_detect_refusals") is not True:
    fail("structured output quality_gate must detect refusals")

tool_search_contracts = tool_search.get("contracts", [])
if not tool_search_contracts:
    fail("tool search contracts are empty")
for contract in tool_search_contracts:
    cid = contract.get("id")
    require_keys(
        contract,
        [
            "id",
            "owner",
            "applies_to",
            "namespace",
            "initial_surface",
            "deferred_surface",
            "max_initial_items",
            "max_namespace_tools",
            "selection_evidence",
            "cache_policy",
            "must_not",
        ],
        f"tool search contract {cid}",
    )
    if contract.get("max_initial_items", 0) > 20:
        fail(f"tool search contract {cid} max_initial_items must be <= 20")
    if contract.get("max_namespace_tools", 0) > 10:
        fail(f"tool search contract {cid} max_namespace_tools must be <= 10")
    for field in ("name", "description"):
        if not any(field in item for item in contract.get("initial_surface", [])):
            fail(f"tool search contract {cid} initial_surface must include {field}")
    if not contract.get("deferred_surface"):
        fail(f"tool search contract {cid} missing deferred_surface")
tool_search_gate = tool_search.get("quality_gate", {})
require_keys(
    tool_search_gate,
    [
        "deferred_loading_requires_namespace_summary",
        "tool_schema_review_required",
        "client_executed_search_requires_trusted_inventory",
        "must_record_loaded_tools",
    ],
    "tool search quality_gate",
)
for key in (
    "deferred_loading_requires_namespace_summary",
    "tool_schema_review_required",
    "client_executed_search_requires_trusted_inventory",
    "must_record_loaded_tools",
):
    if tool_search_gate.get(key) is not True:
        fail(f"tool search quality_gate {key} must be true")

automation_contracts = automation_worktree.get("automation_contracts", [])
worktree_contracts = automation_worktree.get("worktree_contracts", [])
if not automation_contracts:
    fail("automation contracts are empty")
if not worktree_contracts:
    fail("worktree contracts are empty")
for contract in automation_contracts:
    cid = contract.get("id")
    require_keys(
        contract,
        [
            "id",
            "owner",
            "mode",
            "enabled_default",
            "prompt_requirements",
            "run_context",
            "sandbox_policy",
            "approval_policy",
            "first_run_review",
            "first_run_evidence",
            "reliability_promotion_gate",
            "result_policy",
            "cleanup_policy",
        ],
        f"automation contract {cid}",
    )
    if contract.get("mode") != "report-only":
        fail(f"automation contract {cid} must default to report-only")
    if contract.get("enabled_default") is not False:
        fail(f"automation contract {cid} must be disabled by default")
    if contract.get("first_run_review") is not True:
        fail(f"automation contract {cid} must require first-run review")
    first_run_evidence = contract.get("first_run_evidence", [])
    if len(first_run_evidence) < 3:
        fail(f"automation contract {cid} first_run_evidence must contain at least three evidence items")
    for required_evidence in ("run", "summary"):
        if not any(required_evidence in item for item in first_run_evidence):
            fail(f"automation contract {cid} first_run_evidence missing {required_evidence}")
    for required_prompt in ("durable", "stop"):
        if not any(required_prompt in item for item in contract.get("prompt_requirements", [])):
            fail(f"automation contract {cid} prompt_requirements missing {required_prompt}")
    promotion_gate = contract.get("reliability_promotion_gate", [])
    if len(promotion_gate) < 3:
        fail(f"automation contract {cid} reliability_promotion_gate must contain at least three gate items")
    for required_gate in ("manual", "report-only", "owner approval", "rollback"):
        if not any(required_gate in item for item in promotion_gate):
            fail(f"automation contract {cid} reliability_promotion_gate missing {required_gate}")
for contract in worktree_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "creation_gate", "handoff_gate", "cleanup_gate", "must_not"], f"worktree contract {cid}")
    for gate_name in ("creation_gate", "handoff_gate", "cleanup_gate"):
        if not contract.get(gate_name):
            fail(f"worktree contract {cid} missing non-empty {gate_name}")
    if not any("branch" in item for item in contract.get("handoff_gate", [])):
        fail(f"worktree contract {cid} handoff_gate must mention branch limitations")
automation_gate = automation_worktree.get("quality_gate", {})
require_keys(
    automation_gate,
    [
        "automations_enabled_default_must_be_false",
        "first_runs_require_review",
        "first_run_evidence_required",
        "manual_reliable_before_scheduling",
        "promotion_requires_report_only_history",
        "promotion_evidence_required",
        "enabled_mode_requires_owner_approval_and_rollback",
        "full_access_never_for_default_automation",
        "worktree_cleanup_requires_retention_decision",
        "risk_fixtures_required",
        "dirty_worktree_requires_decision",
        "stale_heartbeat_requires_stop_or_replan",
    ],
    "automation worktree quality_gate",
)
for key in (
    "automations_enabled_default_must_be_false",
    "first_runs_require_review",
    "first_run_evidence_required",
    "manual_reliable_before_scheduling",
    "promotion_requires_report_only_history",
    "promotion_evidence_required",
    "enabled_mode_requires_owner_approval_and_rollback",
    "full_access_never_for_default_automation",
    "worktree_cleanup_requires_retention_decision",
    "risk_fixtures_required",
    "dirty_worktree_requires_decision",
    "stale_heartbeat_requires_stop_or_replan",
):
    if automation_gate.get(key) is not True:
        fail(f"automation worktree quality_gate {key} must be true")
automation_risk_fixtures = automation_worktree.get("risk_fixtures", [])
if len(automation_risk_fixtures) < 4:
    fail("automation worktree risk_fixtures must include at least four cases")
fixture_expected = {fixture.get("expected") for fixture in automation_risk_fixtures}
for expected in ("reject", "needs-fix"):
    if expected not in fixture_expected:
        fail(f"automation worktree risk_fixtures missing expected case: {expected}")
for token in ("stop", "full-access", "dirty", "heartbeat"):
    if not any(token in fixture.get("id", "") or token in fixture.get("input", "") for fixture in automation_risk_fixtures):
        fail(f"automation worktree risk_fixtures missing token: {token}")

improvement_loops = improvement_loop.get("loops", [])
if not improvement_loops:
    fail("agent improvement loops are empty")
improvement_loop_ids = {loop.get("id") for loop in improvement_loops}
if "eval-baseline-first-optimization-v1" not in improvement_loop_ids:
    fail("agent improvement loop missing: eval-baseline-first-optimization-v1")
for loop in improvement_loops:
    lid = loop.get("id")
    require_keys(
        loop,
        [
            "id",
            "owner",
            "applies_to",
            "stages",
            "required_artifacts",
            "promotion_gate",
            "must_not",
        ],
        f"agent improvement loop {lid}",
    )
    if lid == "trace-feedback-eval-handoff-v1":
        for stage in ("collect_sanitized_traces", "generate_eval_suite_candidate", "run_validation_gate", "write_adk_handoff", "human_approve_before_merge"):
            if stage not in loop.get("stages", []):
                fail(f"agent improvement loop {lid} missing stage: {stage}")
        for artifact in ("trace_summary_set", "eval_suite_candidate", "validation_result", "adk_handoff"):
            if artifact not in loop.get("required_artifacts", []):
                fail(f"agent improvement loop {lid} missing artifact: {artifact}")
    if lid == "eval-baseline-first-optimization-v1":
        for stage in ("define_success_metrics", "capture_eval_baseline", "run_representative_eval", "promote_or_rollback"):
            if stage not in loop.get("stages", []):
                fail(f"eval-baseline-first loop missing stage: {stage}")
        for step in ("prompt_tuning", "examples_and_context", "tooling_or_retrieval"):
            if step not in loop.get("improvement_ladder", []):
                fail(f"eval-baseline-first loop missing improvement ladder step: {step}")
        if not any("fine-tuning" in item for item in loop.get("must_not", [])):
            fail("eval-baseline-first loop must block premature fine-tuning")
improvement_gate = improvement_loop.get("quality_gate", {})
require_keys(
    improvement_gate,
    [
        "requires_human_approval_before_apply",
        "requires_validation_gate",
        "requires_adk_handoff_artifact",
        "requires_trace_feedback_linkage",
    ],
    "agent improvement loop quality_gate",
)
for key in (
    "requires_human_approval_before_apply",
    "requires_validation_gate",
    "requires_adk_handoff_artifact",
    "requires_trace_feedback_linkage",
):
    if improvement_gate.get(key) is not True:
        fail(f"agent improvement loop quality_gate {key} must be true")

pr_review_contracts = pr_review.get("contracts", [])
if not pr_review_contracts:
    fail("PR review governance contracts are empty")
pr_review_ids = {contract.get("id") for contract in pr_review_contracts}
for expected in ("adk-ci-pr-review-runner-v1", "untrusted-pr-isolation-v1", "inline-review-anchoring-v1"):
    if expected not in pr_review_ids:
        fail(f"PR review governance contract missing: {expected}")
for contract in pr_review_contracts:
    cid = contract.get("id")
    require_keys(
        contract,
        [
            "id",
            "owner",
            "applies_to",
            "enabled_default",
            "mode",
            "required_inputs",
            "runner_policy",
            "prompt_injection_controls",
            "publishing_policy",
            "must_not",
        ],
        f"PR review governance contract {cid}",
    )
    if contract.get("enabled_default") is not False:
        fail(f"PR review governance contract {cid} must be disabled by default")
    if len(contract.get("required_inputs", [])) < 5:
        fail(f"PR review governance contract {cid} has too few required inputs")
    if not any("prompt" in item.lower() for item in contract.get("prompt_injection_controls", [])):
        fail(f"PR review governance contract {cid} must include prompt injection controls")
    if cid == "adk-ci-pr-review-runner-v1":
        policy = contract.get("runner_policy", {})
        if policy.get("sandbox") != "workspace-write":
            fail("ADK CI PR review runner must default to workspace-write sandbox")
        if "drop-sudo" not in policy.get("safety_strategy", ""):
            fail("ADK CI PR review runner must require drop-sudo or equivalent")
        if not any("structured output" in item.lower() for item in contract.get("publishing_policy", [])):
            fail("ADK CI PR review runner publishing policy must require structured output validation")
    if cid == "untrusted-pr-isolation-v1":
        policy = contract.get("runner_policy", {})
        if "fork pull_request" not in policy.get("untrusted_events", []):
            fail("untrusted PR isolation must include fork pull_request")
        if "no protected LLM provider key exposure" not in policy.get("default_for_untrusted", ""):
            fail("untrusted PR isolation must deny protected LLM provider key exposure")
    if cid == "inline-review-anchoring-v1":
        policy = contract.get("runner_policy", {})
        for case in ("new file", "modified file", "renamed file", "deleted file", "multi-line finding"):
            if case not in policy.get("anchoring_cases_to_test", []):
                fail(f"inline review anchoring missing test case: {case}")
        if not any("right-side diff" in item for item in contract.get("publishing_policy", [])):
            fail("inline review anchoring must require right-side diff validation")
pr_review_gate = pr_review.get("quality_gate", {})
for key in (
    "ci_review_enabled_default_must_be_false",
    "untrusted_pr_must_not_receive_protected_secrets",
    "structured_output_required_for_machine_publishing",
    "inline_comments_require_anchor_validation",
    "ai_review_is_not_human_approval",
):
    if pr_review_gate.get(key) is not True:
        fail(f"PR review quality_gate {key} must be true")

skill_repro_contracts = skill_repro.get("contracts", [])
if not skill_repro_contracts:
    fail("skill reproducibility contracts are empty")
skill_repro_ids = {contract.get("id") for contract in skill_repro_contracts}
for expected in ("skill-discoverability-v1", "skill-version-pin-v1", "skill-tiny-cli-v1", "third-party-skill-domain-policy-v1"):
    if expected not in skill_repro_ids:
        fail(f"skill reproducibility contract missing: {expected}")
for contract in skill_repro_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "required_fields", "must_not"], f"skill reproducibility contract {cid}")
    if len(contract.get("required_fields", [])) < 5:
        fail(f"skill reproducibility contract {cid} has too few required fields")
    if cid == "skill-discoverability-v1":
        examples = contract.get("routing_examples", {})
        if examples.get("positive_required") is not True or examples.get("negative_required") is not True:
            fail("skill discoverability must require positive and negative examples")
    if cid == "skill-version-pin-v1":
        pinning = contract.get("pinning_policy", {})
        if "pin explicit skill version" not in pinning.get("production", ""):
            fail("skill version pin policy must require explicit production version pin")
    if cid == "skill-tiny-cli-v1":
        execution = contract.get("execution_policy", {})
        if "deterministic" not in execution.get("stdout", ""):
            fail("skill tiny CLI policy must require deterministic stdout")
    if cid == "third-party-skill-domain-policy-v1":
        for field in ("trust_level", "review_status", "license", "source_revision", "runtime_boundary", "install_scope", "attribution"):
            if field not in contract.get("required_fields", []):
                fail(f"third-party skill domain policy missing field: {field}")
        trust = contract.get("trust_policy", {})
        if trust.get("default") != "review-required":
            fail("third-party skill domain policy must default to review-required")
skill_repro_gate = skill_repro.get("quality_gate", {})
for key in (
    "negative_examples_required_for_routing_changes",
    "production_skill_version_must_be_pinned",
    "scripted_skills_require_deterministic_cli_contract",
    "networked_skills_require_allowlist_and_egress_policy",
    "third_party_skills_default_review_required",
):
    if skill_repro_gate.get(key) is not True:
        fail(f"skill reproducibility quality_gate {key} must be true")

model_records = model_selection.get("records", [])
if not model_records:
    fail("model selection decision records are empty")
model_record_ids = {record.get("id") for record in model_records}
if "adk-model-selection-record-v1" not in model_record_ids:
    fail("model selection decision record missing: adk-model-selection-record-v1")
for record in model_records:
    rid = record.get("id")
    require_keys(record, ["id", "owner", "applies_to", "required_fields", "quality_gates", "must_not"], f"model selection record {rid}")
    for field in (
        "quality_kpis",
        "service_slos",
        "eval_baseline",
        "version_pinning_strategy",
        "ab_test_plan",
        "rollback_plan",
        "owner_approval",
        "prompt_cache_retention_policy",
        "service_tier_policy",
        "retention_privacy_rationale",
    ):
        if field not in record.get("required_fields", []):
            fail(f"model selection record {rid} missing required field: {field}")
    if not any("retrieved_at" in item or "freshness" in item.lower() or "official model catalog" in item for item in record.get("quality_gates", [])):
        fail(f"model selection record {rid} must require freshness evidence")
    if not any("single informal trial" in item for item in record.get("must_not", [])):
        fail(f"model selection record {rid} must reject single informal trials")
model_gate = model_selection.get("quality_gate", {})
for key in (
    "freshness_required_for_model_catalog",
    "kpi_slo_required_before_promotion",
    "eval_baseline_required_before_change",
    "rollback_required_for_default_change",
    "owner_approval_required",
):
    if model_gate.get(key) is not True:
        fail(f"model selection quality_gate {key} must be true")

data_retention_contracts = data_retention.get("contracts", [])
if not data_retention_contracts:
    fail("data retention contracts are empty")
data_retention_ids = {contract.get("id") for contract in data_retention_contracts}
if "api-state-retention-boundary-v1" not in data_retention_ids:
    fail("data retention contract missing: api-state-retention-boundary-v1")
for contract in data_retention_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "state_classes", "required_fields", "quality_gates", "must_not"], f"data retention contract {cid}")
    state_classes = set(contract.get("state_classes", []))
    for state_class in (
        "persistent_application_state",
        "temporary_background_state",
        "third_party_mcp_state",
        "hosted_container_state",
        "prompt_cache_state",
        "client_retained_encrypted_state",
        "no_retention_store_false",
    ):
        if state_class not in state_classes:
            fail(f"data retention contract {cid} missing state class: {state_class}")
    required_fields = set(contract.get("required_fields", []))
    for field in (
        "store_policy",
        "retention_duration",
        "zdr_behavior",
        "background_mode_policy",
        "third_party_retention_policy",
        "hosted_container_lifecycle",
        "prompt_cache_retention_policy",
    ):
        if field not in required_fields:
            fail(f"data retention contract {cid} missing required field: {field}")
data_retention_gate = data_retention.get("quality_gate", {})
for key in (
    "retention_policy_required",
    "zdr_store_false_required",
    "third_party_mcp_retention_required",
    "hosted_container_lifecycle_required",
    "owner_approval_required_for_persistent_state",
):
    if data_retention_gate.get(key) is not True:
        fail(f"data retention quality_gate {key} must be true")

prompt_cache_contracts = prompt_cache.get("contracts", [])
if not prompt_cache_contracts:
    fail("prompt cache contracts are empty")
prompt_cache_ids = {contract.get("id") for contract in prompt_cache_contracts}
if "prompt-cache-retention-policy-v1" not in prompt_cache_ids:
    fail("prompt cache contract missing: prompt-cache-retention-policy-v1")
for contract in prompt_cache_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "required_fields", "allowed_retention_policies", "quality_gates", "must_not"], f"prompt cache contract {cid}")
    required_fields = set(contract.get("required_fields", []))
    for field in (
        "prompt_cache_key_strategy",
        "stable_prefix_boundary",
        "dynamic_tail_boundary",
        "retention_policy",
        "model_support_source",
        "cached_token_metric",
        "privacy_boundary",
    ):
        if field not in required_fields:
            fail(f"prompt cache contract {cid} missing required field: {field}")
    allowed_policies = set(contract.get("allowed_retention_policies", []))
    for policy in ("in_memory", "24h", "model_default"):
        if policy not in allowed_policies:
            fail(f"prompt cache contract {cid} missing allowed retention policy: {policy}")
    gate_text = " ".join(contract.get("quality_gates", [])).lower()
    for token in ("stable prefix", "dynamic tail", "model support", "freshness"):
        if token not in gate_text:
            fail(f"prompt cache contract {cid} quality gates must mention {token}")
prompt_cache_gate = prompt_cache.get("quality_gate", {})
for key in (
    "stable_dynamic_boundary_required",
    "retention_policy_required",
    "model_support_freshness_required",
    "cache_miss_must_be_behavior_preserving",
    "cached_token_metric_observation_only",
):
    if prompt_cache_gate.get(key) is not True:
        fail(f"prompt cache quality_gate {key} must be true")

surface_terms = codex_surface_terms.get("terms", [])
if not surface_terms:
    fail("Codex surface terms are empty")
surface_terms_by_name = {term.get("official_term"): term for term in surface_terms}
surface_gate = codex_surface_terms.get("quality_gate", {})
require_keys(surface_gate, ["required_terms", "must_not"], "Codex surface terms quality_gate")
for term_name in ("Agent", "Skill", "Plugin", "MCP server", "Automation", "Subagent", "Worktree", "Permission profile"):
    if term_name not in surface_terms_by_name:
        fail(f"Codex surface term missing: {term_name}")
    if term_name not in surface_gate.get("required_terms", []):
        fail(f"Codex surface terms quality_gate missing required term: {term_name}")
for term in surface_terms:
    tid = term.get("official_term")
    require_keys(term, ["official_term", "adk_term", "surface", "definition_boundary", "adk_usage"], f"Codex surface term {tid}")
    if not isinstance(term.get("surface"), list) or not term.get("surface"):
        fail(f"Codex surface term {tid} must define non-empty surface list")
if not any("workflow" in item.lower() and "agent" in item.lower() for item in surface_gate.get("must_not", [])):
    fail("Codex surface terms must forbid calling every workflow an agent")
if not any("plugin" in item.lower() and "installable" in item.lower() for item in surface_gate.get("must_not", [])):
    fail("Codex surface terms must distinguish plugin from non-installable skills")

doc_text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
for marker in ("P0", "P1", "P2", "developers.openai.com", "Non-Goals", "structured outputs", "tool-search", "automation", "CI/PR review", "skill version", "Model selection", "Guardrail", "Stored-session", "Data retention", "Prompt cache retention", "ZDR", "Codex glossary", "permission profile", "memory runtime"):
    if marker not in doc_text:
        fail(f"reference doc missing marker: {marker}")

status = "pass" if not failures else "fail"
if summary_json:
    print(json.dumps({
        "status": status,
        "official_sources": len(sources),
        "eval_suites": len(evals.get("suites", [])),
        "trace_contracts": len(trace_contracts),
        "mcp_dependencies": len(mcp.get("dependencies", [])),
        "slash_audits": len(slash.get("audits", [])),
        "subagent_contracts": len(subagents.get("contracts", [])),
        "runtime_policy_layers": len(runtime_layers),
        "rules_contracts": len(rule_contracts),
        "runtime_api_groups": len(runtime_api_groups),
        "context_state_contracts": len(context_contracts),
        "docs_mcp_tooling_targets": len(docs_tool_targets),
        "sandbox_presets": len(sandbox_presets),
        "hook_events": len(hook_events),
        "adk_runner_contracts": len(adk_runner_contracts),
        "plugin_contracts": len(plugin_contracts),
        "marketplace_contracts": len(marketplace_contracts),
        "structured_output_contracts": len(structured_contracts),
        "tool_search_contracts": len(tool_search_contracts),
        "automation_contracts": len(automation_contracts),
        "worktree_contracts": len(worktree_contracts),
        "agent_improvement_loops": len(improvement_loops),
        "pr_review_contracts": len(pr_review_contracts),
        "skill_reproducibility_contracts": len(skill_repro_contracts),
        "model_selection_records": len(model_records),
        "data_retention_contracts": len(data_retention_contracts),
        "prompt_cache_contracts": len(prompt_cache_contracts),
        "codex_surface_terms": len(surface_terms),
        "failures": len(failures),
    }, ensure_ascii=False, separators=(",", ":")))
elif failures:
    for item in failures:
        print(f"[FAIL] {item}", file=sys.stderr)
else:
    print("[PASS] OpenAI Developers governance")

if failures:
    sys.exit(1)
PY
