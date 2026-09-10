#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

[[ ! -e "$ROOT/manifest.yaml" ]] || {
  echo "[FAIL] legacy manifest.yaml must not exist" >&2
  exit 1
}

grep -q 'ADK_MANIFEST=.*manifest.json' "$ROOT/scripts/lib-manifest.sh" || {
  echo "[FAIL] shell Manifest adapter is not bound to manifest.json" >&2
  exit 1
}

for active in \
  "$ROOT/scripts/lib-manifest.sh" \
  "$ROOT/scripts/catalog-assets.sh" \
  "$ROOT/scripts/health-check.sh"; do
  if grep -q 'manifest.yaml' "$active"; then
    echo "[FAIL] active Manifest consumer still references manifest.yaml: ${active#$ROOT/}" >&2
    exit 1
  fi
done

# Prove the stable shell API reads canonical JSON for mapping, list and routing
# queries without depending on a generated compatibility projection.
# shellcheck source=../scripts/lib-manifest.sh
source "$ROOT/scripts/lib-manifest.sh"
adk_require_manifest
adk_profile_exists core
[[ "$(adk_get_manifest_item_value agents requirements-analyst path)" == "agents/requirements-analyst/AGENTS.md" ]]
adk_list_routing_intent_names | grep -q .

# Taxonomy remains valid with only the canonical Manifest available.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cp "$ROOT/manifest.json" "$TMP_DIR/manifest.json"
python3 -m agent_dev_kit.asset_taxonomy_contract --root "$TMP_DIR" --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["source"]=="manifest.json"'

# Health is also a canonical projection and must reject reintroduced mirrors.
python3 -m agent_dev_kit.health_contract --root "$ROOT" --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass", d'

echo "[PASS] active Manifest consumers are JSON-only and canonical"
