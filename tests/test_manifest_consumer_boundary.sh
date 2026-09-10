#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# New typed product code must consume canonical manifest.json. The only Python
# modules allowed to mention the legacy YAML projection are the manifest
# compatibility contract/facade themselves.
mapfile -t offenders < <(
  grep -RIl --include='*.py' 'manifest\.yaml' "$ROOT/src/agent_dev_kit" \
    | sed "s#^$ROOT/##" \
    | grep -v -E '^src/agent_dev_kit/(manifest_contract\.py|domain/manifest\.py)$' \
    || true
)

if (( ${#offenders[@]} > 0 )); then
  echo "[FAIL] typed product code depends on legacy manifest.yaml projection:" >&2
  printf '  - %s\n' "${offenders[@]}" >&2
  exit 1
fi

# The migrated taxonomy contract must stay JSON-only even if the compatibility
# projection is absent.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cp "$ROOT/manifest.json" "$TMP_DIR/manifest.json"
python3 -m agent_dev_kit.asset_taxonomy_contract --root "$TMP_DIR" --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["source"]=="manifest.json"'

echo "[PASS] typed manifest consumers stay on canonical JSON"
