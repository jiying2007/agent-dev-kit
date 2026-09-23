#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-agent-ecosystem-standards.sh" >/dev/null
"$ROOT_DIR/scripts/check-agent-ecosystem-standards.sh" --summary-json | rg -q '"status":"pass"'
"$ROOT_DIR/scripts/check-external-agent-patterns.sh" >/dev/null
"$ROOT_DIR/scripts/check-external-agent-patterns.sh" --help | rg -q -- '--require-local-sources'
if [[ ! -f "${ADK_TEST_SUITE_DIR:-/nonexistent}/validate-summary.json" ]]; then
  bash "$ROOT_DIR/scripts/devkit.sh" validate --strict >/dev/null
fi

python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path(sys.argv[1])

external = json.loads((root / "manifests/external_agent_pattern_contracts.json").read_text(encoding="utf-8"))
local_policy = external["local_source_policy"]
assert local_policy["default_required"] is False
assert local_policy["strict_flag"] == "--require-local-sources"
assert local_policy["resolution_base"] == "parent-of-adk-root"
assert set(local_policy["required_fallback_fields"]) == {"url", "retrieved_at", "decision", "notes"}
sources = {item["id"]: item for item in external["source_refs"]}
assert sources["agent-skills-open-format"]["decision"] == "adopt-method-only"
assert sources["owasp-agentic-top10-2026"]["decision"] == "adopt-method-only"
assert sources["agent-client-protocol"]["decision"] == "observe-method-only"
assert sources["a2a-protocol-1-0"]["decision"] == "observe-method-only"
assert sources["mcp-2026-07-28-final"]["decision"] == "enhance-metadata-only"
assert sources["mcp-2026-07-28-final"]["candidate_id"] == "epc-c6f947d482aa8aa0c78f"
assert sources["mcp-2026-07-28-final"]["owner"] == "leiwenjun"
assert sources["mcp-2026-07-28-final"]["release_tag"] == "2026-07-28"
assert sources["mcp-2026-07-28-final"]["revision"] == "5f5440bb26a62e2cf3440b92da5a667efa03b267"
assert sources["owasp-agentic-skills-top10-2026"]["decision"] == "observe-method-only"
assert sources["agent-skills-in-the-wild-2026"]["decision"] == "adopt-method-only"
assert sources["vscode-agent-skills-2026"]["decision"] == "observe-method-only"

runtime = json.loads((root / "manifests/adk_runtime_policy_gates.json").read_text(encoding="utf-8"))
threats = runtime["agentic_security_taxonomy"]["threats"]
assert [item["id"] for item in threats] == [f"ASI{index:02d}" for index in range(1, 11)]
assert threats[5]["name"] == "Memory and Context Poisoning"
assert threats[9]["name"] == "Rogue Agents"

automation = json.loads((root / "manifests/automation_worktree_contracts.json").read_text(encoding="utf-8"))
safe_output = automation["safe_output_contract"]
assert safe_output["agent_phase"]["direct_write_allowed"] is False
assert safe_output["validation_phase"]["required"] is True
assert safe_output["executor_phase"]["separate_identity_or_job"] is True

mcp = json.loads((root / "manifests/skill_mcp_dependencies.json").read_text(encoding="utf-8"))
for dependency in mcp["dependencies"]:
    assert dependency["provenance"]["artifact_digest"]
    assert dependency["provenance"]["trust_decision"]
compatibility = mcp["protocol_compatibility_policy"]
assert compatibility["active_protocol_version"] == "2026-07-28"
assert compatibility["active_status"] == "supported-current-governance-only"
assert compatibility["active_scope"] == "protocol-governance-contract-only"
assert compatibility["active_runtime_enabled"] is False
assert compatibility["active_feature_enablement"] == {
    "tasks": False,
    "apps": False,
    "extensions": False,
}
candidate = compatibility["candidates"][0]
assert candidate["protocol_version"] == "2026-07-28"
assert candidate["source_ref"] == "mcp-2026-07-28-final"
assert candidate["release_status"] == "released"
assert candidate["runtime_enabled"] is False
assert candidate["final_compatibility_claim"] is True
assert candidate["compatibility_test"] == "pass-mcp-2026-activation-fixture-2026-07-31"
assert candidate["compatibility_scope"].startswith("go-sdk-v1.7.0-pre.3-")
assert candidate["compatibility_evidence"]["sdk_module"] == "github.com/modelcontextprotocol/go-sdk"
assert candidate["compatibility_evidence"]["sdk_version"] == "v1.7.0-pre.3"
assert candidate["compatibility_evidence"]["sdk_revision"] == "827f90ba0c13edb546028df42fadc9f1211a4ff2"
assert candidate["compatibility_evidence"]["network_mode"] == "offline-container-loopback-only"
assert candidate["extension_ids"] == []
assert candidate["feature_enablement"] == {"tasks": False, "apps": False, "extensions": False}
activation = compatibility["activation_gate"]
assert activation["final_spec_retrieved"] is True
assert activation["breaking_change_diff_completed"] is True
assert activation["technical_readiness_completed"] is True
assert activation["owner_decision_required"] is True
assert activation["owner_decision_schema"] == "schemas/mcp-protocol-activation-decision.schema.json"
assert activation["owner_decision_schema_version"] == "mcp-protocol-activation-decision/v1"
assert activation["owner_decision_allowed"] == ["ACTIVATE", "HOLD", "REJECT"]
assert activation["owner_decision_completed"] is True
assert activation["owner_decision_id"] == "mcp-act-2026-07-31-leiwenjun"
assert (
    activation["owner_decision_path"]
    == "docs/changes/mcp-2026-activation-readiness-2026-07-31/owner-activation-decision.json"
)
assert activation["activation_allowed"] is True
assert activation["activation_completed"] is True
assert activation["activation_scope"] == "protocol-governance-contract-only"
assert activation["activated_at"] == "2026-07-31"
assert activation["rollback_target_protocol_version"] == "2025-11-25"
for field in (
    "schema_fixture_completed",
    "client_server_smoke_completed",
    "auth_security_review_completed",
    "rollback_smoke_completed",
):
    assert activation[field] is True

activation_decision_schema = json.loads(
    (root / activation["owner_decision_schema"]).read_text(encoding="utf-8")
)
assert activation_decision_schema["$id"] == activation["owner_decision_schema_version"]
assert activation_decision_schema["properties"]["decision"]["enum"] == activation["owner_decision_allowed"]
assert activation_decision_schema["properties"]["runtime_enabled"]["const"] is False
Draft202012Validator.check_schema(activation_decision_schema)
activation_decision = json.loads(
    (root / activation["owner_decision_path"]).read_text(encoding="utf-8")
)
Draft202012Validator(
    activation_decision_schema,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
).validate(activation_decision)
assert activation_decision["decision_id"] == activation["owner_decision_id"]
assert activation_decision["candidate_id"] == "epc-c6f947d482aa8aa0c78f"
assert activation_decision["protocol_version"] == compatibility["active_protocol_version"]
assert activation_decision["decision"] == "ACTIVATE"
assert activation_decision["owner"] == "leiwenjun"
assert activation_decision["scope"] == compatibility["active_scope"]
assert activation_decision["runtime_enabled"] is False
assert activation_decision["feature_enablement"] == compatibility["active_feature_enablement"]

skill = json.loads((root / "manifests/skill_reproducibility_contracts.json").read_text(encoding="utf-8"))
skill_threats = skill["agentic_skill_security_taxonomy"]["threats"]
assert [item["id"] for item in skill_threats] == [f"AST{index:02d}" for index in range(1, 11)]
maintenance = next(item for item in skill["contracts"] if item["id"] == "skill-maintenance-evidence-v1")
assert "stable_behavior_diff" in maintenance["required_fields"]
assert "target_local_binding_diff" in maintenance["required_fields"]
assert maintenance["unknown_effect_policy"] == "explicit-not-measured"

target_watch = next(item for item in external["contracts"] if item["id"] == "coding-agent-target-watch-v1")
assert target_watch["runtime_enabled"] is False
assert target_watch["direct_target_added"] is False

trace = json.loads((root / "manifests/trace_eval_contracts.json").read_text(encoding="utf-8"))
adapter = trace["interoperability_adapters"][0]
assert adapter["input_contract"] == "adk-workflow-trace-summary-v2"
assert "goal_ref" in adapter["native_only_fields"]
assert "next_goal_ref" in adapter["native_only_fields"]
assert "goal" not in adapter["native_only_fields"]
assert "next_goal" not in adapter["native_only_fields"]
assert adapter["upstream_repository"] == "https://github.com/open-telemetry/semantic-conventions-genai"
assert adapter["upstream_revision"] == "cc07f722069974139dab497d80d145144b19daca"
assert adapter["schema_url_status"] == "unavailable-upstream-todo"
assert "schema_url" not in adapter
assert "schema_version" not in adapter
assert adapter["content_capture"]["enabled_default"] is False
assert adapter["content_capture"]["allow_opt_in"] is False
PY

echo "[PASS] Agent ecosystem standards test"
