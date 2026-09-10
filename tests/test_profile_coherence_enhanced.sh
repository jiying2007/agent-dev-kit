#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

[[ -f "$ROOT_DIR/manifest.json" ]] || {
  echo "[FAIL] manifest.json missing" >&2
  exit 1
}
[[ ! -e "$ROOT_DIR/manifest.yaml" ]] || {
  echo "[FAIL] legacy Manifest YAML projection must be absent" >&2
  exit 1
}

python3 - "$ROOT_DIR/manifest.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert isinstance(data.get("profiles"), dict) and data["profiles"], data
assert isinstance(data.get("default_profile"), str) and data["default_profile"] in data["profiles"], data
assert isinstance(data.get("agents"), list) and data["agents"], data
assert isinstance(data.get("skills"), list) and data["skills"], data
PY

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m agent_dev_kit.profile_coherence_contract --root "$ROOT_DIR" --summary-json >"$TMP"
python3 - "$TMP" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["schema"] == "adk-profile-coherence/v2", data
assert data["status"] == "pass", data
assert data["source"] == "manifest.json", data
assert data["profiles"] > 0, data
PY

echo "[PASS] profile coherence uses canonical manifest.json"
