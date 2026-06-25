#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-tool-skill-evidence-contracts.sh" >/dev/null
"$ROOT_DIR/scripts/check-tool-skill-evidence-contracts.sh" --summary-json | rg -q '"status":"pass"'
python3 -m json.tool "$ROOT_DIR/manifests/tool_skill_evidence_contracts.json" >/dev/null

echo "[PASS] tool/skill evidence contracts test"
