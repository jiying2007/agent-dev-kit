#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

[[ ! -e "$ROOT/manifest.yaml" ]] || {
  echo "[FAIL] legacy manifest.yaml must not exist" >&2
  exit 1
}

if ! python3 -m agent_dev_kit.manifest_contract --root "$ROOT" --summary-json >"$TMP"; then
  cat "$TMP" >&2
  exit 1
fi
python3 - "$TMP" "$ROOT/manifest.json" <<'PY'
import json
import re
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["schema"] == "adk-manifest-contract/v3", data
assert data["status"] == "pass", data
assert data["canonical"] == "manifest.json", data
assert data["legacy_projection_absent"] is True, data
assert re.fullmatch(r"[0-9a-f]{64}", data["canonical_sha256"]), data
with open(sys.argv[2], encoding="utf-8") as handle:
    manifest = json.load(handle)
assert data["version"] == manifest["version"], data
PY

echo "[PASS] single Manifest SSOT contract"
