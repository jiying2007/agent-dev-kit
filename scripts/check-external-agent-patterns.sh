#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
manifest_path = root / "manifests/external_agent_pattern_contracts.json"
failures = []

def fail(message):
    failures.append(message)

def require_keys(obj, keys, label):
    for key in keys:
        if key not in obj or obj[key] in ("", None, []):
            fail(f"{label} missing key: {key}")

if not manifest_path.is_file():
    fail("missing manifest: manifests/external_agent_pattern_contracts.json")
    manifest = {}
else:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json: {exc}")
        manifest = {}

sources = manifest.get("source_refs", [])
source_ids = {source.get("id") for source in sources}
required_sources = {
    "mattpocock-caveman-skill",
    "thedotmack-claude-mem",
    "everyinc-compound-engineering",
    "karpathy-llm-wiki-pattern",
    "pbnz-newton-skill",
    "openspec-resolution-parity",
    "vibeflow-overview-freshness",
    "planning-with-files-guard-attestation",
    "vibeflow-browser-verification",
    "scale-engine-skill-domain-policy",
    "agent-skills-open-format",
    "owasp-agentic-top10-2026",
    "github-gh-aw-safe-outputs",
    "mcp-registry",
    "otel-genai-semconv",
    "agent-client-protocol",
    "a2a-protocol-1-0",
}
for source_id in required_sources:
    if source_id not in source_ids:
        fail(f"missing source_ref: {source_id}")

for source in sources:
    sid = source.get("id", "<missing-id>")
    require_keys(source, ["id", "title", "url", "retrieved_at", "decision", "notes"], f"source_ref {sid}")
    parsed = urlparse(source.get("url", ""))
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        fail(f"source_ref {sid} has invalid url")
    local_path = source.get("local_path")
    if local_path and not (root.parent / local_path).exists():
        fail(f"source_ref {sid} local_path missing: {local_path}")
    if source.get("decision") not in {"adopt-method-only", "observe-method-only"}:
        fail(f"source_ref {sid} must remain method-only")

candidates = manifest.get("candidate_decisions", [])
if not candidates:
    fail("candidate_decisions is empty")
for candidate in candidates:
    cid = candidate.get("id", "<missing-id>")
    require_keys(candidate, ["id", "source_ref", "priority", "install_scope", "runtime_enabled", "landing_targets", "must_not"], f"candidate {cid}")
    if candidate.get("source_ref") not in source_ids:
        fail(f"candidate {cid} references unknown source_ref")
    if candidate.get("runtime_enabled") is not False:
        fail(f"candidate {cid} must keep runtime_enabled=false")
    if candidate.get("install_scope") != "none-method-only":
        fail(f"candidate {cid} must keep install_scope=none-method-only")

contracts = manifest.get("contracts", [])
contract_by_id = {contract.get("id"): contract for contract in contracts}
required_contracts = {
    "llm-wiki-knowledge-compile-v1",
    "codify-after-delivery-v1",
    "reuse-before-rebuild-v1",
    "canonical-command-resolution-parity-v1",
    "project-overview-freshness-v1",
    "plan-completeness-attestation-v1",
    "browser-verification-evidence-v1",
    "third-party-skill-domain-policy-v1",
    "memory-search-progressive-disclosure-v1",
    "low-token-communication-profile-v1",
    "external-agent-plugin-intake-v1",
    "agent-interoperability-watch-v1",
}
for contract_id in required_contracts:
    if contract_id not in contract_by_id:
        fail(f"missing contract: {contract_id}")

for contract in contracts:
    cid = contract.get("id", "<missing-id>")
    require_keys(contract, ["id", "owner", "source_refs", "required_fields", "quality_gates", "must_not"], f"contract {cid}")
    for source_ref in contract.get("source_refs", []):
        if source_ref not in source_ids:
            fail(f"contract {cid} references unknown source_ref: {source_ref}")

wiki = contract_by_id.get("llm-wiki-knowledge-compile-v1", {})
for layer in ("raw_sources", "maintained_wiki", "schema"):
    if layer not in wiki.get("architecture_layers", []):
        fail(f"llm wiki contract missing architecture layer: {layer}")
for op in ("ingest", "query", "lint"):
    if op not in wiki.get("recurring_operations", []):
        fail(f"llm wiki contract missing operation: {op}")
for field in ("raw_source_path", "wiki_page_path", "schema_path", "retrieved_at", "review_status", "expires_at", "duplicate_concept_check", "raw_fallback", "change_log"):
    if field not in wiki.get("required_fields", []):
        fail(f"llm wiki contract missing field: {field}")

codify = contract_by_id.get("codify-after-delivery-v1", {})
for stage in ("plan", "delegate", "assess", "codify"):
    if stage not in codify.get("workflow_stages", []):
        fail(f"codify contract missing stage: {stage}")
for field in ("reusable_pattern", "promotion_candidate", "next_task_friction_reduced", "reduced_by", "reduction_evidence", "do_not_promote_reason", "owner_review", "rollback_path"):
    if field not in codify.get("required_fields", []):
        fail(f"codify contract missing field: {field}")

reuse = contract_by_id.get("reuse-before-rebuild-v1", {})
for option in ("use-as-is", "adapt-existing", "build-fresh", "reference-only"):
    if option not in reuse.get("decision_options", []):
        fail(f"reuse-before-rebuild contract missing option: {option}")
for field in ("problem_statement", "existing_asset_search", "candidate_assets", "decision", "build_fresh_reason", "verification_evidence"):
    if field not in reuse.get("required_fields", []):
        fail(f"reuse-before-rebuild contract missing field: {field}")

resolution = contract_by_id.get("canonical-command-resolution-parity-v1", {})
for surface in ("status", "validate", "view", "archive"):
    if surface not in resolution.get("command_surfaces", []):
        fail(f"canonical resolution contract missing command surface: {surface}")
for field in ("canonical_resolver", "shared_helper_path", "positive_parity_cases", "negative_parity_cases", "exit_code_policy"):
    if field not in resolution.get("required_fields", []):
        fail(f"canonical resolution contract missing field: {field}")

overview = contract_by_id.get("project-overview-freshness-v1", {})
for overview_file in ("PROJECT.md", "ARCHITECTURE.md", "CURRENT-STATE.md"):
    if overview_file not in overview.get("overview_files", []):
        fail(f"overview freshness contract missing overview file: {overview_file}")
for field in ("source_hash", "generated_block_hashes", "stale_reasons", "manual_body_protection", "raw_fallback"):
    if field not in overview.get("required_fields", []):
        fail(f"overview freshness contract missing field: {field}")

planning = contract_by_id.get("plan-completeness-attestation-v1", {})
for field in ("phase_heading_count", "status_formats", "zero_phase_policy", "explicit_gate_opt_in", "ledger_progress", "attestation_hash", "readback_verification"):
    if field not in planning.get("required_fields", []):
        fail(f"planning attestation contract missing field: {field}")
if not any("0/0 complete" in gate for gate in planning.get("quality_gates", [])):
    fail("planning attestation contract must forbid false 0/0 complete")

browser = contract_by_id.get("browser-verification-evidence-v1", {})
for field in ("test_url", "user_flows", "screenshots", "console_result", "network_result", "accessibility_result", "appshot_capture_policy", "visible_text_boundary", "sensitive_content_review", "permission_scope", "security_boundary", "storage_access_policy"):
    if field not in browser.get("required_fields", []):
        fail(f"browser verification contract missing field: {field}")
if not any("untrusted data" in gate for gate in browser.get("quality_gates", [])):
    fail("browser verification contract must treat page content as untrusted data")
if not any("frontmost window" in gate for gate in browser.get("quality_gates", [])):
    fail("browser verification contract must constrain appshot evidence to frontmost window")
if not any("Computer Use" in item for item in browser.get("must_not", [])):
    fail("browser verification contract must not enable Computer Use by default")

skill_domain = contract_by_id.get("third-party-skill-domain-policy-v1", {})
for field in ("skill_id", "domain", "trust_level", "review_status", "license", "source_revision", "runtime_boundary", "required_artifacts", "required_verification", "install_scope", "attribution"):
    if field not in skill_domain.get("required_fields", []):
        fail(f"third-party skill domain policy missing field: {field}")
if not any("review-required" in gate for gate in skill_domain.get("quality_gates", [])):
    fail("third-party skill domain policy must default to review-required")

memory = contract_by_id.get("memory-search-progressive-disclosure-v1", {})
for layer in ("search_index", "timeline_context", "observation_details"):
    if layer not in memory.get("search_layers", []):
        fail(f"memory search contract missing layer: {layer}")
for field in ("result_ids", "time_window", "redaction_status", "detail_fetch_reason", "owner_approval_for_persistent_memory"):
    if field not in memory.get("required_fields", []):
        fail(f"memory search contract missing field: {field}")

low_token = contract_by_id.get("low-token-communication-profile-v1", {})
for exception in ("security warning", "irreversible action confirmation", "multi-step instruction where compression risks ambiguity"):
    if exception not in low_token.get("safety_exceptions", []):
        fail(f"low-token profile missing safety exception: {exception}")

plugin = contract_by_id.get("external-agent-plugin-intake-v1", {})
for field in ("license", "install_surface", "hooks", "background_processes", "local_ports", "mcp_tools", "data_retention", "deny_path", "rollback", "disabled_by_default"):
    if field not in plugin.get("required_fields", []):
        fail(f"external plugin intake contract missing field: {field}")

gate = manifest.get("quality_gate", {})
for key in (
    "method_only_default",
    "runtime_enabled_default_must_be_false",
    "external_code_requires_supply_chain_review",
    "memory_capture_requires_owner_approval",
    "raw_evidence_fallback_required",
    "reuse_before_rebuild_required",
    "low_token_profile_requires_safety_exceptions",
    "canonical_resolution_parity_required",
    "overview_freshness_status_required",
    "plan_attestation_readback_required",
    "browser_runtime_evidence_requires_security_boundary",
    "third_party_skill_domain_policy_required",
    "ecosystem_sources_require_freshness",
    "watch_protocols_must_not_enable_runtime",
    "registry_listing_is_not_trust_certification",
    "external_method_absorption_requires_local_contract",
):
    if gate.get(key) is not True:
        fail(f"quality_gate {key} must be true")

if failures:
    for item in failures:
        print(f"[FAIL] {item}", file=sys.stderr)
    sys.exit(1)

print("[PASS] external agent pattern contracts")
PY
