#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-runtime-boundary.sh"

summary="$("$ROOT_DIR/scripts/check-runtime-boundary.sh" --summary-json)"
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] runtime boundary summary did not pass" >&2
  exit 1
}
echo "$summary" | grep -q '"runtime_scope":"generic-adk"' || {
  echo "[FAIL] runtime boundary summary missing generic scope" >&2
  exit 1
}

echo "[PASS] runtime boundary"
