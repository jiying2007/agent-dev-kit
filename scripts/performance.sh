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
  budget                 检查性能预算契约
  report                 生成报告

Options:
  --target <target>      优化目标
  --level <level>        优化级别
  --summary-json         输出低 token JSON 摘要
  --out <path>           report 写入指定文件；默认输出到 stdout
  --include-quick-tests  benchmark 包含 tests/run_all.sh --quick 计时
  --include-quality      benchmark 包含质量门禁计时
  --include-io           benchmark 包含 I/O 写入测试
  --io-dir <path>        benchmark I/O 测试目录，默认 /tmp
  --apply                执行清理动作；默认只报告将要执行的动作
  -h, --help             显示帮助

Examples:
  ./scripts/performance.sh analyze
  ./scripts/performance.sh analyze --summary-json
  ./scripts/performance.sh optimize --level basic
  ./scripts/performance.sh benchmark
USAGE
}

SUMMARY_JSON=0
OUT=""
INCLUDE_IO=0
INCLUDE_QUALITY=0
INCLUDE_QUICK_TESTS=0
IO_DIR="/tmp"

json_string() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    printf '"%s"' "$value"
}

emit_size_path_json_array() {
    local input="$1"
    local first=1
    local size path
    printf '['
    while IFS=$'\t' read -r size path; do
        [[ -n "$size" && -n "$path" ]] || continue
        [[ "$first" -eq 1 ]] || printf ','
        first=0
        printf '{"size":%s,"path":%s}' "$(json_string "$size")" "$(json_string "$path")"
    done <<< "$input"
    printf ']'
}

top_dirs() {
    du -sh "$ROOT_DIR"/* 2>/dev/null | sort -hr | sed -n '1,10p' | awk '{$1=$1; size=$1; sub(/^[^[:space:]]+[[:space:]]+/, "", $0); print size "\t" $0}' || true
}

top_files() {
    find "$ROOT_DIR" -type f -exec du -h {} \; 2>/dev/null | sort -hr | sed -n '1,10p' | awk '{$1=$1; size=$1; sub(/^[^[:space:]]+[[:space:]]+/, "", $0); print size "\t" $0}' || true
}

recent_files() {
    find "$ROOT_DIR" -type f -mtime -1 -exec ls -lh {} \; 2>/dev/null | sed -n '1,10p' || true
}

file_count() {
    find "$1" "${@:2}" -type f 2>/dev/null | wc -l | tr -d ' '
}

disk_usage_percent() {
    df -h "$ROOT_DIR" | awk 'NR==2 {gsub(/%/, "", $5); print $5}'
}

analyze_summary_json() {
    local total_files script_files test_files doc_files disk_usage status warnings
    total_files="$(file_count "$ROOT_DIR")"
    script_files="$(file_count "$ROOT_DIR/scripts" -name "*.sh")"
    test_files="$(file_count "$ROOT_DIR/tests" -name "*.sh")"
    doc_files="$(file_count "$ROOT_DIR/docs" -name "*.md")"
    disk_usage="$(disk_usage_percent)"
    status="pass"
    warnings=0
    if [[ "$disk_usage" =~ ^[0-9]+$ && "$disk_usage" -ge 90 ]]; then
        status="warn"
        warnings=$((warnings + 1))
    fi

    printf '{"schema_version":1,"status":%s,' "$(json_string "$status")"
    printf '"target":%s,' "$(json_string "$ROOT_DIR")"
    printf '"total_files":%s,"script_files":%s,"test_files":%s,"doc_files":%s,' "$total_files" "$script_files" "$test_files" "$doc_files"
    printf '"disk_usage_percent":%s,' "${disk_usage:-0}"
    printf '"largest_dirs":'
    emit_size_path_json_array "$(top_dirs)"
    printf ',"largest_files":'
    emit_size_path_json_array "$(top_files)"
    printf ',"warnings":%s}\n' "$warnings"
}

analyze_performance() {
    if [[ "$SUMMARY_JSON" -eq 1 ]]; then
        analyze_summary_json
        return 0
    fi

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
    top_dirs | awk -F '\t' '{print $1 "\t" $2}'
    echo ""
    
    # 4. 最大文件
    echo "4. 最大文件:"
    top_files | awk -F '\t' '{print $1 "\t" $2}'
    echo ""
    
    # 5. 最近修改
    echo "5. 最近修改:"
    recent_files
}

optimize_performance() {
    local level="$1"
    case "$level" in
        basic|medium|advanced) ;;
        *)
            log_error "未知优化级别: $level"
            exit 1
            ;;
    esac

    if [[ "$SUMMARY_JSON" -eq 1 ]]; then
        printf '{"schema_version":1,"status":"pass","command":"optimize","level":%s,"apply":%s}\n' \
            "$(json_string "$level")" "${APPLY:-0}"
        return 0
    fi

    log_info "优化性能 (级别: $level)"

    if [[ "${APPLY:-0}" -ne 1 ]]; then
        echo "=== 性能优化 dry-run ==="
        echo "- 将清理受控临时文件: *.tmp"
        echo "- 将清理 7 天前日志: *.log"
        echo "- 将规范 scripts/tests 下 shell 脚本可执行位"
        echo "- medium/advanced 级别还会清理 .cache、旧备份或 dist"
        echo "[INFO] 添加 --apply 后才会执行清理"
        return 0
    fi
    
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
    local health_ms tests_ms test_status quality_ms quality_status file_scan_ms io_ms io_status
    local start_time end_time
    start_time=$(date +%s%N)
    bash "$ROOT_DIR/scripts/health-check.sh" check-all --summary-json >/dev/null
    end_time=$(date +%s%N)
    health_ms=$(( (end_time - start_time) / 1000000 ))

    start_time=$(date +%s%N)
    if [[ "$INCLUDE_QUICK_TESTS" -eq 1 ]]; then
        bash "$ROOT_DIR/tests/run_all.sh" --quick --max-failure-lines 20 >/dev/null
        test_status="quick"
    else
        bash "$ROOT_DIR/tests/test_validate.sh" >/dev/null
        test_status="validate-smoke"
    fi
    end_time=$(date +%s%N)
    tests_ms=$(( (end_time - start_time) / 1000000 ))

    quality_ms=0
    quality_status="skipped"
    if [[ "$INCLUDE_QUALITY" -eq 1 ]]; then
        start_time=$(date +%s%N)
        bash "$ROOT_DIR/scripts/quality-gate-check.sh" check-all >/dev/null
        end_time=$(date +%s%N)
        quality_ms=$(( (end_time - start_time) / 1000000 ))
        quality_status="measured"
    fi

    start_time=$(date +%s%N)
    find "$ROOT_DIR" -type f >/dev/null
    end_time=$(date +%s%N)
    file_scan_ms=$(( (end_time - start_time) / 1000000 ))

    io_ms=0
    io_status="skipped"
    if [[ "$INCLUDE_IO" -eq 1 ]]; then
        [[ -d "$IO_DIR" ]] || {
            log_error "I/O 测试目录不存在: $IO_DIR"
            exit 1
        }
        local bench_file
        bench_file="$(mktemp "$IO_DIR/adk-benchmark.XXXXXX")"
        start_time=$(date +%s%N)
        dd if=/dev/zero of="$bench_file" bs=1M count=10 2>/dev/null
        end_time=$(date +%s%N)
        rm -f "$bench_file"
        io_ms=$(( (end_time - start_time) / 1000000 ))
        io_status="measured"
    fi

    if [[ "$SUMMARY_JSON" -eq 1 ]]; then
        printf '{"schema_version":1,"status":"pass","health_ms":%s,"test_status":%s,"tests_ms":%s,"quality_status":%s,"quality_ms":%s,"file_scan_ms":%s,"io_status":%s,"io_ms":%s}\n' \
            "$health_ms" "$(json_string "$test_status")" "$tests_ms" "$(json_string "$quality_status")" "$quality_ms" "$file_scan_ms" "$(json_string "$io_status")" "$io_ms"
        return 0
    fi

    log_info "运行性能测试"
    
    echo "=== 性能测试 ==="
    echo ""
    
    # 1. 测试脚本执行时间
    echo "1. 脚本执行时间:"
    echo "   - 健康检查: ${health_ms}ms"
    echo "   - 测试检查 (${test_status}): ${tests_ms}ms"
    if [[ "$INCLUDE_QUALITY" -eq 1 ]]; then
        echo "   - 质量门禁: ${quality_ms}ms"
    else
        echo "   - 质量门禁: 跳过；传 --include-quality 后执行"
    fi
    echo ""
    
    # 2. 文件操作性能
    echo "2. 文件操作性能:"
    echo "   - 文件遍历: ${file_scan_ms}ms"
    echo ""
    
    # 3. 磁盘I/O性能
    echo "3. 磁盘I/O性能:"
    if [[ "$INCLUDE_IO" -eq 1 ]]; then
        echo "   - 写入性能: ${io_ms}ms (10MB, dir=${IO_DIR})"
    else
        echo "   - 跳过；传 --include-io --io-dir <path> 后执行"
    fi
}

generate_report() {
    local report
    report="$(cat <<EOF
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
$(top_dirs | awk -F '\t' '{print $1 "\t" $2}')

## 最大文件
$(top_files | awk -F '\t' '{print $1 "\t" $2}')

## 性能测试
- 使用 \`bash scripts/performance.sh benchmark\` 单独采集。

## 优化建议
1. 定期清理临时文件
2. 压缩大文件
3. 优化脚本权限
4. 清理旧备份
5. 监控磁盘使用
EOF
)"

    if [[ "$SUMMARY_JSON" -eq 1 ]]; then
        printf '{"schema_version":1,"status":"pass","command":"report","written":%s,"out":%s}\n' \
            "$([[ -n "$OUT" ]] && printf 1 || printf 0)" "$(json_string "${OUT:-stdout}")"
        return 0
    fi

    if [[ -n "$OUT" ]]; then
        mkdir -p "$(dirname "$OUT")"
        printf '%s\n' "$report" >"$OUT"
        log_success "性能报告已生成: $OUT"
    else
        printf '%s\n' "$report"
    fi
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    if [[ "$command" == "budget" ]]; then
        exec "$ROOT_DIR/scripts/check-performance-budgets.sh" "$@"
    fi
    local target="all"
    local level="basic"
    APPLY=0

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
            --summary-json)
                SUMMARY_JSON=1
                shift
                ;;
            --include-quality)
                INCLUDE_QUALITY=1
                shift
                ;;
            --include-quick-tests)
                INCLUDE_QUICK_TESTS=1
                shift
                ;;
            --out)
                OUT="${2:-}"
                shift 2
                ;;
            --include-io)
                INCLUDE_IO=1
                shift
                ;;
            --io-dir)
                IO_DIR="${2:-}"
                shift 2
                ;;
            --apply)
                APPLY=1
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
        analyze) analyze_performance "$target" ;;
        optimize) optimize_performance "$level" ;;
        benchmark) run_benchmark ;;
        report) generate_report ;;
        -h|--help) usage ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
