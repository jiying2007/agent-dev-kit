#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REQUIRE_LOCAL_SOURCES=0
MANIFEST_PATH="$ROOT_DIR/manifests/external_agent_pattern_contracts.json"
REFERENCE_LOCK_PATH=""
AS_OF=""
MAX_OBSERVATION_AGE_DAYS=""

usage() {
  cat <<'USAGE'
Usage:
  scripts/check-external-agent-patterns.sh [--require-local-sources] [--manifest PATH]
    [--reference-lock PATH] [--as-of YYYY-MM-DD --max-observation-age-days N]

Validates method-only external pattern contracts. Sibling reference clones are
optional for standalone ADK checkouts. Use --require-local-sources only from a
managed parent workspace that is expected to contain every declared local_path.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-local-sources)
      REQUIRE_LOCAL_SOURCES=1
      shift
      ;;
    --manifest)
      MANIFEST_PATH="${2:-}"
      [[ -n "$MANIFEST_PATH" ]] || { echo "[FAIL] --manifest requires a path" >&2; exit 2; }
      shift 2
      ;;
    --reference-lock)
      REFERENCE_LOCK_PATH="${2:-}"
      [[ -n "$REFERENCE_LOCK_PATH" ]] || { echo "[FAIL] --reference-lock requires a path" >&2; exit 2; }
      shift 2
      ;;
    --as-of)
      AS_OF="${2:-}"
      [[ -n "$AS_OF" ]] || { echo "[FAIL] --as-of requires a date" >&2; exit 2; }
      shift 2
      ;;
    --max-observation-age-days)
      MAX_OBSERVATION_AGE_DAYS="${2:-}"
      [[ "$MAX_OBSERVATION_AGE_DAYS" =~ ^[0-9]+$ ]] || {
        echo "[FAIL] --max-observation-age-days requires a non-negative integer" >&2
        exit 2
      }
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$AS_OF" && -z "$MAX_OBSERVATION_AGE_DAYS" ]]; then
  echo "[FAIL] --as-of requires --max-observation-age-days" >&2
  exit 2
fi

python3 - "$ROOT_DIR" "$REQUIRE_LOCAL_SOURCES" "$MANIFEST_PATH" "$REFERENCE_LOCK_PATH" "$AS_OF" "$MAX_OBSERVATION_AGE_DAYS" <<'PY'
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

root = Path(sys.argv[1])
require_local_sources = sys.argv[2] == "1"
manifest_path = Path(sys.argv[3])
reference_lock_path = Path(sys.argv[4]) if sys.argv[4] else None
as_of_raw = sys.argv[5]
max_age_raw = sys.argv[6]
failures = []
MAX_MANIFEST_BYTES = 2 * 1024 * 1024

def fail(message):
    failures.append(message)

def require_keys(obj, keys, label):
    for key in keys:
        if key not in obj or obj[key] in ("", None, []):
            fail(f"{label} missing key: {key}")

def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value

def load_document(path, label, limit):
    if path.is_symlink() or not path.is_file():
        fail(f"{label} is missing or a symlink")
        return {}
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError(f"{label} exceeds byte budget")
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        if not isinstance(document, dict):
            raise ValueError(f"{label} root must be an object")
        return document
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        fail(f"invalid {label}: {exc}")
        return {}

manifest = load_document(manifest_path, "manifest", MAX_MANIFEST_BYTES)
reference_lock = load_document(reference_lock_path, "reference lock", 1024 * 1024) if reference_lock_path else None

sources = manifest.get("source_refs", [])
local_policy = manifest.get("local_source_policy", {})
require_keys(
    local_policy,
    ["id", "default_required", "strict_flag", "resolution_base", "required_fallback_fields", "must_not"],
    "local_source_policy",
)
if local_policy.get("default_required") is not False:
    fail("local_source_policy default_required must be false")
if local_policy.get("strict_flag") != "--require-local-sources":
    fail("local_source_policy strict_flag must be --require-local-sources")
if local_policy.get("resolution_base") != "parent-of-adk-root":
    fail("local_source_policy resolution_base must be parent-of-adk-root")
for field in ("url", "retrieved_at", "decision", "notes"):
    if field not in local_policy.get("required_fallback_fields", []):
        fail(f"local_source_policy missing fallback field: {field}")
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

local_observations = {}
for source in sources:
    sid = source.get("id", "<missing-id>")
    require_keys(source, ["id", "title", "url", "retrieved_at", "decision", "notes"], f"source_ref {sid}")
    parsed = urlparse(source.get("url", ""))
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        fail(f"source_ref {sid} has invalid url")
    local_path = source.get("local_path")
    if local_path:
        require_keys(
            source,
            ["reference_pin", "remote_head_observed", "remote_relation", "canonical_checked_at"],
            f"source_ref {sid}",
        )
        if source.get("ancestry_checked") is not False:
            fail(f"source_ref {sid} must disclose ancestry_checked=false")
        canonical = urlparse(source.get("url", ""))
        try:
            canonical_valid = (
                canonical.scheme == "https"
                and canonical.hostname in {"github.com", "gitee.com"}
                and canonical.username is None
                and canonical.password is None
                and canonical.port is None
                and not canonical.query
                and not canonical.fragment
                and len([part for part in canonical.path.split("/") if part]) == 2
            )
        except ValueError:
            canonical_valid = False
        if not canonical_valid:
            fail(f"source_ref {sid} canonical URL is invalid")
        pin, head = source.get("reference_pin"), source.get("remote_head_observed")
        if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value) for value in (pin, head)):
            fail(f"source_ref {sid} reference pin or observed HEAD is invalid")
        elif source.get("remote_relation") != ("same" if pin == head else "different"):
            fail(f"source_ref {sid} remote relation disagrees with exact SHAs")
        try:
            checked = date.fromisoformat(source["canonical_checked_at"])
            retrieved = date.fromisoformat(source["retrieved_at"])
            if not retrieved <= checked <= date.today():
                fail(f"source_ref {sid} canonical check date is inconsistent")
        except (KeyError, TypeError, ValueError):
            fail(f"source_ref {sid} canonical check date is invalid")
        observation = (source.get("url"), pin, head, source.get("remote_relation"), source.get("canonical_checked_at"))
        if local_path in local_observations and local_observations[local_path] != observation:
            fail(f"source_ref {sid} disagrees with another entry for {local_path}")
        local_observations[local_path] = observation
        local_relative = Path(local_path)
        if local_relative.is_absolute() or ".." in local_relative.parts:
            fail(f"source_ref {sid} local_path must be a safe relative path")
        elif require_local_sources and not (root.parent / local_relative).exists():
            fail(f"source_ref {sid} local_path missing: {local_path}")
    if source.get("decision") not in {"adopt-method-only", "enhance-metadata-only", "observe-method-only"}:
        fail(f"source_ref {sid} must remain method-only")

def repo_identity(url):
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    try:
        valid = (
            parsed.scheme == "https" and parsed.hostname in {"github.com", "gitee.com"}
            and parsed.username is None and parsed.password is None and parsed.port is None
            and not parsed.query and not parsed.fragment
        )
    except ValueError:
        valid = False
    parts = [part for part in parsed.path.split("/") if part]
    if not valid or len(parts) != 2 or any(part in {".", ".."} for part in parts):
        return None
    repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    return parsed.hostname, parts[0], repo

if reference_lock is not None:
    if reference_lock.get("schema") != "llm-agent-reference-pins/v2":
        fail("reference lock schema is unsupported")
    policy = reference_lock.get("policy", {})
    if not isinstance(policy, dict) or policy.get("runtime_enablement") is not False or policy.get("pin_is_evidence_not_source") is not True:
        fail("reference lock policy is not method-only")
    pins = reference_lock.get("pins", [])
    if not isinstance(pins, list):
        fail("reference lock pins must be an array")
        pins = []
    by_path = {}
    for pin_record in pins:
        if not isinstance(pin_record, dict):
            fail("reference lock contains a non-object pin")
            continue
        if pin_record.get("kind") != "reference-repo":
            continue
        path = pin_record.get("path")
        if not isinstance(path, str) or not path:
            fail("reference lock has an invalid reference path")
            continue
        if path in by_path:
            fail(f"reference lock has duplicate path: {path}")
        by_path[path] = pin_record
    for path, observation in local_observations.items():
        pin_record = by_path.get(path)
        if pin_record is None:
            fail(f"reference lock lacks local source: {path}")
            continue
        if repo_identity(pin_record.get("url")) != repo_identity(observation[0]):
            fail(f"reference lock canonical URL differs: {path}")
        if pin_record.get("commit") != observation[1]:
            fail(f"reference lock exact pin differs: {path}")

if max_age_raw:
    max_age = int(max_age_raw)
    if max_age > 365:
        fail("observation freshness budget exceeds 365 days")
    try:
        as_of = date.fromisoformat(as_of_raw) if as_of_raw else date.today()
    except ValueError:
        fail("observation as-of date is invalid")
        as_of = None
    if as_of is not None:
        for path, observation in local_observations.items():
            try:
                checked = date.fromisoformat(observation[4])
            except (TypeError, ValueError):
                continue
            if checked > as_of or (as_of - checked).days > max_age:
                fail(f"reference observation is stale or from the future: {path}")

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
