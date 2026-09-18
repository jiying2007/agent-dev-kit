#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$ROOT_DIR/scripts/devkit.sh" skill-relationships --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass", d; assert d["schema"]=="adk-skill-relationship-resolution/v2", d; assert d["relationship_count"]==len(d["typed_relationships"]), d; assert d["delivery_lifecycle"]["status"]=="pass", d'

python3 - "$ROOT_DIR/manifest.json" <<'PY'
import json, sys
manifest=json.load(open(sys.argv[1], encoding="utf-8"))
for section in ("skills","optional_skills"):
    for item in manifest.get(section, []):
        assert "depends_on" not in item, item.get("name")
PY

echo "[PASS] Skill relationship v2 is the only dependency authority"
