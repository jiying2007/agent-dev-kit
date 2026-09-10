#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ ! -e "$ROOT/manifest.yaml" ]] || {
  echo "[FAIL] legacy manifest.yaml must not exist" >&2
  exit 1
}

grep -q 'ADK_MANIFEST=.*manifest.json' "$ROOT/scripts/lib-manifest.sh" || {
  echo "[FAIL] shell Manifest adapter is not bound to manifest.json" >&2
  exit 1
}

# Prove the stable shell API reads canonical JSON for mapping, list and routing
# queries without depending on a generated compatibility projection.
# shellcheck source=../scripts/lib-manifest.sh
source "$ROOT/scripts/lib-manifest.sh"
adk_require_manifest
adk_profile_exists core
[[ "$(adk_get_manifest_item_value agents requirements-analyst path)" == "agents/requirements-analyst/AGENTS.md" ]]
adk_list_routing_intent_names | grep -q .

# The taxonomy contract must also work in an isolated JSON-only root.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cp "$ROOT/manifest.json" "$TMP_DIR/manifest.json"
python3 -m agent_dev_kit.asset_taxonomy_contract --root "$TMP_DIR" --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["source"]=="manifest.json"'

echo "[PASS] Manifest consumers use canonical JSON without a compatibility projection"
