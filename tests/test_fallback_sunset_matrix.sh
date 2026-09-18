#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ ! -e "$ROOT/scripts/check-fallback-sunset.sh" ]] || {
  echo "[FAIL] retired fallback sunset tombstone returned" >&2
  exit 1
}

python3 - "$ROOT/docs/reference/fallback-sunset-matrix.tsv" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
assert len(rows) == 1, rows
row = rows[0]
assert row["schema_version"] == "2", row
assert row["status"] == "retired", row
assert row["compatibility_enabled"] == "false", row
assert row["replacement"] == "ADK-native-routing-and-runtime-footprint", row
PY

echo "[PASS] fallback compatibility remains retired without an executable tombstone"
