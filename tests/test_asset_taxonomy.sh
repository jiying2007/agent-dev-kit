#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m agent_dev_kit.asset_taxonomy_contract --root "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# The taxonomy validator is a canonical JSON consumer. No shell compatibility
# shim or YAML projection is part of the active gate.
mkdir -p "$TMP_DIR/json-only"
cp "$ROOT_DIR/manifest.json" "$TMP_DIR/json-only/manifest.json"
python3 -m agent_dev_kit.asset_taxonomy_contract \
  --root "$TMP_DIR/json-only" \
  --summary-json >"$TMP_DIR/json-only-result.json"
python3 - "$TMP_DIR/json-only-result.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["status"] == "pass", data
assert data["source"] == "manifest.json", data
assert data["skills"] > 0, data
assert data["routing_scenarios"] > 0, data
PY

CATALOG_OUT="$TMP_DIR/catalog.md"
"$ROOT_DIR/scripts/catalog-assets.sh" build --out "$CATALOG_OUT"

grep -q '^## Skill Routing Matrix$' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing skill routing matrix" >&2
  exit 1
}

grep -q '| 30 | 10 | `planning` | primary | playbook | `adk-lightweight-planning` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing taxonomy columns for adk-lightweight-planning" >&2
  exit 1
}

grep -q '| `planning_only` | 用户明确要求只读计划，不创建、不修改、不删除文件 | profile-resolved | core | `-` | `adk-lightweight-planning` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing planning_only routing scenario" >&2
  exit 1
}

grep -q '| `long_execution` | 长任务需要计划审查、检查点、恢复和完成前闭环 | optional-skill-required | core, embedded-fullstack | `feature-delivery` | `adk-planning-execution-loop` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing optional availability for long_execution" >&2
  exit 1
}

[[ ! -e "$ROOT_DIR/scripts/check-asset-taxonomy.sh" ]] || { echo "[FAIL] retired taxonomy shim returned" >&2; exit 1; }

echo "[PASS] canonical asset taxonomy contract"
