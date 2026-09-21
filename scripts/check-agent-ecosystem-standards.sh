#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-agent-ecosystem-standards.sh [--summary-json]

Checks method-only Agent ecosystem contracts across existing ADK SSOT manifests:
  - Agent Skills portable format
  - OWASP Agentic Top 10 ASI01-ASI10 coverage
  - OWASP Agentic Skills Top 10 AST01-AST10 evolving crosswalk
  - skill maintenance evidence and coding-agent target watch boundaries
  - read-only agent -> validated safe output -> separate write executor
  - MCP dependency provenance and 2026 protocol compatibility staging
  - upstream-revision-pinned OpenTelemetry GenAI adapter with content capture disabled
  - ACP and A2A watch-only boundaries
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
import json
import re
import sys
from datetime import date
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
summary_json = sys.argv[2] == "1"
failures = []
checked = 0
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")


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


def load_json(relative_path):
    path = root / relative_path
    check(path.is_file(), f"missing file: {relative_path}")
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json {relative_path}: {exc}")
        return {}


external = load_json("manifests/external_agent_pattern_contracts.json")
skill = load_json("manifests/skill_reproducibility_contracts.json")
runtime = load_json("manifests/adk_runtime_policy_gates.json")
automation = load_json("manifests/automation_worktree_contracts.json")
mcp = load_json("manifests/skill_mcp_dependencies.json")
trace = load_json("manifests/trace_eval_contracts.json")

expected_sources = {
    "agent-skills-open-format": "adopt-method-only",
    "owasp-agentic-top10-2026": "adopt-method-only",
    "github-gh-aw-safe-outputs": "adopt-method-only",
    "mcp-registry": "adopt-method-only",
    "otel-genai-semconv": "adopt-method-only",
    "agent-client-protocol": "observe-method-only",
    "a2a-protocol-1-0": "observe-method-only",
    "mcp-2026-07-28-final": "enhance-metadata-only",
    "owasp-agentic-skills-top10-2026": "observe-method-only",
    "agent-skills-in-the-wild-2026": "adopt-method-only",
    "vscode-agent-skills-2026": "observe-method-only",
}
source_by_id = {
    item.get("id"): item
    for item in external.get("source_refs", [])
    if isinstance(item, dict)
}
source_fields = [
    "id",
    "title",
    "url",
    "retrieved_at",
    "review_status",
    "expires_at",
    "license",
    "evidence_strength",
    "decision",
    "notes",
]
for source_id, decision in expected_sources.items():
    check(source_id in source_by_id, f"missing ecosystem source_ref: {source_id}")
    source = source_by_id.get(source_id, {})
    require_keys(source, source_fields, f"source_ref {source_id}")
    parsed = urlparse(source.get("url", ""))
    check(parsed.scheme == "https" and bool(parsed.netloc), f"source_ref {source_id} must use a valid https URL")
    check(source.get("decision") == decision, f"source_ref {source_id} decision must be {decision}")
    check(source.get("evidence_strength") in {"medium", "high"}, f"source_ref {source_id} has invalid evidence_strength")
    try:
        retrieved_at = date.fromisoformat(source.get("retrieved_at", ""))
        expires_at = date.fromisoformat(source.get("expires_at", ""))
    except ValueError:
        fail(f"source_ref {source_id} has invalid freshness date")
    else:
        check(expires_at > retrieved_at, f"source_ref {source_id} expires_at must be after retrieved_at")
        check(expires_at >= date.today(), f"source_ref {source_id} review is expired")

expected_candidates = {
    "agent-skills-portable-format-check": "agent-skills-open-format",
    "owasp-agentic-security-crosswalk": "owasp-agentic-top10-2026",
    "safe-output-executor-separation": "github-gh-aw-safe-outputs",
    "mcp-registry-provenance-fields": "mcp-registry",
    "otel-genai-trace-adapter": "otel-genai-semconv",
    "acp-protocol-watch": "agent-client-protocol",
    "a2a-protocol-watch": "a2a-protocol-1-0",
    "mcp-2026-compat-staging": "mcp-2026-07-28-final",
    "agentic-skills-security-crosswalk": "owasp-agentic-skills-top10-2026",
    "skill-maintenance-evidence": "agent-skills-in-the-wild-2026",
    "vscode-github-copilot-target-watch": "vscode-agent-skills-2026",
}
candidate_by_id = {
    item.get("id"): item
    for item in external.get("candidate_decisions", [])
    if isinstance(item, dict)
}
for candidate_id, source_id in expected_candidates.items():
    check(candidate_id in candidate_by_id, f"missing ecosystem candidate: {candidate_id}")
    candidate = candidate_by_id.get(candidate_id, {})
    check(candidate.get("source_ref") == source_id, f"candidate {candidate_id} source_ref must be {source_id}")
    check(candidate.get("runtime_enabled") is False, f"candidate {candidate_id} must keep runtime_enabled=false")
    check(candidate.get("install_scope") == "none-method-only", f"candidate {candidate_id} must remain method-only")

domain_refs = {
    "skill_reproducibility_contracts": (skill, "agent-skills-open-format"),
    "adk_runtime_policy_gates": (runtime, "owasp-agentic-top10-2026"),
    "automation_worktree_contracts": (automation, "github-gh-aw-safe-outputs"),
    "skill_mcp_dependencies": (mcp, "mcp-registry"),
    "trace_eval_contracts": (trace, "otel-genai-semconv"),
}
for label, (manifest, source_id) in domain_refs.items():
    check(source_id in manifest.get("external_source_refs", []), f"{label} missing external source_ref: {source_id}")
for source_id in ("owasp-agentic-skills-top10-2026", "agent-skills-in-the-wild-2026"):
    check(source_id in skill.get("external_source_refs", []), f"skill_reproducibility_contracts missing external source_ref: {source_id}")
check("mcp-2026-07-28-final" in mcp.get("external_source_refs", []), "skill_mcp_dependencies missing MCP 2026 final source_ref")

skill_contracts = {
    item.get("id"): item
    for item in skill.get("contracts", [])
    if isinstance(item, dict)
}
portable = skill_contracts.get("agent-skills-portable-format-v1", {})
check(bool(portable), "missing contract: agent-skills-portable-format-v1")
portable_fields = {
    "skill_directory",
    "skill_md",
    "name",
    "description",
    "support_files_policy",
    "progressive_disclosure",
    "target_profile",
    "conformance_fixture",
    "runtime_smoke_status",
}
check(portable_fields <= set(portable.get("required_fields", [])), "portable skill contract missing required fields")
directory_contract = portable.get("directory_contract", {})
check(directory_contract.get("entrypoint") == "SKILL.md", "portable skill entrypoint must be SKILL.md")
check(set(directory_contract.get("required_frontmatter", [])) == {"name", "description"}, "portable skill frontmatter must require name and description")
field_constraints = portable.get("field_constraints", {})
check("matches parent directory" in field_constraints.get("name", ""), "portable skill name must match its parent directory")
check("1-1024" in field_constraints.get("description", ""), "portable skill description constraint must be bounded")
check(skill.get("quality_gate", {}).get("agent_skills_portable_format_required") is True, "portable skill quality gate must be true")

skill_taxonomy = skill.get("agentic_skill_security_taxonomy", {})
check(skill_taxonomy.get("id") == "owasp-agentic-skills-top10-2026-crosswalk-v1", "missing Agentic Skills Top 10 crosswalk")
skill_threats = skill_taxonomy.get("threats", [])
expected_ast = [f"AST{index:02d}" for index in range(1, 11)]
skill_threat_ids = [item.get("id") for item in skill_threats if isinstance(item, dict)]
check(skill_threat_ids == expected_ast, "Agentic Skills crosswalk must contain AST01-AST10 exactly once in order")
for threat in skill_threats:
    if not isinstance(threat, dict):
        fail("Agentic Skills crosswalk threat must be an object")
        continue
    threat_id = threat.get("id", "<missing-id>")
    require_keys(
        threat,
        ["id", "name", "local_surfaces", "preventive_controls", "evidence_required", "residual_risk"],
        f"skill threat {threat_id}",
    )
check("not an OWASP certification" in skill_taxonomy.get("coverage_policy", ""), "Agentic Skills crosswalk must reject certification claims")

maintenance = skill_contracts.get("skill-maintenance-evidence-v1", {})
check(bool(maintenance), "missing contract: skill-maintenance-evidence-v1")
maintenance_fields = {
    "skill_id",
    "upstream_revision",
    "content_digest",
    "stable_behavior_diff",
    "target_local_binding_diff",
    "use_evidence",
    "effect_evidence",
    "last_verified_at",
    "refresh_due_at",
    "retire_due_at",
    "rollback_path",
}
check(maintenance_fields <= set(maintenance.get("required_fields", [])), "skill maintenance contract missing required fields")
check(maintenance.get("unknown_effect_policy") == "explicit-not-measured", "skill maintenance unknown effect policy must be explicit")
check(skill.get("quality_gate", {}).get("agentic_skill_security_crosswalk_required") is True, "skill security crosswalk gate must be true")
check(skill.get("quality_gate", {}).get("skill_maintenance_evidence_required_for_external_promotion") is True, "skill maintenance promotion gate must be true")

taxonomy = runtime.get("agentic_security_taxonomy", {})
check(taxonomy.get("id") == "owasp-agentic-top10-2026-crosswalk-v1", "missing OWASP Agentic Top 10 crosswalk")
threats = taxonomy.get("threats", [])
expected_asi = [f"ASI{index:02d}" for index in range(1, 11)]
threat_ids = [item.get("id") for item in threats if isinstance(item, dict)]
check(threat_ids == expected_asi, "OWASP crosswalk must contain ASI01-ASI10 exactly once in order")
for threat in threats:
    if not isinstance(threat, dict):
        fail("OWASP crosswalk threat must be an object")
        continue
    threat_id = threat.get("id", "<missing-id>")
    require_keys(threat, ["id", "name", "local_surfaces", "preventive_controls", "evidence_required", "residual_risk"], f"threat {threat_id}")
check(any("not a security certification" in item for item in [taxonomy.get("coverage_policy", "")]), "OWASP crosswalk must reject certification claims")

safe_output = automation.get("safe_output_contract", {})
check(safe_output.get("id") == "read-only-agent-safe-output-executor-v1", "missing safe-output executor separation contract")
check(safe_output.get("agent_phase", {}).get("permissions") == "read-only", "safe-output agent phase must be read-only")
check(safe_output.get("agent_phase", {}).get("direct_write_allowed") is False, "safe-output agent must not write directly")
check(safe_output.get("validation_phase", {}).get("required") is True, "safe-output validation must be required")
check(safe_output.get("executor_phase", {}).get("separate_identity_or_job") is True, "safe-output write executor must be separate")
for control in ("kill switch", "bounded operation count", "bounded payload size", "audit record", "rollback or compensating action"):
    check(control in safe_output.get("safety_controls", []), f"safe-output missing safety control: {control}")
for gate in ("safe_output_executor_separation_required", "safe_output_schema_validation_required", "safe_output_operation_caps_required", "safe_output_kill_switch_required"):
    check(automation.get("quality_gate", {}).get(gate) is True, f"automation quality_gate {gate} must be true")

provenance_policy = mcp.get("external_dependency_provenance_policy", {})
check(provenance_policy.get("id") == "mcp-dependency-provenance-v1", "missing MCP provenance policy")
provenance_fields = {
    "source_url",
    "registry_namespace",
    "namespace_verification",
    "package_version",
    "artifact_digest",
    "retrieved_at",
    "review_status",
    "expires_at",
    "trust_decision",
}
check(provenance_fields <= set(provenance_policy.get("required_fields", [])), "MCP provenance policy missing required fields")
check(provenance_policy.get("trust_model", {}).get("registry_listing") == "discovery metadata only", "MCP registry listing must not be trust certification")
for dependency in mcp.get("dependencies", []):
    label = f"MCP dependency {dependency.get('mcp_server', '<missing-id>')} provenance"
    require_keys(dependency.get("provenance", {}), sorted(provenance_fields), label)

compatibility = mcp.get("protocol_compatibility_policy", {})
check(compatibility.get("id") == "mcp-protocol-compatibility-staging-v1", "missing MCP protocol compatibility staging policy")
check(compatibility.get("active_protocol_version") == "2026-07-28", "MCP active protocol version must be 2026-07-28")
check(
    compatibility.get("active_status") == "supported-current-governance-only",
    "MCP active status must remain governance-only",
)
check(
    compatibility.get("active_scope") == "protocol-governance-contract-only",
    "MCP active scope must remain protocol-governance-contract-only",
)
check(compatibility.get("active_runtime_enabled") is False, "MCP active runtime must remain disabled")
check(
    compatibility.get("active_feature_enablement")
    == {"tasks": False, "apps": False, "extensions": False},
    "MCP active feature enablement must remain disabled",
)
check("no-token-passthrough" in compatibility.get("active_auth_profile", ""), "MCP active auth profile must forbid token passthrough")
mcp_candidate_fields = {
    "protocol_version",
    "source_ref",
    "release_status",
    "capabilities",
    "feature_enablement",
    "extension_ids",
    "deprecated_features",
    "auth_profile",
    "compatibility_test",
    "compatibility_scope",
    "compatibility_evidence",
    "rollback",
    "runtime_enabled",
    "final_compatibility_claim",
}
check(mcp_candidate_fields <= set(compatibility.get("candidate_required_fields", [])), "MCP candidate required fields are incomplete")
mcp_candidates = compatibility.get("candidates", [])
check(len(mcp_candidates) == 1, "MCP compatibility staging must contain exactly one final release candidate")
if mcp_candidates:
    candidate = mcp_candidates[0]
    require_keys(candidate, sorted(mcp_candidate_fields.difference({"extension_ids"})), "MCP compatibility candidate")
    check(candidate.get("protocol_version") == "2026-07-28", "MCP candidate protocol version is invalid")
    check(candidate.get("source_ref") == "mcp-2026-07-28-final", "MCP candidate must reference final release provenance")
    check(candidate.get("release_status") == "released", "MCP candidate must record the released final metadata")
    feature_enablement = candidate.get("feature_enablement", {})
    for feature in ("tasks", "apps", "extensions"):
        check(feature_enablement.get(feature) is False, f"MCP candidate feature must remain disabled: {feature}")
    check(candidate.get("extension_ids") == [], "MCP candidate extensions must remain empty")
    check(candidate.get("runtime_enabled") is False, "MCP candidate runtime must remain disabled")
    check(candidate.get("final_compatibility_claim") is True, "MCP candidate must record the scoped final compatibility evidence")
    check(candidate.get("compatibility_test") == "pass-mcp-2026-activation-fixture-2026-07-31", "MCP candidate compatibility test identity is invalid")
    check(
        candidate.get("compatibility_scope")
        == "go-sdk-v1.7.0-pre.3-json-schema-2020-12-stateless-streamable-http-auth-boundary-and-legacy-rollback-on-offline-loopback",
        "MCP candidate compatibility scope is invalid",
    )
    compatibility_evidence = candidate.get("compatibility_evidence", {})
    require_keys(
        compatibility_evidence,
        [
            "sdk_module",
            "sdk_version",
            "sdk_revision",
            "sdk_sum",
            "sdk_go_mod_sum",
            "runtime_image",
            "transport",
            "network_mode",
            "test_names",
            "negative_boundaries",
            "verified_at",
            "evidence_path",
        ],
        "MCP compatibility evidence",
    )
    check(compatibility_evidence.get("sdk_module") == "github.com/modelcontextprotocol/go-sdk", "MCP SDK module is not pinned")
    check(compatibility_evidence.get("sdk_version") == "v1.7.0-pre.3", "MCP SDK version is not pinned")
    check(compatibility_evidence.get("sdk_revision") == "827f90ba0c13edb546028df42fadc9f1211a4ff2", "MCP SDK revision is not pinned")
    check(compatibility_evidence.get("sdk_sum") == "h1:SEAY9IduDif4iApnZgpFkjFIdo3askSGZVbZIYyTy6I=", "MCP SDK sum is invalid")
    check(
        compatibility_evidence.get("runtime_image")
        == "docker.io/library/golang:1.25.1-bookworm@sha256:c423747fbd96fd8f0b1102d947f51f9b266060217478e5f9bf86f145969562ee",
        "MCP activation runtime image is not digest-pinned",
    )
    check(compatibility_evidence.get("transport") == "streamable-http-local-loopback", "MCP activation transport scope is invalid")
    check(compatibility_evidence.get("network_mode") == "offline-container-loopback-only", "MCP activation smoke must be offline")
    check(
        compatibility_evidence.get("test_names")
        == [
            "TestSchemaCompatibilityFixture",
            "TestVersionPinnedClientServerSmoke",
            "TestAuthBoundaryVerification",
            "TestRollbackSmoke",
        ],
        "MCP activation test identity is incomplete",
    )
    check(candidate.get("auth_profile") == compatibility.get("active_auth_profile"), "MCP candidate auth profile must not weaken the active profile")
activation = compatibility.get("activation_gate", {})
check(activation.get("final_spec_retrieved") is True, "MCP final release metadata must be recorded as retrieved")
check(activation.get("extensions_enabled_default") is False, "MCP extensions must remain disabled by default")
for gate in (
    "breaking_change_diff_required",
    "schema_fixture_required",
    "client_server_smoke_required",
    "auth_security_review_required",
    "rollback_smoke_required",
):
    check(activation.get(gate) is True, f"MCP activation gate is missing: {gate}")
check(activation.get("breaking_change_diff_completed") is True, "MCP breaking-change diff must be completed")
for gate in (
    "schema_fixture_completed",
    "client_server_smoke_completed",
    "auth_security_review_completed",
    "rollback_smoke_completed",
):
    check(activation.get(gate) is True, f"MCP activation evidence must be completed: {gate}")
check(activation.get("technical_readiness_completed") is True, "MCP technical readiness must be completed")
check(activation.get("owner_decision_required") is True, "MCP activation must require an independent owner decision")
check(
    activation.get("owner_decision_schema") == "schemas/mcp-protocol-activation-decision.schema.json",
    "MCP owner decision schema path is invalid",
)
check(
    activation.get("owner_decision_schema_version") == "mcp-protocol-activation-decision/v1",
    "MCP owner decision schema version is invalid",
)
check(
    activation.get("owner_decision_allowed") == ["ACTIVATE", "HOLD", "REJECT"],
    "MCP owner decision enum is invalid",
)
check(activation.get("owner_decision_completed") is True, "MCP owner activation decision must be completed")
check(
    activation.get("owner_decision_id") == "mcp-act-2026-07-31-leiwenjun",
    "MCP owner activation decision id is invalid",
)
check(
    activation.get("owner_decision_path")
    == "docs/changes/mcp-2026-activation-readiness-2026-07-31/owner-activation-decision.json",
    "MCP owner activation decision path is invalid",
)
check(activation.get("activation_allowed") is True, "MCP governance-contract activation must be allowed")
check(activation.get("activation_completed") is True, "MCP governance-contract activation must be completed")
check(
    activation.get("activation_scope") == "protocol-governance-contract-only",
    "MCP activation scope must remain governance-only",
)
check(activation.get("activated_at") == "2026-07-31", "MCP activation date is invalid")
check(
    activation.get("rollback_target_protocol_version") == "2025-11-25",
    "MCP rollback target must remain 2025-11-25",
)

activation_decision_schema = load_json("schemas/mcp-protocol-activation-decision.schema.json")
check(
    activation_decision_schema.get("$id") == "mcp-protocol-activation-decision/v1",
    "MCP activation decision schema id is invalid",
)
check(
    activation_decision_schema.get("properties", {}).get("decision", {}).get("enum")
    == ["ACTIVATE", "HOLD", "REJECT"],
    "MCP activation decision schema enum is invalid",
)
check(
    activation_decision_schema.get("properties", {}).get("runtime_enabled", {}).get("const") is False,
    "MCP protocol activation decision must not authorize runtime enablement",
)
try:
    Draft202012Validator.check_schema(activation_decision_schema)
except SchemaError as exc:
    fail(f"MCP activation decision schema is invalid: {exc.message}")
else:
    activation_decision = load_json(activation.get("owner_decision_path", ""))
    decision_errors = sorted(
        Draft202012Validator(
            activation_decision_schema,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        ).iter_errors(activation_decision),
        key=lambda item: list(item.absolute_path),
    )
    check(
        not decision_errors,
        "MCP activation decision record does not satisfy its schema"
        + (f": {decision_errors[0].message}" if decision_errors else ""),
    )
    check(activation_decision.get("decision_id") == activation.get("owner_decision_id"), "MCP decision id mismatch")
    check(activation_decision.get("candidate_id") == "epc-c6f947d482aa8aa0c78f", "MCP decision candidate id mismatch")
    check(activation_decision.get("decision") == "ACTIVATE", "MCP owner decision must be ACTIVATE")
    check(activation_decision.get("owner") == "leiwenjun", "MCP activation owner is invalid")
    check(
        activation_decision.get("scope") == compatibility.get("active_scope"),
        "MCP decision scope must match the active scope",
    )
    check(activation_decision.get("runtime_enabled") is False, "MCP decision must keep runtime disabled")
    check(
        activation_decision.get("feature_enablement") == compatibility.get("active_feature_enablement"),
        "MCP decision must keep active features disabled",
    )

adapters = {
    item.get("id"): item
    for item in trace.get("interoperability_adapters", [])
    if isinstance(item, dict)
}
otel = adapters.get("otel-genai-trace-summary-v1", {})
check(bool(otel), "missing OTel GenAI trace adapter")
check(otel.get("enabled_default") is False, "OTel GenAI adapter must be disabled by default")
check(
    otel.get("upstream_repository") == "https://github.com/open-telemetry/semantic-conventions-genai",
    "OTel GenAI adapter upstream repository must be canonical",
)
check(
    otel.get("upstream_revision") == "cc07f722069974139dab497d80d145144b19daca",
    "OTel GenAI adapter upstream revision must match the reviewed snapshot",
)
check(otel.get("schema_url_status") == "unavailable-upstream-todo", "OTel GenAI schema URL must remain explicitly unavailable")
check("schema_url" not in otel, "OTel GenAI adapter must not invent an upstream Schema URL")
check("schema_version" not in otel, "OTel GenAI adapter must not invent an upstream schema version")
content_capture = otel.get("content_capture", {})
check(content_capture.get("enabled_default") is False, "OTel GenAI content capture must be disabled by default")
check(content_capture.get("allow_opt_in") is False, "OTel GenAI content capture opt-in must remain disabled")
sensitive_fields = {
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "gen_ai.system_instructions",
    "gen_ai.tool.call.arguments",
    "gen_ai.tool.call.result",
}
check(sensitive_fields <= set(content_capture.get("deny_fields", [])), "OTel GenAI adapter deny list is incomplete")
check("no hosted exporter" in otel.get("export_boundary", ""), "OTel GenAI adapter must not enable hosted export")
check("prompt_version" in otel.get("native_only_fields", []), "OTel GenAI adapter must preserve unmapped prompt_version natively")

external_contracts = {
    item.get("id"): item
    for item in external.get("contracts", [])
    if isinstance(item, dict)
}
watch = external_contracts.get("agent-interoperability-watch-v1", {})
check(bool(watch), "missing ACP/A2A watch-only contract")
check(set(watch.get("source_refs", [])) == {"agent-client-protocol", "a2a-protocol-1-0"}, "watch contract must reference ACP and A2A")
check(external.get("quality_gate", {}).get("watch_protocols_must_not_enable_runtime") is True, "watch-only runtime gate must be true")

target_watch = external_contracts.get("coding-agent-target-watch-v1", {})
check(bool(target_watch), "missing coding-agent target watch contract")
check(target_watch.get("runtime_enabled") is False, "coding-agent target watch runtime must remain disabled")
check(target_watch.get("direct_target_added") is False, "coding-agent target watch must not add a direct target")
target_watch_fields = {
    "target_id",
    "runtime_enabled",
    "direct_target_added",
    "use_case",
    "runtime_version",
    "skill_discovery_paths",
    "export_smoke",
    "install_smoke",
    "effect_eval",
    "security_review",
    "rollback",
}
check(target_watch_fields <= set(target_watch.get("required_fields", [])), "coding-agent target watch required fields are incomplete")
check(external.get("quality_gate", {}).get("coding_agent_target_watch_must_not_enable_runtime") is True, "coding-agent target watch quality gate must be true")


def fixture_errors(data, require_all=False):
    errors = []

    def fixture_require(obj, keys, label):
        for key in keys:
            if key not in obj or obj[key] in ("", None, []):
                errors.append(f"fixture {label} missing field: {key}")

    if data.get("runtime_enabled") is not False:
        errors.append("fixture must keep runtime_enabled=false")
    if data.get("fixture_mode") != "method-only":
        errors.append("fixture must keep fixture_mode=method-only")

    sections = {
        "portable_skill",
        "agentic_security",
        "agentic_skill_security",
        "skill_maintenance",
        "safe_output",
        "mcp_provenance",
        "mcp_protocol_watch",
        "otel_genai_adapter",
        "interoperability_watch",
        "coding_agent_target_watch",
    }
    if require_all:
        for section in sorted(sections):
            if section not in data:
                errors.append(f"fixture missing section: {section}")

    if "portable_skill" in data:
        fixture_require(data["portable_skill"], sorted(portable_fields), "portable_skill")

    if "agentic_security" in data:
        covered = data["agentic_security"].get("covered_threats", [])
        if covered != expected_asi:
            errors.append("fixture agentic_security must cover ASI01-ASI10 exactly once")

    if "agentic_skill_security" in data:
        covered = data["agentic_skill_security"].get("covered_threats", [])
        if covered != expected_ast:
            errors.append("fixture agentic_skill_security must cover AST01-AST10 exactly once")

    if "skill_maintenance" in data:
        fixture_require(data["skill_maintenance"], sorted(maintenance_fields), "skill_maintenance")
        value = data["skill_maintenance"]
        digest = value.get("content_digest")
        if digest not in (None, "") and (not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest)):
            errors.append("fixture skill_maintenance content_digest must be a sha256 digest")
        for field in ("use_evidence", "effect_evidence"):
            evidence = value.get(field)
            if evidence not in (None, "") and evidence != "not-measured" and not (
                isinstance(evidence, str) and evidence.startswith("measured:") and len(evidence) > len("measured:")
            ):
                errors.append(f"fixture skill_maintenance {field} must be measured evidence or not-measured")
        verified_at = value.get("last_verified_at")
        refresh_due_at = value.get("refresh_due_at")
        retire_due_at = value.get("retire_due_at")
        if all(isinstance(item, str) and item for item in (verified_at, refresh_due_at, retire_due_at)):
            try:
                verified_date = date.fromisoformat(verified_at)
                refresh_date = date.fromisoformat(refresh_due_at)
                retire_date = None if retire_due_at == "not-scheduled" else date.fromisoformat(retire_due_at)
            except ValueError:
                errors.append("fixture skill_maintenance lifecycle dates must be ISO dates or not-scheduled")
            else:
                if refresh_date < verified_date or (retire_date is not None and retire_date < verified_date):
                    errors.append("fixture skill_maintenance lifecycle dates must not precede last_verified_at")

    if "safe_output" in data:
        value = data["safe_output"]
        fixture_require(value, ["read_only_agent", "structured_output_schema", "schema_validation", "separate_write_executor", "operation_cap", "payload_size_cap_bytes", "kill_switch", "audit_record", "rollback_path"], "safe_output")
        if value.get("read_only_agent") is not True:
            errors.append("fixture safe_output agent must be read-only")
        if value.get("direct_write_allowed") is not False:
            errors.append("fixture safe_output must forbid direct agent writes")
        if value.get("schema_validation") is not True:
            errors.append("fixture safe_output must require schema validation")
        if value.get("separate_write_executor") is not True:
            errors.append("fixture safe_output must use a separate write executor")
        if not isinstance(value.get("operation_cap"), int) or value.get("operation_cap", 0) <= 0:
            errors.append("fixture safe_output operation_cap must be a positive integer")
        if value.get("kill_switch") is not True:
            errors.append("fixture safe_output must include a kill switch")

    if "mcp_provenance" in data:
        fixture_require(data["mcp_provenance"], sorted(provenance_fields), "mcp_provenance")

    if "mcp_protocol_watch" in data:
        value = data["mcp_protocol_watch"]
        mcp_watch_fields = (
            mcp_candidate_fields.difference({"protocol_version", "extension_ids"})
            | {"active_protocol_version", "candidate_protocol_version"}
        )
        fixture_require(value, sorted(mcp_watch_fields), "mcp_protocol_watch")
        if value.get("runtime_enabled") is not False:
            errors.append("fixture mcp_protocol_watch must keep runtime_enabled=false")
        if value.get("final_compatibility_claim") is not False:
            errors.append("fixture mcp_protocol_watch must not claim final compatibility")
        if value.get("source_ref") != "mcp-2026-07-28-final":
            errors.append("fixture mcp_protocol_watch must reference final release provenance")
        if value.get("release_status") != "released":
            errors.append("fixture mcp_protocol_watch must record released final metadata")
        feature_enablement = value.get("feature_enablement", {})
        for feature in ("tasks", "apps", "extensions"):
            if feature_enablement.get(feature) is not False:
                errors.append(f"fixture mcp_protocol_watch feature must remain disabled: {feature}")
        if value.get("extension_ids") != []:
            errors.append("fixture mcp_protocol_watch extension_ids must remain empty")
        if value.get("auth_profile") != compatibility.get("active_auth_profile"):
            errors.append("fixture mcp_protocol_watch must not weaken the active auth profile")

    if "otel_genai_adapter" in data:
        value = data["otel_genai_adapter"]
        fixture_require(
            value,
            ["upstream_repository", "upstream_revision", "schema_url_status", "deny_fields", "export_boundary"],
            "otel_genai_adapter",
        )
        if value.get("enabled_default") is not False:
            errors.append("fixture otel_genai_adapter must be disabled by default")
        if value.get("content_capture_enabled") is not False:
            errors.append("fixture otel_genai_adapter must keep content capture disabled")
        if value.get("upstream_repository") != "https://github.com/open-telemetry/semantic-conventions-genai":
            errors.append("fixture otel_genai_adapter upstream repository must be canonical")
        if value.get("upstream_revision") != "cc07f722069974139dab497d80d145144b19daca":
            errors.append("fixture otel_genai_adapter upstream revision must match reviewed snapshot")
        if value.get("schema_url_status") != "unavailable-upstream-todo":
            errors.append("fixture otel_genai_adapter schema URL must remain unavailable")
        if "schema_url" in value or "schema_version" in value:
            errors.append("fixture otel_genai_adapter must not invent schema URL/version")
        if not sensitive_fields <= set(value.get("deny_fields", [])):
            errors.append("fixture otel_genai_adapter deny list is incomplete")

    if "interoperability_watch" in data:
        protocols = data["interoperability_watch"].get("protocols", [])
        protocol_ids = [item.get("protocol_id") for item in protocols if isinstance(item, dict)]
        if protocol_ids != ["ACP", "A2A"]:
            errors.append("fixture interoperability_watch must contain ACP and A2A in order")
        for protocol in protocols:
            if not isinstance(protocol, dict):
                errors.append("fixture interoperability_watch protocol must be an object")
                continue
            protocol_id = protocol.get("protocol_id", "<missing-id>")
            fixture_require(protocol, ["protocol_id", "protocol_version", "activation_trigger"], f"interoperability_watch protocol {protocol_id}")
            if protocol.get("runtime_enabled") is not False:
                errors.append(f"fixture interoperability_watch protocol {protocol_id} must keep runtime_enabled=false")

    if "coding_agent_target_watch" in data:
        value = data["coding_agent_target_watch"]
        fixture_require(value, sorted(target_watch_fields), "coding_agent_target_watch")
        if value.get("runtime_enabled") is not False:
            errors.append("fixture coding_agent_target_watch must keep runtime_enabled=false")
        if value.get("direct_target_added") is not False:
            errors.append("fixture coding_agent_target_watch must not add a direct target")

    return errors


pass_fixture = load_json("fixtures/agent-ecosystem-standards/pass/local-fixture-bundle.json")
pass_errors = fixture_errors(pass_fixture, require_all=True)
check(not pass_errors, f"positive fixture failed: {pass_errors}")

negative_dir = root / "fixtures/agent-ecosystem-standards/fail"
negative_paths = sorted(negative_dir.glob("*.json")) if negative_dir.is_dir() else []
check(len(negative_paths) >= 6, "at least six ecosystem negative fixtures are required")
for path in negative_paths:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid negative fixture {path.relative_to(root)}: {exc}")
        continue
    expected = data.get("expected_failure")
    check(bool(expected), f"negative fixture {path.name} missing expected_failure")
    actual = fixture_errors(data)
    check(actual == [expected], f"negative fixture {path.name} expected exactly {expected!r}, got {actual!r}")

if failures:
    if summary_json:
        print(json.dumps({
            "schema_version": 1,
            "status": "fail",
            "checks": checked,
            "failures": failures,
        }, ensure_ascii=False, separators=(",", ":")))
    for item in failures:
        print(f"[FAIL] {item}", file=sys.stderr)
    sys.exit(1)

if summary_json:
    print(json.dumps({
        "schema_version": 1,
        "status": "pass",
        "checks": checked,
        "sources": len(expected_sources),
        "asi_threats": len(expected_asi),
        "negative_fixtures": len(negative_paths),
        "runtime_enabled": False,
    }, separators=(",", ":")))
else:
    print(f"[PASS] Agent ecosystem standards contracts checks={checked} sources={len(expected_sources)} asi=10 negative_fixtures={len(negative_paths)}")
PY
