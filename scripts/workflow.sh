#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/workflow.sh <propose|apply|verify|review|archive> [options]

Options:
  --change <change-id>   # kebab-case
  --title <title>        # propose 必填
  --result <pass|needs-fix>   # review 必填
  --blockers <n>         # review 可选，默认 0
  --majors <n>           # review 可选，默认 0
  --minors <n>           # review 可选，默认 0
  --owner <owner>
  --root <change-root>   # 默认 docs/changes
  --notes <text>
  --force                # archive 时忽略状态校验（高风险）
  -h, --help

Examples:
  ./scripts/workflow.sh propose --change modbus-tcp --title "接入 Modbus TCP"
  ./scripts/workflow.sh verify --change modbus-tcp
  ./scripts/workflow.sh review --change modbus-tcp --result pass --blockers 0 --majors 0 --minors 1
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

ACTION="$1"
shift

CHANGE_ID=""
TITLE=""
OWNER="${USER:-unknown}"
CHANGE_ROOT="$ROOT_DIR/docs/changes"
NOTES=""
FORCE=0
RESULT=""
BLOCKERS=0
MAJORS=0
MINORS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --change)
      CHANGE_ID="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --result)
      RESULT="$2"
      shift 2
      ;;
    --blockers)
      BLOCKERS="$2"
      shift 2
      ;;
    --majors)
      MAJORS="$2"
      shift 2
      ;;
    --minors)
      MINORS="$2"
      shift 2
      ;;
    --owner)
      OWNER="$2"
      shift 2
      ;;
    --root)
      CHANGE_ROOT="$2"
      shift 2
      ;;
    --notes)
      NOTES="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

ensure_change_id() {
  [[ -n "$CHANGE_ID" ]] || {
    echo "[FAIL] --change is required" >&2
    exit 1
  }

  [[ "$CHANGE_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || {
    echo "[FAIL] --change must be kebab-case" >&2
    exit 1
  }
}

ensure_non_negative_int() {
  local value="$1"
  local key="$2"
  [[ "$value" =~ ^[0-9]+$ ]] || {
    echo "[FAIL] $key must be a non-negative integer: $value" >&2
    exit 1
  }
}

current_stage() {
  local change_dir="$1"
  awk '/^stage:/ {print $2; exit}' "$change_dir/state.yaml" 2>/dev/null || true
}

require_stage() {
  local change_dir="$1"
  local expected="$2"
  local action="$3"
  local stage
  stage="$(current_stage "$change_dir")"
  [[ "$stage" == "$expected" ]] || {
    echo "[FAIL] $action requires stage '$expected', current: ${stage:-unknown}" >&2
    exit 1
  }
}

write_state() {
  local change_dir="$1"
  local stage="$2"

  {
    echo "stage: $stage"
    echo "owner: $OWNER"
    echo "updated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [[ -n "$NOTES" ]]; then
      echo "notes: $NOTES"
    fi
  } > "$change_dir/state.yaml"

  printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$stage" "$OWNER" >> "$change_dir/history.log"
}

run_verify_checks() {
  "$ROOT_DIR/scripts/validate_assets.sh" --strict
  "$ROOT_DIR/scripts/check_format.sh"
}

validate_change_artifacts() {
  local change_dir="$1"

  for file in proposal.md design.md tasks.md checklist.md negative-results.md; do
    [[ -f "$change_dir/$file" ]] || {
      echo "[FAIL] missing required artifact: $change_dir/$file" >&2
      return 1
    }
  done

  grep -q "^## 问题陈述（单问题）" "$change_dir/proposal.md" || {
    echo "[FAIL] proposal.md missing section: 问题陈述（单问题）" >&2
    return 1
  }

  grep -q "^## 上下文充分性检查" "$change_dir/proposal.md" || {
    echo "[FAIL] proposal.md missing section: 上下文充分性检查" >&2
    return 1
  }

  grep -q "^## Core/Optional 边界检查" "$change_dir/proposal.md" || {
    echo "[FAIL] proposal.md missing section: Core/Optional 边界检查" >&2
    return 1
  }

  grep -q "^## 变更重复性检查" "$change_dir/proposal.md" || {
    echo "[FAIL] proposal.md missing section: 变更重复性检查" >&2
    return 1
  }

  grep -q "^## Breaking Change 检查" "$change_dir/proposal.md" || {
    echo "[FAIL] proposal.md missing section: Breaking Change 检查" >&2
    return 1
  }

  grep -q "^## Ownership 与并行冲突检查" "$change_dir/tasks.md" || {
    echo "[FAIL] tasks.md missing section: Ownership 与并行冲突检查" >&2
    return 1
  }

  grep -q "^## 已验证的负结果" "$change_dir/negative-results.md" || {
    echo "[FAIL] negative-results.md missing section: 已验证的负结果" >&2
    return 1
  }
}

propose() {
  ensure_change_id
  [[ -n "$TITLE" ]] || {
    echo "[FAIL] --title is required for propose" >&2
    exit 1
  }

  local change_dir="$CHANGE_ROOT/$CHANGE_ID"
  if [[ -e "$change_dir" ]]; then
    echo "[FAIL] change already exists: $change_dir" >&2
    exit 1
  fi

  mkdir -p "$change_dir"

  cat > "$change_dir/proposal.md" <<PROPOSAL
# 变更提案：$CHANGE_ID

## 背景
- 说明当前问题、上下文和触发信号。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：
- 触发证据（日志/复现/反馈）：

## 目标
- $TITLE

## 非目标
- 不在本次变更范围内的事项。

## 上下文充分性检查
- [ ] 已明确输入/输出与接口契约
- [ ] 已识别关键风险（并发/边界/性能/兼容）
- [ ] 已明确验证命令与通过标准
- [ ] 若信息不足，已列出补充收集计划

## Core/Optional 边界检查
- [ ] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：

## 变更重复性检查
- 已检索是否存在相同 change-id/同类方案：
- 若有历史方案，本次差异与必要性：

## Breaking Change 检查
- [ ] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## 备选方案与取舍
- 方案 A：
- 方案 B：
- 选型理由：

## 风险与回退
- 识别主要风险，给出回退策略。
PROPOSAL

  cat > "$change_dir/design.md" <<DESIGN
# 设计说明：$CHANGE_ID

## 架构影响
- 模块边界与接口变化。

## 数据与配置影响
- 配置项、数据结构、兼容性说明。

## 兼容性与迁移方案
- 升级路径、灰度策略、回滚触发条件。

## 验证策略
- 需要执行的测试与验证命令。
DESIGN

  cat > "$change_dir/tasks.md" <<TASKS
# 执行任务：$CHANGE_ID

- [ ] 需求确认与边界冻结
- [ ] 实施改动并补充测试
- [ ] 本地验证（lint/test/build/smoke）
- [ ] 代码评审与分级闭环（blocker/major/minor）
- [ ] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围（scope_write）：
- 读取范围（scope_read）：
- 是否与其他任务冲突（同文件/同 contract/同配置）：
TASKS

  cat > "$change_dir/checklist.md" <<CHECKLIST
# 交付清单：$CHANGE_ID

- [ ] 关键场景覆盖
- [ ] 风险项评估完成
- [ ] 回退方案可执行
- [ ] 验证证据可追溯
- [ ] 评审结果为 pass（无 blocker/major 未闭环）
CHECKLIST

  cat > "$change_dir/negative-results.md" <<NEGATIVE
# 负结果记录：$CHANGE_ID

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| T0 | 待补充 | 待补充 | 待补充 | 待补充 |
NEGATIVE

  write_state "$change_dir" "proposed"
  echo "[OK] proposed: $change_dir"
}

apply_change() {
  ensure_change_id
  local change_dir="$CHANGE_ROOT/$CHANGE_ID"
  [[ -d "$change_dir" ]] || {
    echo "[FAIL] change not found: $change_dir" >&2
    exit 1
  }
  require_stage "$change_dir" "proposed" "apply"

  write_state "$change_dir" "applied"
  echo "[OK] applied: $change_dir"
}

verify_change() {
  ensure_change_id
  local change_dir="$CHANGE_ROOT/$CHANGE_ID"
  [[ -d "$change_dir" ]] || {
    echo "[FAIL] change not found: $change_dir" >&2
    exit 1
  }
  require_stage "$change_dir" "applied" "verify"

  local report="$change_dir/verify-report.md"
  {
    echo "# 验证报告：$CHANGE_ID"
    echo
    echo "- 时间：$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- 执行人：$OWNER"
    echo "- 验证命令："
    echo "  - scripts/validate_assets.sh --strict"
    echo "  - scripts/check_format.sh"
    echo "- 工件检查：proposal/design/tasks/checklist/negative-results"
    echo
  } > "$report"

  if validate_change_artifacts "$change_dir" >> "$report" 2>&1 && run_verify_checks >> "$report" 2>&1; then
    write_state "$change_dir" "verified"
    echo "[OK] verified: $change_dir"
    echo "[INFO] report: $report"
  else
    write_state "$change_dir" "verify-failed"
    echo "[FAIL] verify failed, see report: $report" >&2
    exit 1
  fi
}

review_change() {
  ensure_change_id
  local change_dir="$CHANGE_ROOT/$CHANGE_ID"
  [[ -d "$change_dir" ]] || {
    echo "[FAIL] change not found: $change_dir" >&2
    exit 1
  }
  require_stage "$change_dir" "verified" "review"

  [[ -n "$RESULT" ]] || {
    echo "[FAIL] --result is required for review" >&2
    exit 1
  }

  case "$RESULT" in
    pass|needs-fix)
      ;;
    *)
      echo "[FAIL] --result must be pass or needs-fix" >&2
      exit 1
      ;;
  esac

  ensure_non_negative_int "$BLOCKERS" "--blockers"
  ensure_non_negative_int "$MAJORS" "--majors"
  ensure_non_negative_int "$MINORS" "--minors"

  local report="$change_dir/review-report.md"
  {
    echo "# 评审报告：$CHANGE_ID"
    echo
    echo "- 时间：$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- 执行人：$OWNER"
    echo "- 结果：$RESULT"
    echo "- 分级统计：blocker=$BLOCKERS major=$MAJORS minor=$MINORS"
    echo
    echo "## 必改项（blocker/major）"
    echo "- 待补充"
    echo
    echo "## 可延期项（minor）"
    echo "- 待补充"
    echo
    echo "## 问题真实性与证据"
    echo "- 问题是否可复现："
    echo "- 证据链接（日志/命令/报告）："
    echo
    echo "## Core/Optional 归属复核"
    echo "- 归属：core/optional"
    echo "- 复核结论与依据："
  } > "$report"

  if [[ "$RESULT" == "pass" ]]; then
    if [[ "$BLOCKERS" -ne 0 || "$MAJORS" -ne 0 ]]; then
      write_state "$change_dir" "review-failed"
      echo "[FAIL] pass review requires blocker=0 and major=0" >&2
      exit 1
    fi

    write_state "$change_dir" "review-passed"
    echo "[OK] review passed: $change_dir"
    echo "[INFO] report: $report"
    return 0
  fi

  write_state "$change_dir" "review-failed"
  echo "[FAIL] review needs-fix, see report: $report" >&2
  exit 1
}

archive_change() {
  ensure_change_id
  local change_dir="$CHANGE_ROOT/$CHANGE_ID"
  [[ -d "$change_dir" ]] || {
    echo "[FAIL] change not found: $change_dir" >&2
    exit 1
  }

  local stage
  stage="$(awk '/^stage:/ {print $2; exit}' "$change_dir/state.yaml" 2>/dev/null || true)"
  if [[ "$FORCE" -ne 1 && "$stage" != "review-passed" ]]; then
    echo "[FAIL] change is not review-passed (current: ${stage:-unknown}), use --force to archive" >&2
    exit 1
  fi

  local archive_root="$CHANGE_ROOT/archive"
  local archive_dir="$archive_root/$(date +%Y%m%d)-$CHANGE_ID"
  mkdir -p "$archive_root"
  mv "$change_dir" "$archive_dir"
  echo "[OK] archived: $archive_dir"
}

case "$ACTION" in
  propose)
    propose
    ;;
  apply)
    apply_change
    ;;
  verify)
    verify_change
    ;;
  review)
    review_change
    ;;
  archive)
    archive_change
    ;;
  *)
    echo "[FAIL] unsupported action: $ACTION" >&2
    usage
    exit 1
    ;;
esac
