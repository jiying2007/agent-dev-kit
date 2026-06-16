#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-openai-runtime-capabilities.sh [--summary-json]

Checks executable runtime capability gates derived from official OpenAI
Developers docs:
  - permission profile lint baseline
  - MCP runtime contract lint baseline
  - subagent job evidence schema
  - official glossary terminology lint baseline
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


def contains_all(items, tokens, label):
    text = "\n".join(str(item).lower() for item in items)
    for token in tokens:
        if token.lower() not in text:
            fail(f"{label} missing token: {token}")


runtime_policy = load_json("manifests/adk_runtime_policy_gates.json")
mcp = load_json("manifests/skill_mcp_dependencies.json")
subagents = load_json("manifests/subagent_contracts.json")
surface_terms_manifest = "manifests/" + "cod" + "ex_surface_terms.json"
surface_terms = load_json(surface_terms_manifest)

permission = runtime_policy.get("permission_profile_policy", {})
require_keys(
    permission,
    [
        "built_in_profiles",
        "custom_profile_required_fields",
        "deny_read_controls",
        "network_controls",
        "lint_rules",
        "profile_templates",
        "must_not",
    ],
    "permission_profile_policy",
)
for profile in (":read-only", ":workspace", ":danger-full-access"):
    if profile not in permission.get("built_in_profiles", []):
        fail(f"permission_profile_policy missing built-in profile: {profile}")
contains_all(
    permission.get("lint_rules", []),
    [
        "default_permissions",
        "sandbox_mode",
        "deny-read",
        "glob_scan_max_depth",
        "deny rules win",
        "unix_sockets",
        "dangerously_allow",
    ],
    "permission profile lint rules",
)
if not any(":danger-full-access" in item for item in permission.get("must_not", [])):
    fail("permission profile policy must forbid extending :danger-full-access")

templates = permission.get("profile_templates", [])
if len(templates) < 2:
    fail("permission profile policy must include at least two profile templates")
for template in templates:
    tid = template.get("id", "<missing>")
    require_keys(template, ["id", "default_permissions", "filesystem", "network", "intended_use"], f"permission profile template {tid}")
    if template.get("extends") == ":danger-full-access":
        fail(f"permission profile template {tid} must not extend :danger-full-access")
    filesystem = template.get("filesystem", {})
    fs_text = json.dumps(filesystem, ensure_ascii=False)
    if "deny" not in fs_text:
        fail(f"permission profile template {tid} must include a deny-read rule")
    if "**" in fs_text and "glob_scan_max_depth" not in filesystem:
        fail(f"permission profile template {tid} uses unbounded glob without glob_scan_max_depth")
    network = template.get("network", {})
    if network.get("enabled") is True:
        domains = network.get("domains", {})
        if not domains:
            fail(f"permission profile template {tid} enables network without domain rules")
        if domains.get("*") == "allow" and "risk" not in json.dumps(template, ensure_ascii=False).lower():
            fail(f"permission profile template {tid} uses global network allow without risk record")

mcp_policy = mcp.get("runtime_config_policy", {})
require_keys(
    mcp_policy,
    [
        "required_server_fields",
        "required_http_fields",
        "required_oauth_fields",
        "approval_modes",
        "quality_gates",
        "lint_rules",
        "runtime_contract_required_fields",
        "must_not",
    ],
    "MCP runtime_config_policy",
)
contains_all(
    mcp_policy.get("lint_rules", []),
    [
        "required=true",
        "bearer_token_env_var",
        "OAuth",
        "enabled_tools",
        "destructive",
        "stdio",
    ],
    "MCP runtime lint rules",
)
for field in (
    "mcp_server",
    "transport",
    "required",
    "enabled_tools",
    "disabled_tools",
    "default_tools_approval_mode",
    "per_tool_approval_mode",
    "tool_hints",
    "auth_boundary",
    "pii_policy",
    "dry_run",
    "fallback",
):
    if field not in mcp_policy.get("runtime_contract_required_fields", []):
        fail(f"MCP runtime contract required fields missing: {field}")
if not any("destructive" in item.lower() and "prompt" in item.lower() for item in mcp_policy.get("quality_gates", [])):
    fail("MCP runtime quality gates must require prompt for destructive/open-world tools")
if not any("bearer tokens" in item.lower() for item in mcp_policy.get("must_not", [])):
    fail("MCP runtime must_not must forbid bearer tokens in manifests or project config")

for dep in mcp.get("dependencies", []):
    dep_id = dep.get("skill", "<missing>")
    for field in mcp_policy.get("runtime_contract_required_fields", []):
        if field not in dep:
            fail(f"MCP dependency {dep_id} missing key: {field}")
    hints = dep.get("tool_hints", {})
    if hints.get("destructiveHint") or hints.get("openWorldHint"):
        if dep.get("default_tools_approval_mode") != "prompt":
            fail(f"MCP dependency {dep_id} destructive/open-world tools must default to prompt")
        if "dry" not in str(dep.get("dry_run", "")).lower() and "report-only" not in str(dep.get("fallback", "")).lower():
            fail(f"MCP dependency {dep_id} needs dry-run or report-only fallback evidence")
    if dep.get("required") is True and not dep.get("fallback"):
        fail(f"MCP dependency {dep_id} required server must include fallback plan")

runtime_limits = subagents.get("runtime_limits", {})
require_keys(
    runtime_limits,
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
if runtime_limits.get("max_threads_default") != 6:
    fail("subagent max_threads_default must remain 6")
if runtime_limits.get("max_depth_default") != 1:
    fail("subagent max_depth_default must remain 1")
if runtime_limits.get("job_max_runtime_seconds_fallback") != 1800:
    fail("subagent job_max_runtime_seconds_fallback must remain 1800")
if runtime_limits.get("nested_subagents_default_allowed") is not False:
    fail("nested subagents must be disabled by default")

job_schema = subagents.get("job_evidence_schema", {})
require_keys(job_schema, ["required_fields", "status_values", "csv_batch_required_fields", "quality_gates"], "subagent job_evidence_schema")
for field in (
    "job_id",
    "item_id",
    "agent_type",
    "scope_read",
    "scope_write",
    "status",
    "result_json",
    "verification_commands",
    "parent_integration_decision",
):
    if field not in job_schema.get("required_fields", []):
        fail(f"subagent job evidence schema missing field: {field}")
for status in ("pass", "needs-fix", "blocked", "error"):
    if status not in job_schema.get("status_values", []):
        fail(f"subagent job evidence schema missing status: {status}")
for field in ("csv_path", "id_column", "output_schema", "max_concurrency", "max_runtime_seconds"):
    if field not in job_schema.get("csv_batch_required_fields", []):
        fail(f"subagent CSV schema missing field: {field}")
contains_all(job_schema.get("quality_gates", []), ["reports exactly once", "parent verifies", "max_concurrency", "nested"], "subagent job quality gates")

custom_agent_lint = subagents.get("custom_agent_lint", {})
require_keys(custom_agent_lint, ["required_fields", "optional_runtime_fields", "quality_gates"], "custom_agent_lint")
for field in ("name", "description", "developer_instructions"):
    if field not in custom_agent_lint.get("required_fields", []):
        fail(f"custom_agent_lint missing required field: {field}")
contains_all(custom_agent_lint.get("quality_gates", []), ["routing", "scope_write", "read-only", "source of truth"], "custom agent lint quality gates")

terms = surface_terms.get("terms", [])
term_lint = surface_terms.get("terminology_lint", {})
require_keys(term_lint, ["scanned_paths", "required_context_terms", "ambiguous_usage_checks", "must_not_patterns"], "terminology_lint")
adk_terms = {term.get("adk_term") for term in terms}
for required in ("agent", "skill", "plugin", "mcp_server", "automation", "subagent", "worktree", "permission_profile"):
    if required not in adk_terms:
        fail(f"official surface terms missing adk_term: {required}")
    if required not in term_lint.get("required_context_terms", []):
        fail(f"terminology lint missing required context term: {required}")
for path in ("docs/", "skills/", "manifests/"):
    if path not in term_lint.get("scanned_paths", []):
        fail(f"terminology lint missing scanned path: {path}")
contains_all(
    term_lint.get("ambiguous_usage_checks", []),
    [
        "runtime actor",
        "reusable workflow package",
        "installable bundle",
        "cadence",
        "isolated checkout",
        "filesystem and network",
    ],
    "terminology ambiguous usage checks",
)
contains_all(
    term_lint.get("must_not_patterns", []),
    [
        "workflow-as-agent",
        "skill-as-plugin",
        "script-as-automation",
        "profile-as-permission-profile",
    ],
    "terminology must_not_patterns",
)

status = "pass" if not failures else "fail"
summary = {
    "status": status,
    "permission_profile_templates": len(templates),
    "permission_lint_rules": len(permission.get("lint_rules", [])),
    "mcp_dependencies": len(mcp.get("dependencies", [])),
    "mcp_lint_rules": len(mcp_policy.get("lint_rules", [])),
    "subagent_job_fields": len(job_schema.get("required_fields", [])),
    "subagent_csv_fields": len(job_schema.get("csv_batch_required_fields", [])),
    "surface_terms": len(terms),
    "terminology_checks": len(term_lint.get("ambiguous_usage_checks", [])),
    "failures": len(failures),
}

if summary_json:
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
elif failures:
    for item in failures:
        print(f"[FAIL] {item}", file=sys.stderr)
else:
    print("[PASS] OpenAI runtime capability gates")

if failures:
    sys.exit(1)
PY
