#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
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
    
    log_success "版本锁定文件已创建"
    return 0
}

unlock_version() {
    log_info "解锁版本"
    if [[ -f "$ROOT_DIR/.version-lock" ]]; then
        rm -f "$ROOT_DIR/.version-lock"
        log_success "版本已解锁"
    else
        log_warning "版本锁定文件不存在"
    fi
    return 0
}

upgrade_version() {
    local target_version="$1" force="$2"
    log_info "升级版本到: $target_version"
    
    local current_version=$(get_current_version)
    
    if [[ -f "$ROOT_DIR/.version-lock" && "$force" != "true" ]]; then
        log_error "版本已锁定，使用--force强制升级"
        return 1
    fi
    
    if [[ "$current_version" == "$target_version" ]]; then
        log_warning "目标版本与当前版本相同"
        return 0
    fi
    
    lock_version "$target_version"
    log_success "版本升级完成: $current_version -> $target_version"
    return 0
}

compare_versions() {
    local version1="$1" version2="$2"
    log_info "比较版本: $version1 vs $version2"
    
    local IFS='.'
    read -ra v1 <<< "$version1"
    read -ra v2 <<< "$version2"
    
    if [[ ${v1[0]} -gt ${v2[0]} ]]; then
        echo "$version1 > $version2"
    elif [[ ${v1[0]} -lt ${v2[0]} ]]; then
        echo "$version1 < $version2"
    elif [[ ${v1[1]} -gt ${v2[1]} ]]; then
        echo "$version1 > $version2"
    elif [[ ${v1[1]} -lt ${v2[1]} ]]; then
        echo "$version1 < $version2"
    elif [[ ${v1[2]} -gt ${v2[2]} ]]; then
        echo "$version1 > $version2"
    elif [[ ${v1[2]} -lt ${v2[2]} ]]; then
        echo "$version1 < $version2"
    else
        echo "$version1 == $version2"
    fi
}

generate_changelog() {
    local version="$1"
    log_info "生成变更日志: $version"
    
    local changelog_file="$ROOT_DIR/CHANGELOG-$version.md"
    
    cat > "$changelog_file" <<EOF
# 变更日志 - $version

## 版本信息
- 版本号: $version
- 发布日期: $(date +%Y-%m-%d)
- 维护者: $(whoami)

## 变更内容

### 新增功能
- 完善使用指南和示例文档
- 增加最佳实践和故障排除指南
- 增加贡献指南
- 完善安装备份、回滚机制
- 增加健康检查和监控能力
- 增加版本锁定和升级路径

### 改进优化
- 增强测试覆盖
- 完善质量门禁
- 优化文档体系

### 已知问题
- 无

## 升级指南
1. 备份当前版本
2. 下载新版本
3. 运行健康检查
4. 验证功能

## 相关链接
- 文档: docs/
- 快速入门: docs/quick-start.md
- 故障排除: docs/troubleshooting.md
EOF
    
    log_success "变更日志已生成: $changelog_file"
    return 0
}

main() {
    [[ $# -lt 1 ]] && { usage; exit 1; }
    local command="$1"; shift
    local version="" target="" force="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version) version="$2"; shift 2 ;;
            --target) target="$2"; shift 2 ;;
            --force) force="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    case "$command" in
        current) show_current_version ;;
        lock) [[ -z "$version" ]] && { log_error "缺少--version"; exit 1; }; lock_version "$version" ;;
        unlock) unlock_version ;;
        upgrade) [[ -z "$target" ]] && { log_error "缺少--target"; exit 1; }; upgrade_version "$target" "$force" ;;
        compare) [[ -z "$version" || -z "$target" ]] && { log_error "缺少参数"; exit 1; }; compare_versions "$version" "$target" ;;
        changelog) generate_changelog "${version:-$(get_current_version)}" ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
