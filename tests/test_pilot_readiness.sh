#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_FILE="$(mktemp)"
trap 'rm -f "$OUT_FILE"' EXIT

"$ROOT_DIR/scripts/pilot-readiness.sh"

"$ROOT_DIR/scripts/pilot-readiness.sh" --pilot embedded-bugfix-systematic-debugging >"$OUT_FILE"
grep -q 'readiness=evidence-ready' "$OUT_FILE" || {
  echo "[FAIL] pilot filter did not report evidence-ready readiness" >&2
  exit 1
}

"$ROOT_DIR/scripts/pilot-readiness.sh" --summary-json >"$OUT_FILE"
grep -q '"status":"pass"' "$OUT_FILE" || {
  echo "[FAIL] pilot readiness summary json did not pass" >&2
  exit 1
}

if "$ROOT_DIR/scripts/pilot-readiness.sh" --pilot does-not-exist >/tmp/adk_pilot_missing.out 2>&1; then
  echo "[FAIL] missing pilot should fail" >&2
  exit 1
fi

echo "[PASS] pilot readiness"
