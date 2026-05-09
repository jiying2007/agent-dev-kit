#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

# ============================================================================
# backup-rollback.sh — agent-dev-kit 仓库内备份回滚
#
# 职责: 备份和回滚 agent-dev-kit 仓库内部的配置和数据
# 特点: 功能更专注，仅处理仓库内部内容
# 对应: llm_agent/scripts/backup-rollback.sh 是工作区级完整版
# ============================================================================

; ; ; BLUE='\033[0;34m'; 
[INFO]${NC} $1"; }
[SUCCESS]${NC} $1"; }
[WARNING]${NC} $1"; }
[ERROR]${NC} $1"; }

usage() {
    cat <<USAGE
安装备份和回滚脚本

Usage:
  ./scripts/backup-rollback.sh <command> [options]

Commands:
  backup                 创建备份
  restore                恢复备份
  list                   列出备份
  rollback               回滚到指定版本
  verify                 验证备份完整性

Options:
  --target <target>      安装目标目录
  --backup-dir <dir>     备份目录
  --version <version>    版本号
  --force                强制执行
  -h, --help             显示帮助

Examples:
  ./scripts/backup-rollback.sh backup --target ~/.codex
  ./scripts/backup-rollback.sh restore --target ~/.codex --version 20260505
  ./scripts/backup-rollback.sh list --target ~/.codex
USAGE
}

create_backup() {
    local target="$1" backup_dir="$2" version="$3"
    log_info "创建备份: $target -> $backup_dir"
    mkdir -p "$backup_dir"
    local backup_file="$backup_dir/backup-${version}-$(date +%Y%m%d%H%M%S).tar.gz"
    
    if [[ -d "$target" ]]; then
        tar -czf "$backup_file" -C "$(dirname "$target")" "$(basename "$target")"
        log_success "备份创建成功: $backup_file"
        return 0
    else
        log_error "目标目录不存在: $target"
        return 1
    fi
}

restore_backup() {
    local target="$1" backup_dir="$2" version="$3" force="$4"
    log_info "恢复备份: $version -> $target"
    local backup_file
    backup_file=$(find "$backup_dir" -name "backup-${version}-*.tar.gz" 2>/dev/null | sort -r | head -1)
    
    if [[ -z "$backup_file" ]]; then
        log_error "未找到版本 $version 的备份"
        return 1
    fi
    
    if [[ -d "$target" && "$force" != "true" ]]; then
        log_warning "目标目录已存在: $target"
        if [[ "${force:-}" != "true" ]]; then
            echo "[FAIL] --force required for overwrite" >&2
            exit 1
        fi
    fi
    
    [[ -d "$target" ]] && rm -rf "$target"
    tar -xzf "$backup_file" -C "$(dirname "$target")"
    log_success "备份恢复成功: $backup_file"
    return 0
}

list_backups() {
    local backup_dir="$1"
    log_info "列出备份: $backup_dir"
    [[ ! -d "$backup_dir" ]] && { log_warning "备份目录不存在"; return 0; }
    
    local backups
    backups=$(find "$backup_dir" -name "backup-*.tar.gz" 2>/dev/null | sort -r)
    [[ -z "$backups" ]] && { log_warning "没有找到备份"; return 0; }
    
    echo "可用备份:"
    echo "======================================"
    for backup in $backups; do
        local filename=$(basename "$backup")
        local version=$(echo "$filename" | sed -n 's/backup-\([^-]*\)-.*/\1/p')
        echo "版本: $version | 文件: $backup"
    done
    return 0
}

rollback_version() {
    local target="$1" backup_dir="$2" version="$3" force="$4"
    log_info "回滚到版本: $version"
    local current_version="pre-rollback-$(date +%Y%m%d%H%M%S)"
    create_backup "$target" "$backup_dir" "$current_version"
    restore_backup "$target" "$backup_dir" "$version" "$force"
    log_success "回滚完成"
    return 0
}

verify_backup() {
    local backup_dir="$1" version="$2"
    log_info "验证备份完整性: $version"
    local backup_file
    backup_file=$(find "$backup_dir" -name "backup-${version}-*.tar.gz" 2>/dev/null | sort -r | head -1)
    
    [[ -z "$backup_file" ]] && { log_error "未找到版本 $version 的备份"; return 1; }
    
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_success "备份文件完整: $backup_file"
        return 0
    else
        log_error "备份文件损坏: $backup_file"
        return 1
    fi
}

main() {
    [[ $# -lt 1 ]] && { usage; exit 1; }
    local command="$1"; shift
    local target="" backup_dir="$ROOT_DIR/.backups" version="" force="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target) target="$2"; shift 2 ;;
            --backup-dir) backup_dir="$2"; shift 2 ;;
            --version) version="$2"; shift 2 ;;
            --force) force="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    case "$command" in
        backup) [[ -z "$target" ]] && { log_error "缺少--target"; exit 1; }; create_backup "$target" "$backup_dir" "${version:-$(date +%Y%m%d)}" ;;
        restore) [[ -z "$target" || -z "$version" ]] && { log_error "缺少参数"; exit 1; }; restore_backup "$target" "$backup_dir" "$version" "$force" ;;
        list) list_backups "$backup_dir" ;;
        rollback) [[ -z "$target" || -z "$version" ]] && { log_error "缺少参数"; exit 1; }; rollback_version "$target" "$backup_dir" "$version" "$force" ;;
        verify) [[ -z "$version" ]] && { log_error "缺少--version"; exit 1; }; verify_backup "$backup_dir" "$version" ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
