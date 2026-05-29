#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_FILE="$(mktemp)"
trap 'rm -f "$OUT_FILE"' EXIT

"$ROOT_DIR/scripts/check-token-budget.sh" --summary-json >"$OUT_FILE"
grep -q '"status":"pass"' "$OUT_FILE" || {
  echo "[FAIL] token context governance summary did not pass" >&2
  exit 1
}
grep -q '"context_governance_assets":8' "$OUT_FILE" || {
  echo "[FAIL] token context governance assets not counted" >&2
  exit 1
}

"$ROOT_DIR/scripts/skill-match.sh" \
  --skill adk-token-context-governance \
  --text "日志太长，需要压缩输出并保留 raw_evidence 后按需回退原文" >/dev/null

"$ROOT_DIR/scripts/skill-match.sh" \
  --skill adk-token-context-governance \
  --text "需要上下文预算，按审计模式读取原文证据" >/dev/null

if "$ROOT_DIR/scripts/skill-match.sh" \
  --skill adk-token-context-governance \
  --text "高风险审计要求直接看原文" >/tmp/adk_token_context_negative.out 2>&1; then
  echo "[FAIL] high-risk raw-read request should not trigger compression governance" >&2
  exit 1
fi

echo "[PASS] token context governance"
