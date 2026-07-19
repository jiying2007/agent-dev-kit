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
  echo "[FAIL] research-intake must require its optional absorption skill" >&2
  exit 1
fi
grep -q "missing skill in selected profiles: adk-external-practice-absorption" "$TMP_DIR/research-intake.out" || {
  echo "[FAIL] workflow closure failure did not explain the missing optional skill" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-workflow-closure.sh" \
  --profile research-intake \
  --with-optional-skill adk-external-practice-absorption >/dev/null

echo "[PASS] workflow closure"
