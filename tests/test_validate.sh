#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "${ADK_TEST_SUITE_MODE:-full}" == "quick" ]]; then
  summary="$(bash "$ROOT_DIR/scripts/devkit.sh" validate --quick --summary-json)"
else
  bash "$ROOT_DIR/scripts/devkit.sh" validate --quick
  summary="$(bash "$ROOT_DIR/scripts/devkit.sh" validate --strict --summary-json)"
fi
if [[ -n "${ADK_TEST_SUITE_DIR:-}" ]]; then
  printf '%s\n' "$summary" >"${ADK_TEST_SUITE_DIR}/validate-summary.json"
fi
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] validate summary did not pass" >&2
  exit 1
}
echo "$summary" | grep -q '"change_sets":1' || {
  echo "[FAIL] validate summary missing change set count" >&2
  exit 1
}

[[ ! -e "$ROOT_DIR/scripts/validate-assets.sh" ]] || { echo "[FAIL] retired validate-assets.sh returned" >&2; exit 1; }

echo "[PASS] validate"
