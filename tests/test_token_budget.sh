#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_FILE="$(mktemp)"
ROLE_OUT_FILE="$(mktemp)"
trap 'rm -f "$OUT_FILE" "$ROLE_OUT_FILE"' EXIT

"$ROOT_DIR/scripts/check-token-budget.sh"
"$ROOT_DIR/scripts/check-role-context-budget.sh"

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
grep -q '"agents_bytes":' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing agents_bytes" >&2
  exit 1
}
grep -q '"budget_status":"within-soft-limit"' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing soft-limit status" >&2
  exit 1
}
grep -q '"agents_estimated_tokens":' "$OUT_FILE" || {
  echo "[FAIL] token budget summary missing token estimate" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-role-context-budget.sh" --summary-json >"$ROLE_OUT_FILE"
grep -q '"status":"pass"' "$ROLE_OUT_FILE" || {
  echo "[FAIL] role context budget summary did not pass" >&2
  cat "$ROLE_OUT_FILE" >&2
  exit 1
}
grep -q '"role_agent_files":13' "$ROLE_OUT_FILE" || {
  echo "[FAIL] role context budget did not cover all 13 roles" >&2
  exit 1
}
for field in role_agents_bytes role_agents_limit role_agents_estimated_tokens max_role_agent_bytes max_role_agent_limit max_role_agent_file; do
  grep -q "\"${field}\":" "$ROLE_OUT_FILE" || {
    echo "[FAIL] role context budget summary missing ${field}" >&2
    exit 1
  }
done

if "$ROOT_DIR/scripts/check-token-budget.sh" --max-skill-lines 1 >/tmp/adk_token_budget_fail.out 2>&1; then
  echo "[FAIL] tiny skill line budget should fail" >&2
  exit 1
fi
if "$ROOT_DIR/scripts/check-role-context-budget.sh" --max-role-agent-bytes 1 >/tmp/adk_role_context_file_fail.out 2>&1; then
  echo "[FAIL] tiny per-role context budget should fail" >&2
  exit 1
fi
if "$ROOT_DIR/scripts/check-role-context-budget.sh" --max-role-agents-bytes 1 >/tmp/adk_role_context_total_fail.out 2>&1; then
  echo "[FAIL] tiny aggregate role context budget should fail" >&2
  exit 1
fi

echo "[PASS] token budget"
