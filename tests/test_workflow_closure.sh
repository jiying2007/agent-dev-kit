#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-workflow-closure.sh" --profile core

summary="$("$ROOT_DIR/scripts/check-workflow-closure.sh" --profile core --summary-json)"
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] workflow closure summary did not pass" >&2
  exit 1
}

if "$ROOT_DIR/scripts/check-workflow-closure.sh" --profile research-intake >"$TMP_DIR/research-intake.out" 2>&1; then
  echo "[FAIL] research-intake should not satisfy global workflow closure" >&2
  exit 1
fi
grep -q "found no workflows" "$TMP_DIR/research-intake.out" || {
  echo "[FAIL] workflow closure failure did not explain missing workflow contract" >&2
  exit 1
}

echo "[PASS] workflow closure"
