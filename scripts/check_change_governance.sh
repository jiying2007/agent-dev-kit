#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/check_change_governance.sh <change_dir>
USAGE
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

CHANGE_DIR="$1"

if [[ ! -d "${CHANGE_DIR}" ]]; then
  echo "[FAIL] change dir not found: ${CHANGE_DIR}" >&2
  exit 1
fi

require_file() {
  local file="$1"
  if [[ ! -f "${CHANGE_DIR}/${file}" ]]; then
    echo "[FAIL] missing required artifact: ${CHANGE_DIR}/${file}" >&2
    exit 1
  fi
}

require_section() {
  local file="$1"
  local section="$2"
  if ! rg -q --fixed-strings -- "${section}" "${CHANGE_DIR}/${file}"; then
    echo "[FAIL] ${file} missing section: ${section}" >&2
    exit 1
  fi
}

require_line() {
  local file="$1"
  local line="$2"
  if ! rg -q --fixed-strings -- "${line}" "${CHANGE_DIR}/${file}"; then
    echo "[FAIL] ${file} missing line: ${line}" >&2
    exit 1
  fi
}

require_file "proposal.md"
require_file "design.md"
require_file "tasks.md"
require_file "checklist.md"
require_file "negative-results.md"

require_section "proposal.md" "## 问题陈述（单问题）"
require_section "proposal.md" "## 上下文充分性检查"
require_section "proposal.md" "## Core/Optional 边界检查"
require_section "proposal.md" "## 变更重复性检查"
require_section "proposal.md" "## Breaking Change 检查"
require_section "proposal.md" "## Spec 链路检查"
require_section "proposal.md" "## 安装范围与依赖边界"
require_section "proposal.md" "## Prompt 回归证据计划"
require_section "proposal.md" "## 收敛模式与退出条件"

require_section "tasks.md" "## Ownership 与并行冲突检查"
require_section "tasks.md" "## 轻量工件与收敛结论"

require_section "negative-results.md" "## 已验证的负结果"
require_section "negative-results.md" "## Evidence Index（命令级）"
require_line "negative-results.md" "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"

require_line "checklist.md" "- [ ] Prompt before/after 对比证据"
require_line "checklist.md" "- [ ] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）"
require_line "checklist.md" "- [ ] Skill Intake 归属与安装范围结论"
require_line "checklist.md" "- [ ] 收敛结论或阻塞说明"

echo "[PASS] change governance checks passed: ${CHANGE_DIR}"
