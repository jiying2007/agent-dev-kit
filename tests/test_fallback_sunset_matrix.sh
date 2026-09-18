#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ ! -e "$ROOT/scripts/check-fallback-sunset.sh" ]] || {
  echo "[FAIL] retired fallback tombstone script returned" >&2
  exit 1
}

python3 - "$ROOT/docs/reference/fallback-sunset-matrix.tsv" "$ROOT/docs/reference/fallback-sunset-matrix.md" <<'PY'
import csv
import sys
from pathlib import Path

tsv = Path(sys.argv[1])
md = Path(sys.argv[2])
rows = list(csv.DictReader(tsv.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
assert len(rows) == 1, rows
row = rows[0]
assert row["status"] == "retired", row
assert row["compatibility_enabled"] == "false", row
assert row["replacement"] == "ADK-native-routing-and-runtime-footprint", row
text = md.read_text(encoding="utf-8")
assert "已于 2026-08-31 退役" in text
assert "不再提供 Superpowers runtime fallback" in text
PY

echo "[PASS] fallback remains retired without an executable tombstone"
