#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTEXT="$ROOT_DIR/CONTEXT.md"
MANIFEST_JSON="$ROOT_DIR/manifest.json"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

[[ -f "$CONTEXT" ]] || fail "CONTEXT.md missing"
[[ -f "$MANIFEST_JSON" ]] || fail "manifest.json missing"
[[ ! -e "$ROOT_DIR/manifest.yaml" ]] || fail "legacy Manifest YAML projection must be absent"

manifest_version="$(python3 - "$MANIFEST_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["version"])
PY
)"

grep -Fq "产品版本：${manifest_version}" "$CONTEXT" || fail "CONTEXT version drift: expected ${manifest_version}"
grep -Fq '结构化单一事实源：`manifest.json`' "$CONTEXT" || fail "CONTEXT must declare manifest.json as structured SSOT"
grep -Fq 'ADK 不再维护 Manifest 的 YAML 镜像' "$CONTEXT" || fail "CONTEXT must declare the Manifest YAML projection retired"
grep -Fq 'ADK 不实现通用 LLM 推理循环或 session scheduler' "$CONTEXT" || fail "CONTEXT runtime boundary missing"
grep -Fq 'routing-ir/v2' "$CONTEXT" || fail "CONTEXT routing IR version missing"
grep -Fq 'Session 临时状态不是长期知识' "$CONTEXT" || fail "CONTEXT session/knowledge boundary missing"
grep -Fq '历史变更文档允许出现被移除的外部仓' "$CONTEXT" || fail "CONTEXT provenance boundary missing"

for legacy in \
  '单一事实源：`manifest.yaml`' \
  '结构化单一事实源：`manifest.yaml`' \
  '位置：`manifest.yaml`' \
  '位置: `manifest.yaml`' \
  '`manifest.yaml` 只作为兼容镜像'; do
  if grep -Fq "$legacy" "$CONTEXT"; then
    fail "CONTEXT contains retired Manifest wording: $legacy"
  fi
done

for term in Agent Skill Profile Workflow Artifact Gate Evidence Receipt Routing; do
  grep -Fq "$term" "$CONTEXT" || fail "CONTEXT missing core term: $term"
done

echo "[PASS] CONTEXT.md semantic contract matches canonical manifest.json"
