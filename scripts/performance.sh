#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<USAGE
性能优化脚本

Usage:
  ./scripts/performance.sh <command> [options]

Commands:
  analyze                分析性能
  optimize               优化性能
  benchmark              性能测试
  report                 生成报告

Options:
  --target <target>      优化目标
  --level <level>        优化级别
  -h, --help             显示帮助

Examples:
  ./scripts/performance.sh analyze
  ./scripts/performance.sh optimize --level basic
  ./scripts/performance.sh benchmark
USAGE
}

analyze_performance() {
    log_info "分析性能"
    
    echo "=== 性能分析报告 ==="
    echo ""
    
    # 1. 系统资源
    echo "1. 系统资源:"
    echo "   - CPU核心数: $(nproc)"
    echo "   - 内存总量: $(free -h | awk 'NR==2 {print $2}')"
    echo "   - 磁盘空间: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $4}') 可用"
    echo "   - 磁盘使用率: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}')"
    echo ""
    
    # 2. 文件统计
    echo "2. 文件统计:"
    echo "   - 总文件数: $(find "$ROOT_DIR" -type f | wc -l)"
    echo "   - 脚本文件: $(find "$ROOT_DIR/scripts" -name "*.sh" -type f | wc -l)"
    echo "   - 测试文件: $(find "$ROOT_DIR/tests" -name "*.sh" -type f | wc -l)"
    echo "   - 文档文件: $(find "$ROOT_DIR/docs" -name "*.md" -type f | wc -l)"
    echo ""
    
    # 3. 目录大小
    echo "3. 目录大小:"
    du -sh "$ROOT_DIR"/* 2>/dev/null | sort -hr | head -10
    echo ""
    
    # 4. 最大文件
    echo "4. 最大文件:"
    find "$ROOT_DIR" -type f -exec du -h {} \; 2>/dev/null | sort -hr | head -10
    echo ""
    
    # 5. 最近修改
    echo "5. 最近修改:"
    find "$ROOT_DIR" -type f -mtime -1 -exec ls -lh {} \; 2>/dev/null | head -10
}

optimize_performance() {
    local level="$1"
    log_info "优化性能 (级别: $level)"
    
    case "$level" in
        basic)
            log_info "基础优化"
            # 清理临时文件
            find "$ROOT_DIR" -name "*.tmp" -type f -delete 2>/dev/null || true
            find "$ROOT_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
            # 优化权限
            find "$ROOT_DIR/scripts" -name "*.sh" -type f -exec chmod +x {} \;
            find "$ROOT_DIR/tests" -name "*.sh" -type f -exec chmod +x {} \;
            ;;
        medium)
            log_info "中等优化"
            # 基础优化
            optimize_performance "basic"
            # 清理缓存
            rm -rf "$ROOT_DIR/.cache" 2>/dev/null || true
            # 压缩大文件
            find "$ROOT_DIR/docs" -name "*.md" -type f -size +100k -exec gzip -k {} \; 2>/dev/null || true
            ;;
        advanced)
            log_info "高级优化"
            # 中等优化
            optimize_performance "medium"
            # 清理旧备份
            find "$ROOT_DIR/.backups" -name "backup-*.tar.gz" -type f -mtime +30 -delete 2>/dev/null || true
            # 清理构建目录
            rm -rf "$ROOT_DIR/dist" 2>/dev/null || true
            # 优化文档
            # Removed: destructive sed that strips blank lines from .md files breaks markdown rendering
            # find "$ROOT_DIR/docs" -name "*.md" -type f -exec sed -i 's/^[[:space:]]*$//' {} \; 2>/dev/null || true
            ;;
    esac
    
    log_success "性能优化完成"
}

run_benchmark() {
    log_info "运行性能测试"
    
    echo "=== 性能测试 ==="
    echo ""
    
    # 1. 测试脚本执行时间
    echo "1. 脚本执行时间:"
    echo "   - 健康检查: $(time bash "$ROOT_DIR/scripts/health-check.sh" check-all 2>&1 | tail -1)"
    echo "   - 测试运行: $(time bash "$ROOT_DIR/tests/run_all.sh" 2>&1 | tail -1)"
    echo "   - 质量门禁: $(time bash "$ROOT_DIR/scripts/quality-gate-check.sh" check-all 2>&1 | tail -1)"
    echo ""
    
    # 2. 文件操作性能
    echo "2. 文件操作性能:"
    local start_time=$(date +%s%N)
    find "$ROOT_DIR" -type f | wc -l
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))
    echo "   - 文件遍历: ${duration}ms"
    echo ""
    
    # 3. 磁盘I/O性能
    echo "3. 磁盘I/O性能:"
    local start_time=$(date +%s%N)
    dd if=/dev/zero of="$ROOT_DIR/.benchmark" bs=1M count=10 2>/dev/null
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))
    echo "   - 写入性能: ${duration}ms (10MB)"
    rm -f "$ROOT_DIR/.benchmark"
}

generate_report() {
    log_info "生成性能报告"
    
    local report_file="$ROOT_DIR/.monitoring/performance-report-$(date +%Y%m%d%H%M%S).md"
    
    cat > "$report_file" <<EOF
# 性能报告

## 报告信息
- 生成时间: $(date)
- 系统信息: $(uname -a)

## 系统资源
- CPU核心数: $(nproc)
- 内存总量: $(free -h | awk 'NR==2 {print $2}')
- 磁盘空间: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $4}') 可用
- 磁盘使用率: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}')

## 文件统计
- 总文件数: $(find "$ROOT_DIR" -type f | wc -l)
- 脚本文件: $(find "$ROOT_DIR/scripts" -name "*.sh" -type f | wc -l)
- 测试文件: $(find "$ROOT_DIR/tests" -name "*.sh" -type f | wc -l)
- 文档文件: $(find "$ROOT_DIR/docs" -name "*.md" -type f | wc -l)

## 目录大小
$(du -sh "$ROOT_DIR"/* 2>/dev/null | sort -hr | head -10)

## 最大文件
$(find "$ROOT_DIR" -type f -exec du -h {} \; 2>/dev/null | sort -hr | head -10)

## 性能测试
- 健康检查: $(time bash "$ROOT_DIR/scripts/health-check.sh" check-all 2>&1 | tail -1)
- 测试运行: $(time bash "$ROOT_DIR/tests/run_all.sh" 2>&1 | tail -1)
- 质量门禁: $(time bash "$ROOT_DIR/scripts/quality-gate-check.sh" check-all 2>&1 | tail -1)

## 优化建议
1. 定期清理临时文件
2. 压缩大文件
3. 优化脚本权限
4. 清理旧备份
5. 监控磁盘使用
EOF

    log_success "性能报告已生成: $report_file"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    local target="all"
    local level="basic"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)
                target="$2"
                shift 2
                ;;
            --level)
                level="$2"
                shift 2
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
        analyze) analyze_performance "$target" ;;
        optimize) optimize_performance "$target" "$level" ;;
        benchmark) run_benchmark ;;
        report) generate_report ;;
        -h|--help) usage ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
