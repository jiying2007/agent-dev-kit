#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

[[ ! -e "$ROOT/manifest.yaml" ]] || {
  echo "[FAIL] legacy manifest.yaml must not exist" >&2
  exit 1
}

python3 - <<'PY'
from agent_dev_kit import manifest_contract
from agent_dev_kit.domain import manifest as manifest_domain

for name in ("ManifestContract", "canonical_manifest", "load_canonical_manifest", "load_contract"):
    assert hasattr(manifest_domain, name), name
    assert not hasattr(manifest_contract, name), name
assert hasattr(manifest_contract, "main")
PY

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
assert all("depends_on" not in item for section in ("skills", "optional_skills") for item in manifest.get(section, []))
assert "L2-phase-triggered" not in manifest["context_layers"]
assert "L2-phase-triggered" not in manifest["embedded_context_layers"]
PY

python3 - "$ROOT/manifests/manifest.schema.json" "$ROOT/manifest.json" <<'PY'
import copy
import json
import sys
from jsonschema import Draft202012Validator

schema=json.load(open(sys.argv[1], encoding="utf-8"))
manifest=json.load(open(sys.argv[2], encoding="utf-8"))
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(manifest)

probe=copy.deepcopy(manifest)
probe["context_layers"]["L2-phase-triggered"]={
    "description":"retired phase path mirror",
    "triggers":{"review":["skills/adk-code-review-loop/"]},
}
errors=list(Draft202012Validator(schema).iter_errors(probe))
assert errors, "manifest schema accepted retired phase trigger mirror"
PY

python3 - <<'PY'
import tempfile
from pathlib import Path
from agent_dev_kit.domain.manifest import load_canonical_manifest

# Alternative consumers must not silently accept ambiguous canonical data.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    document = root / "manifest.json"
    for raw in (
        '{"version":"11.4.11","version":"forged","schema_version":1,"product":{}}',
        '{"version":"11.4.11","schema_version":1,"product":{"kind":"safe","kind":"forged"}}',
        '{"version":"11.4.11","schema_version":NaN,"product":{}}',
    ):
        document.write_text(raw, encoding="utf-8")
        try:
            load_canonical_manifest(root)
        except ValueError:
            pass
        else:
            raise AssertionError("canonical manifest accepted unsafe ambiguous JSON")
    document.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    try:
        load_canonical_manifest(root)
    except ValueError:
        pass
    else:
        raise AssertionError("canonical manifest accepted an oversized JSON input")
PY

echo "[PASS] single Manifest SSOT contract"
python3 -m unittest discover -s "$ROOT/tests" -p test_manifest_validation_reuse.py
python3 -m unittest discover -s "$ROOT/tests" -p test_manifest_stream_consumers.py
