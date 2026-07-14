#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-agent-ecosystem-standards.sh" >/dev/null
"$ROOT_DIR/scripts/check-agent-ecosystem-standards.sh" --summary-json | rg -q '"status":"pass"'
"$ROOT_DIR/scripts/check-external-agent-patterns.sh" >/dev/null
"$ROOT_DIR/scripts/validate-assets.sh" --strict >/dev/null

python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

external = json.loads((root / "manifests/external_agent_pattern_contracts.json").read_text(encoding="utf-8"))
sources = {item["id"]: item for item in external["source_refs"]}
assert sources["agent-skills-open-format"]["decision"] == "adopt-method-only"
assert sources["owasp-agentic-top10-2026"]["decision"] == "adopt-method-only"
assert sources["agent-client-protocol"]["decision"] == "observe-method-only"
assert sources["a2a-protocol-1-0"]["decision"] == "observe-method-only"

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

trace = json.loads((root / "manifests/trace_eval_contracts.json").read_text(encoding="utf-8"))
adapter = trace["interoperability_adapters"][0]
assert adapter["schema_version"] == "1.42.0"
assert adapter["content_capture"]["enabled_default"] is False
assert adapter["content_capture"]["allow_opt_in"] is False
PY

echo "[PASS] Agent ecosystem standards test"
