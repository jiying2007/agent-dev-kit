#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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
EOF

    log_success "版本锁定文件已创建: .version-lock"
}

unlock_version() {
    log_info "解锁版本"

    if [[ -f "$ROOT_DIR/.version-lock" ]]; then
        rm -f "$ROOT_DIR/.version-lock"
        log_success "版本已解锁"
    else
        log_warning "版本锁定文件不存在"
    fi
}

upgrade_version() {
    local target_version="$1"
    local force="$2"
    local current_version
    current_version="$(get_current_version)"

    log_info "升级版本: ${current_version} -> ${target_version}"

    if [[ -f "$ROOT_DIR/.version-lock" && "$force" != "true" ]]; then
        log_error "版本已锁定，使用 --force 强制升级"
        return 1
    fi

    if [[ "$current_version" == "$target_version" ]]; then
        log_warning "目标版本与当前版本相同"
        return 0
    fi

    lock_version "$target_version"
    log_success "版本升级完成: ${current_version} -> ${target_version}"
}

compare_versions() {
    local version1="$1"
    local version2="$2"

    if [[ "$version1" == "$version2" ]]; then
        echo "$version1 == $version2"
    elif [[ "$(printf '%s\n%s\n' "$version1" "$version2" | sort -V | head -n1)" == "$version1" ]]; then
        echo "$version1 < $version2"
    else
        echo "$version1 > $version2"
    fi
}

generate_changelog() {
    local version="$1"
    local changelog_file="$ROOT_DIR/CHANGELOG-$version.md"

    cat > "$changelog_file" <<EOF
# 变更日志 - $version

## 版本信息
- 版本号: $version
- 发布日期: $(date +%Y-%m-%d)
- 维护者: $(whoami)

## 变更内容

### 新增功能
- 待补充

### 改进优化
- 待补充

### 修复问题
- 待补充

### 已知问题
- 待补充
EOF

    log_success "变更日志已生成: $changelog_file"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    local version=""
    local target=""
    local force="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                [[ $# -ge 2 ]] || { log_error "--version 缺少值"; exit 1; }
                version="$2"
                shift 2
                ;;
            --target)
                [[ $# -ge 2 ]] || { log_error "--target 缺少值"; exit 1; }
                target="$2"
                shift 2
                ;;
            --force)
                force="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                usage
                exit 1
                ;;
        esac
    done

    case "$command" in
        current)
            show_current_version
            ;;
        lock)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            lock_version "$version"
            ;;
        unlock)
            unlock_version
            ;;
        upgrade)
            [[ -n "$target" ]] || { log_error "缺少 --target 参数"; exit 1; }
            upgrade_version "$target" "$force"
            ;;
        compare)
            [[ -n "$version" && -n "$target" ]] || { log_error "缺少 --version 或 --target 参数"; exit 1; }
            compare_versions "$version" "$target"
            ;;
        changelog)
            version="${version:-$(get_current_version)}"
            generate_changelog "$version"
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
