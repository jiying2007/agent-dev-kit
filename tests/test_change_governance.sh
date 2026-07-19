#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHANGE_ROOT="$TMP_DIR/changes"
CHANGE_ID="governance-smoke"
CHANGE_DIR="$CHANGE_ROOT/$CHANGE_ID"

"$ROOT_DIR/scripts/workflow.sh" propose --change "$CHANGE_ID" --title "governance smoke" --root "$CHANGE_ROOT"

if bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR" >/dev/null 2>&1; then
  echo "[FAIL] governance check should fail while negative-results has no evidence rows" >&2
  exit 1
fi

cat > "$CHANGE_DIR/negative-results.md" <<'NEGATIVE'
# 负结果记录：governance-smoke

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| T1 | 仅检查章节即可放行 | 运行 check-change-governance 默认模板 | 失败 | 缺少真实负结果和命令证据 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| scripts/check-change-governance.sh default-template | 1 | blocked missing evidence rows | negative-results.md | Workflow | negative-results |
NEGATIVE

bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR"

# 完成态 checklist 仍应通过；门禁约束字段存在性，不应强制保持未勾选。
sed -i 's/^- \[ \] Prompt before\/after 对比证据$/- [x] Prompt before\/after 对比证据/' "$CHANGE_DIR/checklist.md"
sed -i 's/^- \[ \] Evidence Index 命令级字段完整/- [x] Evidence Index 命令级字段完整/' "$CHANGE_DIR/checklist.md"
bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR"

# 标签本身仍是合同；改名后必须失败。
sed -i 's/Prompt before\/after 对比证据/Prompt regression evidence/' "$CHANGE_DIR/checklist.md"
if bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR" >/dev/null 2>&1; then
  echo "[FAIL] governance check should fail when checklist contract label changes" >&2
  exit 1
fi
sed -i 's/Prompt regression evidence/Prompt before\/after 对比证据/' "$CHANGE_DIR/checklist.md"

# 删除一个关键段落，校验脚本应失败
sed -i '/^## Spec 链路检查$/,/^## 安装范围与依赖边界$/d' "$CHANGE_DIR/proposal.md"
if bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR" >/dev/null 2>&1; then
  echo "[FAIL] governance check should fail when required section is missing" >&2
  exit 1
fi

echo "[PASS] change governance"
