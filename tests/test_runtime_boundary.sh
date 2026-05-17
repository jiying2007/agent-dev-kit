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
echo "$summary" | grep -q '"codex_root":"~/codex"' || {
  echo "[FAIL] runtime boundary summary missing codex root" >&2
  exit 1
}

if "$ROOT_DIR/scripts/sync-codex-assets.sh" >"$TMP_DIR/sync-codex-assets.out" 2>&1; then
  echo "[FAIL] retired sync-codex-assets should fail" >&2
  exit 1
fi
grep -q "has been retired" "$TMP_DIR/sync-codex-assets.out" || {
  echo "[FAIL] retired sync-codex-assets message missing" >&2
  exit 1
}

echo "[PASS] runtime boundary"
