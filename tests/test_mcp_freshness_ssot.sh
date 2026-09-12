#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER="$ROOT/tools/control_plane/mcp_freshness_ssot.py"

python3 "$CHECKER" --root "$ROOT" --as-of 2026-09-12 --summary-json | grep -q '"status":"pass"'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/manifests"
cp "$ROOT/manifests/skill_mcp_dependencies.json" "$TMP/manifests/"
cp "$ROOT/manifests/official_docs_freshness_gates.json" "$TMP/manifests/"
cp "$ROOT/manifests/external_agent_pattern_contracts.json" "$TMP/manifests/"

python3 - "$TMP/manifests/skill_mcp_dependencies.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
v = json.loads(p.read_text())
v["dependencies"][0]["provenance"]["expires_at"] = "2026-08-13"
p.write_text(json.dumps(v, indent=2) + "\n")
PY
if python3 "$CHECKER" --root "$TMP" --as-of 2026-09-12 --summary-json >/dev/null; then
  echo '[FAIL] divergent compatibility snapshot unexpectedly passed' >&2
  exit 1
fi

cp "$ROOT/manifests/skill_mcp_dependencies.json" "$TMP/manifests/skill_mcp_dependencies.json"
python3 - "$TMP/manifests/skill_mcp_dependencies.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
v = json.loads(p.read_text())
v["dependencies"][0]["provenance"]["review_source_ref"] = "missing-source"
p.write_text(json.dumps(v, indent=2) + "\n")
PY
if python3 "$CHECKER" --root "$TMP" --as-of 2026-09-12 --summary-json >/dev/null; then
  echo '[FAIL] unresolved canonical source unexpectedly passed' >&2
  exit 1
fi

cp "$ROOT/manifests/skill_mcp_dependencies.json" "$TMP/manifests/skill_mcp_dependencies.json"
python3 - "$TMP/manifests/skill_mcp_dependencies.json" "$TMP/manifests/official_docs_freshness_gates.json" "$TMP/manifests/external_agent_pattern_contracts.json" <<'PY'
import json
import sys
from pathlib import Path
manifest_path, official_path, external_path = map(Path, sys.argv[1:])
v = json.loads(manifest_path.read_text())
official = json.loads(official_path.read_text())
external = json.loads(external_path.read_text())
official_ids = {row["id"] for row in official["sources"]}
external_ids = {row["id"] for row in external["source_refs"]}
ambiguous = sorted(official_ids & external_ids)
assert ambiguous, "fixture requires at least one pre-existing cross-registry overlap"
v["dependencies"][0]["provenance"]["review_source_ref"] = ambiguous[0]
manifest_path.write_text(json.dumps(v, indent=2) + "\n")
PY
if python3 "$CHECKER" --root "$TMP" --as-of 2026-09-12 --summary-json >/dev/null; then
  echo '[FAIL] ambiguous referenced canonical source unexpectedly passed' >&2
  exit 1
fi

cp "$ROOT/manifests/skill_mcp_dependencies.json" "$TMP/manifests/skill_mcp_dependencies.json"
python3 - "$TMP/manifests/official_docs_freshness_gates.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
v = json.loads(p.read_text())
for row in v["sources"]:
    if row["id"] == "openai-docs-mcp-quickstart":
        row["expires_at"] = "2026-09-11"
p.write_text(json.dumps(v, indent=2) + "\n")
PY
if python3 "$CHECKER" --root "$TMP" --as-of 2026-09-12 --summary-json >/dev/null; then
  echo '[FAIL] expired canonical source unexpectedly passed' >&2
  exit 1
fi

echo '[PASS] MCP dependency freshness has a single canonical authority'
