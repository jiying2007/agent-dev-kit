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
  - Codex runtime policy and sandbox gates
  - Codex command rule contracts
  - Codex app-server runtime API risk groups
  - context state and session memory contracts
  - OpenAI Docs MCP cross-tool setup contracts
  - hooks runtime audit contracts
  - Codex-as-MCP runner contracts
  - plugin marketplace packaging contracts
  - CI/PR review governance contracts
  - skill reproducibility and version pin contracts
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

official = load_json("manifests/official_docs_freshness_gates.json")
evals = load_json("manifests/eval_suites.json")
trace = load_json("manifests/trace_eval_contracts.json")
mcp = load_json("manifests/skill_mcp_dependencies.json")
slash = load_json("manifests/slash_command_runtime_audits.json")
subagents = load_json("manifests/subagent_contracts.json")
runtime_policy = load_json("manifests/codex_runtime_policy_gates.json")
rules = load_json("manifests/codex_rules_contracts.json")
runtime_api = load_json("manifests/codex_runtime_api_contracts.json")
context_state = load_json("manifests/context_state_contracts.json")
docs_mcp_tooling = load_json("manifests/official_docs_mcp_tooling.json")
hooks = load_json("manifests/hooks_runtime_audits.json")
codex_mcp = load_json("manifests/codex_mcp_runner_contracts.json")
plugins = load_json("manifests/plugin_marketplace_contracts.json")
structured_outputs = load_json("manifests/structured_output_contracts.json")
tool_search = load_json("manifests/tool_search_contracts.json")
automation_worktree = load_json("manifests/automation_worktree_contracts.json")
improvement_loop = load_json("manifests/agent_improvement_loop_contracts.json")
pr_review = load_json("manifests/pr_review_governance_contracts.json")
skill_repro = load_json("manifests/skill_reproducibility_contracts.json")

doc = root / "docs/reference/openai-developers-reference.md"
runbook = root / "docs/runbooks/openai-developers-governance.md"
for rel_path in (doc, runbook):
    if not rel_path.is_file():
        fail(f"missing doc: {rel_path.relative_to(root)}")

today = dt.date.today()
allowed_domains = set(official.get("review_policy", {}).get("allowed_domains", []))
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
    (runtime_policy, "manifests/codex_runtime_policy_gates.json"),
    (rules, "manifests/codex_rules_contracts.json"),
    (runtime_api, "manifests/codex_runtime_api_contracts.json"),
    (context_state, "manifests/context_state_contracts.json"),
    (docs_mcp_tooling, "manifests/official_docs_mcp_tooling.json"),
    (hooks, "manifests/hooks_runtime_audits.json"),
    (codex_mcp, "manifests/codex_mcp_runner_contracts.json"),
    (plugins, "manifests/plugin_marketplace_contracts.json"),
    (structured_outputs, "manifests/structured_output_contracts.json"),
    (tool_search, "manifests/tool_search_contracts.json"),
    (automation_worktree, "manifests/automation_worktree_contracts.json"),
    (improvement_loop, "manifests/agent_improvement_loop_contracts.json"),
    (pr_review, "manifests/pr_review_governance_contracts.json"),
    (skill_repro, "manifests/skill_reproducibility_contracts.json"),
):
    require_source_refs(manifest, rel)

suite_categories = {suite.get("category") for suite in evals.get("suites", [])}
for category in ("routing", "governance", "completion", "macro-eval"):
    if category not in suite_categories:
        fail(f"eval suite category missing: {category}")
for suite in evals.get("suites", []):
    require_keys(suite, ["id", "category", "owner", "goal", "dataset_path", "fixtures", "graders", "minimum_gate"], f"eval suite {suite.get('id')}")

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
if not subagents.get("contracts"):
    fail("subagent contracts are empty")

runtime_layers = runtime_policy.get("policy_layers", [])
if not runtime_layers:
    fail("runtime policy layers are empty")
layer_ids = {layer.get("id") for layer in runtime_layers}
for expected in ("admin-enforced-requirements", "project-config-boundary"):
    if expected not in layer_ids:
        fail(f"runtime policy layer missing: {expected}")
for layer in runtime_layers:
    lid = layer.get("id")
    require_keys(layer, ["id", "owner", "config_file", "precedence", "user_override_allowed", "required_controls", "verification"], f"runtime policy layer {lid}")
    if lid == "admin-enforced-requirements" and layer.get("user_override_allowed") is not False:
        fail("admin-enforced requirements must not allow user override")
    if lid == "project-config-boundary":
        must_not_override = set(layer.get("must_not_override", []))
        for key in ("model_providers", "profile", "otel"):
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

rule_contracts = rules.get("contracts", [])
if not rule_contracts:
    fail("Codex rules contracts are empty")
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
    fail("Codex runtime API method groups are empty")
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
        fail(f"Codex runtime API group missing: {group_id}")
transport_policy = runtime_api.get("transport_policy", {})
require_keys(transport_policy, ["supported", "experimental", "forbidden_defaults", "required_auth_for_remote"], "Codex runtime API transport policy")
if "non-loopback unauthenticated websocket" not in transport_policy.get("forbidden_defaults", []):
    fail("Codex runtime API transport policy must forbid non-loopback unauthenticated websocket")
for group in runtime_api_groups:
    gid = group.get("id")
    require_keys(group, ["id", "owner", "methods", "risk", "classification", "required_evidence", "approval_boundary"], f"Codex runtime API group {gid}")
    classification = group.get("classification", {})
    for key in ("read_only", "destructive", "open_world", "sandbox_inherited"):
        if key not in classification or not isinstance(classification[key], bool):
            fail(f"Codex runtime API group {gid} missing boolean classification.{key}")
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
for contract in context_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "applies_to", "context_classes", "required_fields", "quality_gates", "poisoning_controls", "verification"], f"context state contract {cid}")
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
        for field in ("previous_response_id_policy", "phase_preservation", "prompt_cache_layout"):
            if field not in required_fields:
                fail(f"context state contract {cid} missing field: {field}")

docs_mcp_server = docs_mcp_tooling.get("server", {})
require_keys(docs_mcp_server, ["name", "url", "transport", "purpose"], "OpenAI Docs MCP server")
if docs_mcp_server.get("url") != "https://developers.openai.com/mcp":
    fail("OpenAI Docs MCP server URL must be https://developers.openai.com/mcp")
docs_tool_targets = docs_mcp_tooling.get("tooling_targets", [])
if not docs_tool_targets:
    fail("OpenAI Docs MCP tooling targets are empty")
target_ids = {target.get("id") for target in docs_tool_targets}
for target_id in ("codex", "vscode", "cursor", "claude-code"):
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

codex_contracts = codex_mcp.get("contracts", [])
if not codex_contracts:
    fail("Codex MCP runner contracts are empty")
codex_tools = {contract.get("tool") for contract in codex_contracts}
for tool in ("codex", "codex-reply"):
    if tool not in codex_tools:
        fail(f"Codex MCP runner contract missing tool: {tool}")
for contract in codex_contracts:
    cid = contract.get("id")
    require_keys(contract, ["id", "owner", "tool", "purpose", "required_inputs", "approval_boundary", "sandbox_boundary", "state_output", "must_record", "stop_condition"], f"Codex MCP contract {cid}")
    if contract.get("tool") == "codex-reply" and "threadId" not in contract.get("required_inputs", []):
        fail("codex-reply contract must require threadId")
    for token in ("pass", "replan", "split", "blocked", "abort"):
        if token not in contract.get("stop_condition", ""):
            fail(f"Codex MCP contract {cid} stop_condition missing {token}")

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
    for required_file in (".codex-plugin/plugin.json", "skills/<skill-name>/SKILL.md"):
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
    for required_prompt in ("durable", "stop"):
        if not any(required_prompt in item for item in contract.get("prompt_requirements", [])):
            fail(f"automation contract {cid} prompt_requirements missing {required_prompt}")
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
        "full_access_never_for_default_automation",
        "worktree_cleanup_requires_retention_decision",
    ],
    "automation worktree quality_gate",
)
for key in (
    "automations_enabled_default_must_be_false",
    "first_runs_require_review",
    "full_access_never_for_default_automation",
    "worktree_cleanup_requires_retention_decision",
):
    if automation_gate.get(key) is not True:
        fail(f"automation worktree quality_gate {key} must be true")

improvement_loops = improvement_loop.get("loops", [])
if not improvement_loops:
    fail("agent improvement loops are empty")
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
    for stage in ("collect_sanitized_traces", "generate_eval_suite_candidate", "run_validation_gate", "write_codex_handoff", "human_approve_before_merge"):
        if stage not in loop.get("stages", []):
            fail(f"agent improvement loop {lid} missing stage: {stage}")
    for artifact in ("trace_summary_set", "eval_suite_candidate", "validation_result", "codex_handoff"):
        if artifact not in loop.get("required_artifacts", []):
            fail(f"agent improvement loop {lid} missing artifact: {artifact}")
improvement_gate = improvement_loop.get("quality_gate", {})
require_keys(
    improvement_gate,
    [
        "requires_human_approval_before_apply",
        "requires_validation_gate",
        "requires_codex_handoff_artifact",
        "requires_trace_feedback_linkage",
    ],
    "agent improvement loop quality_gate",
)
for key in (
    "requires_human_approval_before_apply",
    "requires_validation_gate",
    "requires_codex_handoff_artifact",
    "requires_trace_feedback_linkage",
):
    if improvement_gate.get(key) is not True:
        fail(f"agent improvement loop quality_gate {key} must be true")

pr_review_contracts = pr_review.get("contracts", [])
if not pr_review_contracts:
    fail("PR review governance contracts are empty")
pr_review_ids = {contract.get("id") for contract in pr_review_contracts}
for expected in ("codex-ci-pr-review-runner-v1", "untrusted-pr-isolation-v1", "inline-review-anchoring-v1"):
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
    if cid == "codex-ci-pr-review-runner-v1":
        policy = contract.get("runner_policy", {})
        if policy.get("sandbox") != "workspace-write":
            fail("Codex CI PR review runner must default to workspace-write sandbox")
        if "drop-sudo" not in policy.get("safety_strategy", ""):
            fail("Codex CI PR review runner must require drop-sudo or equivalent")
        if not any("structured output" in item.lower() for item in contract.get("publishing_policy", [])):
            fail("Codex CI PR review runner publishing policy must require structured output validation")
    if cid == "untrusted-pr-isolation-v1":
        policy = contract.get("runner_policy", {})
        if "fork pull_request" not in policy.get("untrusted_events", []):
            fail("untrusted PR isolation must include fork pull_request")
        if "no protected OpenAI key exposure" not in policy.get("default_for_untrusted", ""):
            fail("untrusted PR isolation must deny protected OpenAI key exposure")
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
for expected in ("skill-discoverability-v1", "skill-version-pin-v1", "skill-tiny-cli-v1"):
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
skill_repro_gate = skill_repro.get("quality_gate", {})
for key in (
    "negative_examples_required_for_routing_changes",
    "production_skill_version_must_be_pinned",
    "scripted_skills_require_deterministic_cli_contract",
    "networked_skills_require_allowlist_and_egress_policy",
):
    if skill_repro_gate.get(key) is not True:
        fail(f"skill reproducibility quality_gate {key} must be true")

doc_text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
for marker in ("P0", "P1", "P2", "developers.openai.com", "Non-Goals", "structured outputs", "tool-search", "automation", "CI/PR review", "skill version"):
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
        "codex_mcp_contracts": len(codex_contracts),
        "plugin_contracts": len(plugin_contracts),
        "marketplace_contracts": len(marketplace_contracts),
        "structured_output_contracts": len(structured_contracts),
        "tool_search_contracts": len(tool_search_contracts),
        "automation_contracts": len(automation_contracts),
        "worktree_contracts": len(worktree_contracts),
        "agent_improvement_loops": len(improvement_loops),
        "pr_review_contracts": len(pr_review_contracts),
        "skill_reproducibility_contracts": len(skill_repro_contracts),
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
