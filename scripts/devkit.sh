#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/devkit.sh <command> [options]

Commands:
  install   安装 Agents/Skills 到目标工具目录
  validate  校验 manifest 与资产结构
  convert   转换资产到目标工具格式
  catalog   生成或检索 Agent/Skill 目录索引
  match     根据输入文本匹配 skill 触发条件
  propose   创建变更提案工件
  apply     更新变更状态为已实施
  verify    执行变更验证并写报告
  review    执行分级评审并闭环门禁
  archive   归档已验证变更
  test      运行回归测试集

Examples:
  ./scripts/devkit.sh install --tool auto --profile embedded-fullstack
  ./scripts/devkit.sh convert --target claude-code --profile core
  ./scripts/devkit.sh catalog build
  ./scripts/devkit.sh match --skill requirements-triage --text "收到模糊需求"
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
    exec "$SCRIPT_DIR/install_assets.sh" "$@"
    ;;
  validate)
    exec "$SCRIPT_DIR/validate_assets.sh" "$@"
    ;;
  convert)
    exec "$SCRIPT_DIR/convert_assets.sh" "$@"
    ;;
  catalog)
    exec "$SCRIPT_DIR/catalog_assets.sh" "$@"
    ;;
  match)
    exec "$SCRIPT_DIR/skill_match.sh" "$@"
    ;;
  propose|apply|verify|review|archive)
    exec "$SCRIPT_DIR/workflow.sh" "$CMD" "$@"
    ;;
  test)
    exec "$ROOT_DIR/tests/run_all.sh" "$@"
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
