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
  - read-only agent -> validated safe output -> separate write executor
  - MCP dependency provenance
  - version-pinned OpenTelemetry GenAI adapter with content capture disabled
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
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
summary_json = sys.argv[2] == "1"
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

adapters = {
    item.get("id"): item
    for item in trace.get("interoperability_adapters", [])
    if isinstance(item, dict)
}
otel = adapters.get("otel-genai-trace-summary-v1", {})
check(bool(otel), "missing OTel GenAI trace adapter")
check(otel.get("enabled_default") is False, "OTel GenAI adapter must be disabled by default")
check(otel.get("schema_url") == "https://opentelemetry.io/schemas/gen-ai/1.42.0", "OTel GenAI adapter schema URL must be pinned")
check(otel.get("schema_version") == "1.42.0", "OTel GenAI adapter schema version must be pinned")
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
        "safe_output",
        "mcp_provenance",
        "otel_genai_adapter",
        "interoperability_watch",
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

    if "otel_genai_adapter" in data:
        value = data["otel_genai_adapter"]
        fixture_require(value, ["schema_url", "schema_version", "deny_fields", "export_boundary"], "otel_genai_adapter")
        if value.get("enabled_default") is not False:
            errors.append("fixture otel_genai_adapter must be disabled by default")
        if value.get("content_capture_enabled") is not False:
            errors.append("fixture otel_genai_adapter must keep content capture disabled")
        if value.get("schema_url") != "https://opentelemetry.io/schemas/gen-ai/1.42.0":
            errors.append("fixture otel_genai_adapter schema URL must be pinned")
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
