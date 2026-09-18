#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

MANIFEST_BEFORE="$(sha256sum "$ROOT/manifest.json" | awk '{print $1}')"
POLICY_BEFORE="$(sha256sum "$ROOT/manifests/manifest_composition_policy.json" | awk '{print $1}')"

REPORT="$(bash "$ROOT/scripts/devkit.sh" manifest composition-check --summary-json)"
python3 - "$REPORT" <<'PY'
import json
import sys

value = json.loads(sys.argv[1])
assert value["schema"] == "adk-manifest-composition-check/v1", value
assert value["status"] == "pass", value
assert value["canonical_source"] == "manifest.json", value
assert value["source_digest"] == value["round_trip_digest"], value
assert value["owner_domain_count"] > 0, value
assert value["reference_composer_mode"] == "pure-in-memory-only", value
assert value["runtime_enabled"] is False, value
assert value["writes"] is False, value
assert value["composition_generator"] is None, value
PY

[[ "$(sha256sum "$ROOT/manifest.json" | awk '{print $1}')" == "$MANIFEST_BEFORE" ]] || {
  echo "[FAIL] composition-check modified manifest.json" >&2
  exit 1
}
[[ "$(sha256sum "$ROOT/manifests/manifest_composition_policy.json" | awk '{print $1}')" == "$POLICY_BEFORE" ]] || {
  echo "[FAIL] composition-check modified composition policy" >&2
  exit 1
}

bash "$ROOT/scripts/devkit.sh" help | grep -q '^  manifest ' || {
  echo "[FAIL] manifest command missing from public CLI help" >&2
  exit 1
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$TMP_DIR/manifests"
cp "$ROOT/manifest.json" "$TMP_DIR/manifest.json"
cp "$ROOT/manifests/manifest.schema.json" "$TMP_DIR/manifests/manifest.schema.json"
cp "$ROOT/manifests/manifest_composition_policy.json" "$TMP_DIR/manifests/manifest_composition_policy.json"

python3 - "$TMP_DIR/manifests/manifest_composition_policy.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
value["reference_composer"]["runtime_enabled"] = True
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
if ADK_ROOT="$TMP_DIR" PYTHONPATH="$ROOT/src" python3 -m agent_dev_kit.cli \
  manifest composition-check --summary-json >"$TMP_DIR/runtime-enabled.json" 2>"$TMP_DIR/runtime-enabled.err"; then
  echo "[FAIL] composition-check accepted runtime-enabled reference composer" >&2
  exit 1
fi
python3 - "$TMP_DIR/runtime-enabled.json" <<'PY'
import json
import sys
from pathlib import Path

value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert value["status"] == "fail", value
assert any("runtime_enabled" in item for item in value["failures"]), value
PY

cp "$ROOT/manifests/manifest_composition_policy.json" "$TMP_DIR/manifests/manifest_composition_policy.json"
python3 - "$TMP_DIR/manifests/manifest_composition_policy.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
value["section_owners"].pop("version")
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
if ADK_ROOT="$TMP_DIR" PYTHONPATH="$ROOT/src" python3 -m agent_dev_kit.cli \
  manifest composition-check --summary-json >"$TMP_DIR/unowned.json" 2>"$TMP_DIR/unowned.err"; then
  echo "[FAIL] composition-check accepted unowned canonical section" >&2
  exit 1
fi
python3 - "$TMP_DIR/unowned.json" <<'PY'
import json
import sys
from pathlib import Path

value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert value["status"] == "fail", value
assert any("unowned sections" in item for item in value["failures"]), value
PY

echo '[PASS] manifest composition CLI is read-only and fail-closed'
