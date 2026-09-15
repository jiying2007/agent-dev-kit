#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-change-governance.sh <change_dir>
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

require_check_item() {
  local file="$1"
  local item="$2"
  if ! awk -v item="${item}" '
    /^- \[[ xX]\] / {
      line = $0
      sub(/^- \[[ xX]\] /, "", line)
      if (line == item) found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "${CHANGE_DIR}/${file}"; then
    echo "[FAIL] ${file} missing checklist item: ${item}" >&2
    exit 1
  fi
}

reject_placeholder_text() {
  local file="$1"
  local pattern='待补充|未定义|TODO|TBD|FIXME|PLACEHOLDER|占位|<[^>]+>'
  if rg -n -- "${pattern}" "${CHANGE_DIR}/${file}" >&2; then
    echo "[FAIL] ${file} contains placeholder text" >&2
    exit 1
  fi
}

require_table_data_row_after_section() {
  local file="$1"
  local section="$2"
  if ! awk -v section="$section" '
    $0 == section { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section && /^\|/ {
      if ($0 ~ /^\|[[:space:]]*-+/) next
      if ($0 ~ /^\|[[:space:]]*(时间|Command)[[:space:]]*\|/) next
      row = $0
      gsub(/[|[:space:]-]/, "", row)
      if (row != "") found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "${CHANGE_DIR}/${file}"; then
    echo "[FAIL] ${file} missing data row after section: ${section}" >&2
    exit 1
  fi
}

validate_canonical_change_contract() {
  local proposal="${CHANGE_DIR}/proposal.md"
  local tasks="${CHANGE_DIR}/tasks.md"
  local task_id

  require_line "proposal.md" "| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |"

  if ! awk -F'|' '
    function trim(value) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      return value
    }
    $0 == "## Canonical Change Contract" { in_contract = 1; next }
    in_contract && /^## / { in_contract = 0 }
    in_contract && /^\|/ {
      req = trim($2)
      if (req == "Requirement ID" || req ~ /^-+$/ || req == "") next
      requirement = trim($3)
      operation = trim($4)
      target = trim($5)
      surface = trim($6)
      acceptance = trim($7)
      criterion = trim($8)
      task = trim($9)
      verification = trim($10)
      evidence = trim($11)

      if (req !~ /^REQ-[0-9][0-9][0-9]+$/) exit 11
      if (acceptance !~ /^ACC-[0-9][0-9][0-9]+$/) exit 12
      if (task !~ /^TASK-[0-9][0-9][0-9]+$/) exit 13
      if (verification !~ /^VERIFY-[0-9][0-9][0-9]+$/) exit 14
      if (operation != "ADDED" && operation != "MODIFIED" && operation != "REMOVED") exit 15
      if (requirement == "" || target == "" || surface == "" || criterion == "" || evidence == "") exit 16
      rows += 1
    }
    END { if (rows < 1) exit 20 }
  ' "$proposal"; then
    echo "[FAIL] proposal.md Canonical Change Contract row is invalid" >&2
    exit 1
  fi

  while IFS= read -r task_id; do
    [[ -n "$task_id" ]] || continue
    if ! rg -q --fixed-strings -- "$task_id" "$tasks"; then
      echo "[FAIL] tasks.md missing task referenced by Canonical Change Contract: $task_id" >&2
      exit 1
    fi
  done < <(rg -o 'TASK-[0-9]{3,}' "$proposal" | sort -u)
}

validate_verification_traceability_if_present() {
  local proposal="${CHANGE_DIR}/proposal.md"
  local report="${CHANGE_DIR}/verify-report.md"
  local verification_id

  [[ -f "$report" ]] || return 0
  while IFS= read -r verification_id; do
    [[ -n "$verification_id" ]] || continue
    if ! rg -q --fixed-strings -- "$verification_id" "$report"; then
      echo "[FAIL] verify-report.md missing verification referenced by Canonical Change Contract: $verification_id" >&2
      exit 1
    fi
  done < <(rg -o 'VERIFY-[0-9]{3,}' "$proposal" | sort -u)
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
require_section "proposal.md" "## Canonical Change Contract"
require_section "proposal.md" "## 安装范围与依赖边界"
require_section "proposal.md" "## Prompt 回归证据计划"
require_section "proposal.md" "## 收敛模式与退出条件"

require_section "tasks.md" "## Ownership 与并行冲突检查"
require_section "tasks.md" "## 轻量工件与收敛结论"

require_section "negative-results.md" "## 已验证的负结果"
require_section "negative-results.md" "## Evidence Index（命令级）"
require_line "negative-results.md" "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"
require_table_data_row_after_section "negative-results.md" "## 已验证的负结果"
require_table_data_row_after_section "negative-results.md" "## Evidence Index（命令级）"

require_check_item "checklist.md" "Prompt before/after 对比证据"
require_check_item "checklist.md" "Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）"
require_check_item "checklist.md" "Canonical Change Contract 追溯关系完整"
require_check_item "checklist.md" "Skill Intake 归属与安装范围结论"
require_check_item "checklist.md" "收敛结论或阻塞说明"

validate_canonical_change_contract
validate_verification_traceability_if_present

reject_placeholder_text "proposal.md"
reject_placeholder_text "design.md"
reject_placeholder_text "tasks.md"
reject_placeholder_text "checklist.md"
reject_placeholder_text "negative-results.md"

echo "[PASS] change governance checks passed: ${CHANGE_DIR}"
