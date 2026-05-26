#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ADK_DECLARATION_ROOT="${ADK_ROOT:-$ROOT_DIR}"

usage() {
    cat <<USAGE
自动化运维脚本

Usage:
  ./scripts/auto-ops.sh <command> [options]

Commands:
  daily                  每日运维
  weekly                 每周运维
  monthly                每月运维
  cleanup                清理临时文件
  optimize               优化性能
  security               安全检查

Options:
  --dry-run              模拟运行
  --force                强制执行
  -h, --help             显示帮助

Examples:
  ./scripts/auto-ops.sh daily
  ./scripts/auto-ops.sh weekly --dry-run
  ./scripts/auto-ops.sh cleanup
  ./scripts/auto-ops.sh optimize
USAGE
}

daily_ops() {
    local dry_run="$1"
    log_info "执行每日运维"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 模拟每日运维"
    fi
    
    # 1. 健康检查
    log_info "1. 健康检查"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/health-check.sh" check-all
    fi
    
    # 2. 运行测试
    log_info "2. 运行测试"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/tests/run_all.sh"
    fi
    
    # 3. 清理临时文件
    log_info "3. 清理临时文件"
    if [[ "$dry_run" != "true" ]]; then
        cleanup_temp_files
    fi
    
    # 4. 检查磁盘空间
    log_info "4. 检查磁盘空间"
    local disk_usage=$(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ "$disk_usage" -gt 80 ]]; then
        log_warning "磁盘使用率过高: ${disk_usage}%"
    else
        log_success "磁盘使用率正常: ${disk_usage}%"
    fi
    
    # 5. 检查备份
    log_info "5. 检查备份"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/backup-rollback.sh" list 2>/dev/null || log_warning "无备份"
    fi
    
    log_success "每日运维完成"
}

weekly_ops() {
    local dry_run="$1"
    log_info "执行每周运维"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 模拟每周运维"
    fi
    
    # 1. 执行每日运维
    log_info "1. 执行每日运维"
    if [[ "$dry_run" != "true" ]]; then
        daily_ops "$dry_run"
    fi
    
    # 2. 创建备份
    log_info "2. 创建备份"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/backup-rollback.sh" backup --target "$CODEX_DECLARATION_ROOT"
    fi
    
    # 3. 生成监控报告
    log_info "3. 生成监控报告"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/monitoring.sh" report
    fi
    
    # 4. 检查版本
    log_info "4. 检查版本"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/version-manager.sh" current
    fi
    
    # 5. 安全检查
    log_info "5. 安全检查"
    if [[ "$dry_run" != "true" ]]; then
        security_check
    fi
    
    log_success "每周运维完成"
}

monthly_ops() {
    local dry_run="$1"
    log_info "执行每月运维"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 模拟每月运维"
    fi
    
    # 1. 执行每周运维
    log_info "1. 执行每周运维"
    if [[ "$dry_run" != "true" ]]; then
        weekly_ops "$dry_run"
    fi
    
    # 2. 版本升级检查
    log_info "2. 版本升级检查"
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/version-manager.sh" current
    fi
    
    # 3. 性能优化
    log_info "3. 性能优化"
    if [[ "$dry_run" != "true" ]]; then
        optimize_performance
    fi
    
    # 4. 清理旧备份
    log_info "4. 清理旧备份"
    if [[ "$dry_run" != "true" ]]; then
        cleanup_old_backups
    fi
    
    # 5. 生成月度报告
    log_info "5. 生成月度报告"
    if [[ "$dry_run" != "true" ]]; then
        generate_monthly_report
    fi
    
    log_success "每月运维完成"
}

cleanup_temp_files() {
    log_info "清理临时文件"
    
    # 清理临时目录
    find "$ROOT_DIR" -name "*.tmp" -type f -mtime +7 -delete 2>/dev/null || true
    find "$ROOT_DIR" -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true
    find "$ROOT_DIR" -name "*.bak" -type f -mtime +7 -delete 2>/dev/null || true
    
    # 清理构建目录
    if [[ -d "$ROOT_DIR/dist" ]]; then
        rm -rf "$ROOT_DIR/dist"
        log_info "清理构建目录"
    fi
    
    log_success "临时文件清理完成"
}

cleanup_old_backups() {
    log_info "清理旧备份"
    
    local backup_dir="$ROOT_DIR/.backups"
    if [[ -d "$backup_dir" ]]; then
        # 保留最近30天的备份
        find "$backup_dir" -name "backup-*.tar.gz" -type f -mtime +30 -delete 2>/dev/null || true
        log_success "旧备份清理完成"
    else
        log_info "无备份目录"
    fi
}

optimize_performance() {
    log_info "优化性能"
    
    # 1. 优化脚本权限
    log_info "优化脚本权限"
    find "$ROOT_DIR/scripts" -name "*.sh" -type f -exec chmod +x {} \;
    find "$ROOT_DIR/tests" -name "*.sh" -type f -exec chmod +x {} \;
    
    # 2. 清理缓存
    log_info "清理缓存"
    if [[ -d "$ROOT_DIR/.cache" ]]; then
        rm -rf "$ROOT_DIR/.cache"
    fi
    
    # 3. 优化文档
    log_info "优化文档"
    if [[ -d "$ROOT_DIR/docs" ]]; then
        # 压缩大文件 - 已禁用: gzip 会在原始文件旁产生不需要的 .gz 副本
        : # no-op placeholder
    fi
    
    log_success "性能优化完成"
}

security_check() {
    log_info "安全检查"
    
    local issues=()
    
    # 1. 检查文件权限
    log_info "检查文件权限"
    local world_writable=$(find "$ROOT_DIR" -type f -perm -o+w 2>/dev/null | wc -l)
    if [[ "$world_writable" -gt 0 ]]; then
        issues+=("发现 $world_writable 个世界可写文件")
    fi
    
    # 2. 检查敏感文件
    log_info "检查敏感文件"
    local sensitive_files=(".env" "*.key" "*.pem" "*.p12")
    for pattern in "${sensitive_files[@]}"; do
        local found=$(find "$ROOT_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)
        if [[ "$found" -gt 0 ]]; then
            issues+=("发现 $found 个敏感文件: $pattern")
        fi
    done
    
    # 3. 检查脚本安全
    log_info "检查脚本安全"
    local scripts_with_sudo=$(grep -r "sudo" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
    if [[ "$scripts_with_sudo" -gt 0 ]]; then
        issues+=("发现 $scripts_with_sudo 个脚本使用sudo")
    fi
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "安全检查通过"
    else
        log_warning "安全检查发现问题:"
        for issue in "${issues[@]}"; do echo "  - $issue"; done
    fi
}

generate_monthly_report() {
    log_info "生成月度报告"
    
    local report_file="$ROOT_DIR/.monitoring/monthly-report-$(date +%Y%m).md"
    
    cat > "$report_file" <<EOF
# 月度运维报告

## 报告信息
- 月份: $(date +%Y年%m月)
- 生成时间: $(date)

## 系统状态
- 磁盘使用率: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}')
- 内存使用率: $(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')%
- CPU负载: $(uptime | awk -F'load average:' '{print $2}')

## 健康检查
- 目录结构: $(bash "$ROOT_DIR/scripts/health-check.sh" check-structure >/dev/null 2>&1 && echo "通过" || echo "失败")
- 依赖检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-dependencies >/dev/null 2>&1 && echo "通过" || echo "失败")
- 配置检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-configuration >/dev/null 2>&1 && echo "通过" || echo "失败")
- 测试检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-tests >/dev/null 2>&1 && echo "通过" || echo "失败")
- 质量检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-quality >/dev/null 2>&1 && echo "通过" || echo "失败")

## 测试状态
- 测试用例: $(bash "$ROOT_DIR/tests/run_all.sh" 2>&1 | grep -E "Total:|Passed:|Failed:" | tail -3)

## 备份状态
$(bash "$ROOT_DIR/scripts/backup-rollback.sh" list 2>/dev/null || echo "无备份")

## 版本信息
- 当前版本: $(bash "$ROOT_DIR/scripts/version-manager.sh" current 2>/dev/null || echo "未知")

## 建议
1. 定期运行健康检查
2. 监控磁盘和内存使用
3. 及时处理告警
4. 定期备份数据
5. 定期更新版本
EOF

    log_success "月度报告已生成: $report_file"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    local dry_run="false"
    local force="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run="true"
                shift
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
        daily)
            daily_ops "$dry_run"
            ;;
        weekly)
            weekly_ops "$dry_run"
            ;;
        monthly)
            monthly_ops "$dry_run"
            ;;
        cleanup)
            cleanup_temp_files "$dry_run" "$force"
            ;;
        optimize)
            optimize_performance "$dry_run"
            ;;
        security)
            security_check
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
