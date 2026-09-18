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
grep -q '"context_governance_assets":11' "$OUT_FILE" || {
  echo "[FAIL] token context governance assets not counted" >&2
  exit 1
}
grep -q '"failures":0' "$OUT_FILE" || {
  echo "[FAIL] token context governance fixture gate reported failures" >&2
  exit 1
}

python3 - "$ROOT_DIR/manifests/token_context_policy.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
assert data["schema"] == "adk-token-context-policy/v1", data
assert data["status"] == "active", data
assert data["scope"] == "all-profiles-all-workflows", data
assert data["default_mode"] == "balanced", data
assert set(data["modes"]) == {"fast", "balanced", "precision", "audit"}, data
assert data["modes"]["audit"]["default_read_tiers"] == ["L3"], data
assert data["modes"]["audit"]["compress_readonly"] is False, data
invariants = data["invariants"]
for key in (
    "progressive_disclosure",
    "deferred_tool_skill_loading",
    "stable_context_prefix_first",
    "dynamic_context_last",
    "bounded_summary_first",
    "full_evidence_retained",
    "raw_evidence_required",
    "high_risk_raw_read",
    "mutation_review_never_replaced_by_compression",
):
    assert invariants[key] is True, (key, data)
assert invariants["high_risk_mode"] == "audit", data
assert invariants["usage_fields"] == [
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "total_tokens",
], data
overlay = data["low_token_overlay"]
assert overlay["asset_profile"] is False, data
assert overlay["mode"] == "fast", data
assert "high-risk" in overlay["restore_on"], data
assert "low-confidence" in overlay["restore_on"], data
PY

for file in \
  "$ROOT_DIR/AGENTS.md" \
  "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" \
  "$ROOT_DIR/templates/context/low-token-profile.md"; do
  grep -q 'balanced' "$file" || {
    echo "[FAIL] balanced baseline missing from ${file#$ROOT_DIR/}" >&2
    exit 1
  }
done

grep -Eq 'Low Token.*runtime overlay|Low Token.*runtime.*overlay' "$ROOT_DIR/AGENTS.md" || {
  echo "[FAIL] root AGENTS must define Low Token as runtime overlay" >&2
  exit 1
}
grep -q 'not.*manifest asset profile' "$ROOT_DIR/templates/context/low-token-profile.md" || {
  echo "[FAIL] low-token template must not masquerade as an asset profile" >&2
  exit 1
}
grep -q 'cached_tokens' "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" || {
  echo "[FAIL] token governance must account for cached tokens" >&2
  exit 1
}

bash "$ROOT_DIR/scripts/devkit.sh" match \
  --skill adk-token-context-governance \
  --text "日志太长，需要压缩输出并保留 raw_evidence 后按需回退原文" >/dev/null

bash "$ROOT_DIR/scripts/devkit.sh" match \
  --skill adk-token-context-governance \
  --text "token lean 模式下按预算读取，低置信度时恢复原文" >/dev/null

if bash "$ROOT_DIR/scripts/devkit.sh" match \
  --skill adk-token-context-governance \
  --text "高风险审计要求直接看原文" >/tmp/adk_token_context_negative.out 2>&1; then
  echo "[FAIL] high-risk raw-read request should not trigger compression governance" >&2
  exit 1
fi

ROUTER="$ROOT_DIR/skills/adk-runtime-router/SKILL.md"
ROUTER_REF="$ROOT_DIR/skills/adk-runtime-router/references/runtime-routing-details.md"
[[ -s "$ROUTER_REF" ]] || {
  echo "[FAIL] runtime-router progressive-disclosure reference missing" >&2
  exit 1
}
router_bytes="$(wc -c <"$ROUTER" | tr -d ' ')"
[[ "$router_bytes" -le 5600 ]] || {
  echo "[FAIL] runtime-router entry exceeds 5600-byte ratchet: $router_bytes" >&2
  exit 1
}
search_path='~/co'
search_path+='dex/scripts/skill-search.sh'
for marker in \
  '## Prerequisites' '## Workflow' '## Commands' '## Quality Gate' \
  'skill-catalog-lazy-loading-v1' 'namespace_summary' 'deferred_surface' \
  'loaded_tools' 'schema_review' 'code_intelligence_provider_contract' \
  'Tool / Skill Evidence Plan' 'primary' 'supporting' 'fallback' 'verification' \
  'Skipped Skills' 'Fallback Evidence' 'L1' 'L2' 'L3' 'raw' "$search_path"; do
  grep -Fq -- "$marker" "$ROUTER" || {
    echo "[FAIL] runtime-router entry lost required marker: $marker" >&2
    exit 1
  }
done
for marker in 'Task Routing' 'Tool Routing' 'Rationalization Guard' 'no match' 'ambiguous' 'retrieval failed' 'Best Tool for Task'; do
  grep -Fq -- "$marker" "$ROUTER_REF" || {
    echo "[FAIL] runtime-router reference lost required detail: $marker" >&2
    exit 1
  }
done
forbidden='--profile token-'
forbidden+='lean'
if grep -Fq -- "$forbidden" "$ROUTER" "$ROUTER_REF"; then
  echo "[FAIL] retired low-context selector returned to runtime-router" >&2
  exit 1
fi

echo "[PASS] token context governance"
