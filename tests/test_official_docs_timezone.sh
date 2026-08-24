#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TZ=Pacific/Kiritimati "$ROOT_DIR/scripts/check-official-docs-governance.sh" --summary-json >"$TMP_DIR/east.json" || true
TZ=America/Adak "$ROOT_DIR/scripts/check-official-docs-governance.sh" --summary-json >"$TMP_DIR/west.json" || true

python3 - "$TMP_DIR/east.json" "$TMP_DIR/west.json" <<'PY'
import datetime as dt
import json
import pathlib
import sys

east = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
west = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
expected = dt.datetime.now(dt.timezone.utc).date().isoformat()
assert east["evaluated_at"] == expected, east
assert west["evaluated_at"] == expected, west
assert east["date_basis"] == west["date_basis"] == "utc", (east, west)
PY

echo "[PASS] official docs freshness uses one UTC date across host timezones"
