#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_FILE="$(mktemp)"
trap 'rm -f "$OUT_FILE"' EXIT

"$ROOT_DIR/scripts/check-token-budget.sh"

"$ROOT_DIR/scripts/check-token-budget.sh" --summary-json >"$OUT_FILE"
grep -q '"status":"pass"' "$OUT_FILE" || {
  echo "[FAIL] token budget summary did not pass" >&2
  exit 1
}
grep -q '"max_skill_lines":' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing max_skill_lines" >&2
  exit 1
}
grep -q '"max_doc_lines":' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing max_doc_lines" >&2
  exit 1
}
grep -q '"context_governance_assets":' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing context_governance_assets" >&2
  exit 1
}

if "$ROOT_DIR/scripts/check-token-budget.sh" --max-skill-lines 1 >/tmp/adk_token_budget_fail.out 2>&1; then
  echo "[FAIL] tiny skill line budget should fail" >&2
  exit 1
fi

echo "[PASS] token budget"
