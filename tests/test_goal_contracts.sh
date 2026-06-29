#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-goal-contracts.sh"
"$ROOT_DIR/scripts/check-goal-contracts.sh" --summary-json >"$TMP_DIR/goal-contracts.json"
rg -q '"status":"pass"' "$TMP_DIR/goal-contracts.json" || {
  echo "[FAIL] goal contract summary did not pass" >&2
  cat "$TMP_DIR/goal-contracts.json" >&2
  exit 1
}
rg -q '"goals":4' "$TMP_DIR/goal-contracts.json" || {
  echo "[FAIL] goal contract summary did not count expected goals" >&2
  cat "$TMP_DIR/goal-contracts.json" >&2
  exit 1
}

echo "[PASS] goal contracts"
