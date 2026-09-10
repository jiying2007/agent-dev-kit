#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTEXT="$ROOT_DIR/CONTEXT.md"
MANIFEST_JSON="$ROOT_DIR/manifest.json"
MANIFEST_YAML="$ROOT_DIR/manifest.yaml"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

[[ -f "$CONTEXT" ]] || fail "CONTEXT.md missing"
[[ -f "$MANIFEST_JSON" ]] || fail "manifest.json missing"
[[ -f "$MANIFEST_YAML" ]] || fail "manifest.yaml compatibility mirror missing"

manifest_version="$(python3 - "$MANIFEST_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["version"])
PY
)"

# 结构存在性之外，必须验证会影响 Agent 行为的关键语义。
grep -Fq "产品版本：${manifest_version}" "$CONTEXT" || fail "CONTEXT version drift: expected ${manifest_version}"
grep -Fq '结构化单一事实源：`manifest.json`' "$CONTEXT" || fail "CONTEXT must declare manifest.json as structured SSOT"
grep -Fq '`manifest.yaml` 只作为兼容镜像' "$CONTEXT" || fail "CONTEXT must classify manifest.yaml as compatibility mirror"
grep -Fq 'ADK 不实现通用 LLM 推理循环或 session scheduler' "$CONTEXT" || fail "CONTEXT runtime boundary missing"
grep -Fq 'routing-ir/v2' "$CONTEXT" || fail "CONTEXT routing IR version missing"
grep -Fq 'Session 临时状态不是长期知识' "$CONTEXT" || fail "CONTEXT session/knowledge boundary missing"
grep -Fq '历史变更文档允许出现被移除的外部仓' "$CONTEXT" || fail "CONTEXT provenance boundary missing"

# 防止旧 SSOT 文案再次回流。
if grep -Eq '单一事实源[^\n]*manifest\.yaml|位置:[[:space:]]*`manifest\.yaml`' "$CONTEXT"; then
  fail "CONTEXT contains legacy manifest.yaml SSOT wording"
fi

# 核心概念仍需可导航。
for term in Agent Skill Profile Workflow Artifact Gate Evidence Receipt Routing; do
  grep -Fq "$term" "$CONTEXT" || fail "CONTEXT missing core term: $term"
done

echo "[PASS] CONTEXT.md semantic contract matches manifest.json and current runtime boundary"
