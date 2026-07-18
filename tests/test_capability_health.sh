#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-capability-health.sh"
"$ROOT_DIR/scripts/check-capability-health.sh" --summary-json >"$TMP_DIR/capability-health.json"
rg -q '"status":"pass"' "$TMP_DIR/capability-health.json" || {
  echo "[FAIL] capability health summary did not pass" >&2
  cat "$TMP_DIR/capability-health.json" >&2
  exit 1
}
rg -q '"capabilities":8' "$TMP_DIR/capability-health.json" || {
  echo "[FAIL] capability health summary did not count expected capabilities" >&2
  cat "$TMP_DIR/capability-health.json" >&2
  exit 1
}

echo "[PASS] capability health"
