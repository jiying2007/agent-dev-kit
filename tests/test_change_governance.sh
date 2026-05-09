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
bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR"

# 删除一个关键段落，校验脚本应失败
sed -i '/^## Spec 链路检查$/,/^## 安装范围与依赖边界$/d' "$CHANGE_DIR/proposal.md"
if bash "$ROOT_DIR/scripts/check-change-governance.sh" "$CHANGE_DIR" >/dev/null 2>&1; then
  echo "[FAIL] governance check should fail when required section is missing" >&2
  exit 1
fi

echo "[PASS] change governance"
