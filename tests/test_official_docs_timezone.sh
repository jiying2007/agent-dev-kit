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
governance_tz = dt.timezone(dt.timedelta(hours=8))
expected = dt.datetime.now(governance_tz).date().isoformat()
expected_basis = "fixed_utc_offset:+08:00;label=Asia/Hong_Kong"
assert east["evaluated_at"] == expected, east
assert west["evaluated_at"] == expected, west
assert east["date_basis"] == west["date_basis"] == expected_basis, (east, west)
PY

fixture_root="$TMP_DIR/future-root"
mkdir -p "$fixture_root"
cp -R \
  "$ROOT_DIR/scripts" \
  "$ROOT_DIR/manifests" \
  "$ROOT_DIR/docs" \
  "$ROOT_DIR/workflows" \
  "$ROOT_DIR/skills" \
  "$ROOT_DIR/optional-skills" \
  "$ROOT_DIR/agents" \
  "$fixture_root/"

python3 - "$fixture_root/manifests/official_docs_freshness_gates.json" <<'PY'
import datetime as dt
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
governance_tz = dt.timezone(dt.timedelta(hours=8))
future = dt.datetime.now(governance_tz).date() + dt.timedelta(days=1)
source = data["sources"][0]
source["retrieved_at"] = future.isoformat()
source["expires_at"] = (future + dt.timedelta(days=90)).isoformat()
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

if TZ=UTC "$fixture_root/scripts/check-official-docs-governance.sh" \
  >"$TMP_DIR/future.out" 2>"$TMP_DIR/future.err"; then
  echo "[FAIL] governance-relative future retrieved_at unexpectedly passed" >&2
  exit 1
fi
rg -q --fixed-strings -- "has future retrieved_at" "$TMP_DIR/future.err"

echo "[PASS] official docs freshness uses declared +08:00 date across host timezones and rejects future dates"
