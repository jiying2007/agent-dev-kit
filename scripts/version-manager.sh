#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

# ============================================================================
# version-manager.sh — agent-dev-kit 仓库内版本管理
#
# 职责: 管理 agent-dev-kit 仓库内部的版本锁定和升级路径
# 特点: 功能更专注，仅处理仓库内部内容
# 对应: llm_agent/scripts/version-manager.sh 是工作区级完整版
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat <<USAGE
版本锁定和升级路径脚本

Usage:
  ./scripts/version-manager.sh <command> [options]

Commands:
  current                显示当前版本
  lock                   锁定版本
  unlock                 解锁版本
  upgrade                升级版本
  compare                比较版本
  changelog              生成变更日志

Options:
  --version <version>    版本号
  --target <target>      目标版本
  --force                强制执行
  -h, --help             显示帮助

Examples:
  ./scripts/version-manager.sh current
  ./scripts/version-manager.sh lock --version 1.0.0
  ./scripts/version-manager.sh upgrade --target 1.1.0
USAGE
}

get_current_version() {
    if [[ -f "$ROOT_DIR/manifest.yaml" ]]; then
        grep "^version:" "$ROOT_DIR/manifest.yaml" | awk '{print $2}' | tr -d '"'
    else
        echo "unknown"
    fi
}

show_current_version() {
    local version=$(get_current_version)
    log_info "当前版本: $version"
    echo "$version"
}

lock_version() {
    local version="$1"
    log_info "锁定版本: $version"
    
    if [[ -f "$ROOT_DIR/manifest.yaml" ]]; then
        sed -i "s/^version:.*$/version: $version/" "$ROOT_DIR/manifest.yaml"
        log_success "版本已锁定: $version"
    else
        log_error "manifest.yaml不存在"
        return 1
    fi
    
    cat > "$ROOT_DIR/.version-lock" <<EOF
version: $version
locked_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
locked_by: $(whoami)
