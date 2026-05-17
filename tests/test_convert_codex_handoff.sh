#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/convert-assets.sh" \
  --target codex \
  --profile core \
  --with-optional-skill adk-incident-rca-report \
  --codex-profile team-collab \
  --out "$TMP_DIR" \
  --clean

[[ -f "$TMP_DIR/codex/src/codex-home/vendor/agents/agent-dev-kit/2.9.0/requirements-analyst/AGENTS.md" ]] || {
  echo "[FAIL] missing codex vendor agent" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/src/codex-home/vendor/skills/adk-requirements-triage/1.1.0/SKILL.md" ]] || {
  echo "[FAIL] missing codex vendor skill" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/src/codex-home/vendor/skills/adk-incident-rca-report/1.0.0/SKILL.md" ]] || {
  echo "[FAIL] missing codex vendor optional skill" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/manifest-fragments/agents.json" ]] || {
  echo "[FAIL] missing codex agents manifest fragment" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/manifest-fragments/skills.json" ]] || {
  echo "[FAIL] missing codex skills manifest fragment" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/manifest-fragments/workflows.json" ]] || {
  echo "[FAIL] missing codex workflows manifest fragment" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/manifest-fragments/mcp_servers.json" ]] || {
  echo "[FAIL] missing codex MCP manifest fragment" >&2
  exit 1
}

[[ -f "$TMP_DIR/codex/manifest-fragments/change_sets.json" ]] || {
  echo "[FAIL] missing codex change set manifest fragment" >&2
  exit 1
}

rtk python3 - "$TMP_DIR/codex" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
agents = json.loads((root / "manifest-fragments/agents.json").read_text())
skills = json.loads((root / "manifest-fragments/skills.json").read_text())
workflows = json.loads((root / "manifest-fragments/workflows.json").read_text())
mcp_servers = json.loads((root / "manifest-fragments/mcp_servers.json").read_text())
change_sets = json.loads((root / "manifest-fragments/change_sets.json").read_text())

agent = next(item for item in agents["agents"] if item["name"] == "requirements-analyst")
skill = next(item for item in skills["skills"] if item["name"] == "adk-requirements-triage")
optional = next(item for item in skills["skills"] if item["name"] == "adk-incident-rca-report")
workflow = next(item for item in workflows["workflows"] if item["name"] == "adk-delivery-gate")
change_set = next(item for item in change_sets["change_sets"] if item["name"] == "adk-change-governance")

assert agent["vendor_rel"] == "vendor/agents/agent-dev-kit/2.9.0/requirements-analyst/AGENTS.md"
assert agent["target_rel"] == "agents/requirements-analyst/AGENTS.md"
assert agent["profiles"] == ["team-collab"]
assert skill["vendor_rel"] == "vendor/skills/adk-requirements-triage/1.1.0"
assert skill["target_rel"] == "skills/adk-requirements-triage"
assert optional["vendor_rel"] == "vendor/skills/adk-incident-rca-report/1.0.0"
assert optional["profiles"] == ["team-collab"]
assert workflow["profiles"] == ["team-collab"]
assert "adk-verification-before-completion" in workflow["skills"]
assert "code-review-governor" in workflow["agents"]
assert mcp_servers["mcp_servers"] == []
assert change_set["root"] == "docs/changes"
assert "proposal.md" in change_set["required_files"]
PY

summary="$("$ROOT_DIR/scripts/convert-assets.sh" \
  --target codex \
  --profile core \
  --codex-profile team-collab \
  --out "$TMP_DIR/summary" \
  --clean \
  --summary-json)"
echo "$summary" | grep -q '"change_sets":1' || {
  echo "[FAIL] convert summary missing change set count" >&2
  exit 1
}

echo "[PASS] convert codex handoff"
