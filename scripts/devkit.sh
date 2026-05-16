#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# devkit.sh — agent-dev-kit 仓库内统一入口
#
# 职责: 管理 agent-dev-kit 仓库内部的资产（install/validate/convert/catalog/match）
# 特点: 功能更专注，仅处理仓库内部内容
# 对应: llm_agent/scripts/devkit.sh 是工作区级完整版
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/devkit.sh <command> [options]

Commands:
  install   安装 Agents/Skills 到目标工具目录
  validate  校验 manifest 与资产结构
  convert   转换资产到目标工具格式
  codex-handoff 检查 Codex handoff 是否符合 ~/codex 规范
  catalog   生成或检索 Agent/Skill 目录索引
  match     根据输入文本匹配 skill 触发条件
  bridge    执行 OpenSpec 与 adk 变更工件桥接（import/export）
  evidence  追加命令级 Evidence Index 记录
  propose   创建变更提案工件
  apply     更新变更状态为已实施
  verify    执行变更验证并写报告
  review    执行分级评审并闭环门禁
  archive   归档已验证变更
  test      运行回归测试集
  health    健康检查（结构/依赖/配置/测试/质量）
  backup    备份/恢复/回滚操作
  ops       日常/周常/月常运维编排
  monitor   系统监控与告警
  perf      性能分析与优化
  security  安全扫描与加固
  release   发布准备/验证/构建/发布/回滚
  version   版本查看/锁定/升级/对比

Examples:
  ./scripts/devkit.sh install --tool auto --profile embedded-fullstack
  ./scripts/devkit.sh convert --target claude-code --profile core
  ./scripts/devkit.sh codex-handoff --codex-root ~/codex
  ./scripts/devkit.sh catalog build
  ./scripts/devkit.sh match --skill adk-requirements-triage --text "收到模糊需求"
  ./scripts/devkit.sh evidence append --file docs/changes/my-change/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/my-change/verify-report.md --layer Workflow --artifact verify-report
  ./scripts/devkit.sh propose --change add-can-fd --title "新增 CAN-FD 接入"
  ./scripts/devkit.sh review --change add-can-fd --result pass --blockers 0 --majors 0 --minors 1
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

CMD="$1"
shift

case "$CMD" in
  install)
    exec "$SCRIPT_DIR/install-assets.sh" "$@"
    ;;
  validate)
    exec "$SCRIPT_DIR/validate-assets.sh" "$@"
    ;;
  convert)
    exec "$SCRIPT_DIR/convert-assets.sh" "$@"
    ;;
  codex-handoff)
    exec "$SCRIPT_DIR/check-codex-handoff.sh" "$@"
    ;;
  catalog)
    exec "$SCRIPT_DIR/catalog-assets.sh" "$@"
    ;;
  match)
    exec "$SCRIPT_DIR/skill-match.sh" "$@"
    ;;
  bridge)
    exec "$SCRIPT_DIR/openspec-bridge.sh" "$@"
    ;;
  evidence)
    exec "$SCRIPT_DIR/evidence-index.sh" "$@"
    ;;
  propose|apply|verify|review|archive)
    exec "$SCRIPT_DIR/workflow.sh" "$CMD" "$@"
    ;;
  test)
    exec "$ROOT_DIR/tests/run_all.sh" "$@"
    ;;
  health)
    exec "$SCRIPT_DIR/health-check.sh" "$@"
    ;;
  backup)
    exec "$SCRIPT_DIR/backup-rollback.sh" "$@"
    ;;
  ops)
    exec "$SCRIPT_DIR/auto-ops.sh" "$@"
    ;;
  monitor)
    exec "$SCRIPT_DIR/monitoring.sh" "$@"
    ;;
  perf)
    exec "$SCRIPT_DIR/performance.sh" "$@"
    ;;
  security)
    exec "$SCRIPT_DIR/security.sh" "$@"
    ;;
  release)
    exec "$SCRIPT_DIR/release-manager.sh" "$@"
    ;;
  version)
    exec "$SCRIPT_DIR/version-manager.sh" "$@"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "[FAIL] unknown command: $CMD" >&2
    usage
    exit 1
    ;;
esac
