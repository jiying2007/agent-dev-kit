#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if ! python3 -m agent_dev_kit.manifest_contract --root "$ROOT" --summary-json >"$TMP"; then
  cat "$TMP" >&2
  exit 1
fi
python3 - "$TMP" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["status"] == "pass", data
assert data["canonical"] == "manifest.json", data
assert data["compatibility_mirror"] == "manifest.yaml", data
assert data["version"] == "5.0.0-rc.2", data
PY

echo "[PASS] manifest SSOT compatibility contract"
