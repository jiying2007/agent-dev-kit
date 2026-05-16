#!/usr/bin/env bash
# scripts/quality-gates.sh
# 通用质量门禁脚本
#
# 用途：检查代码变更的质量和完整性
# 来源：Harness Engineering 文章分析
# 日期：2026-05-13

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_pass() {
    echo -e "${GREEN}PASS: $1${NC}"
}

log_fail() {
    echo -e "${RED}FAIL: $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}WARN: $1${NC}"
}

log_info() {
    echo -e "INFO: $1"
}

# 门禁 1: CI 状态检查
check_ci_status() {
    local change_dir=$1
    local ci_result="$change_dir/ci_result/ci_report.md"

    log_info "检查 CI 状态: $change_dir"

    # 检查 CI 报告是否存在
    if [[ ! -f "$ci_result" ]]; then
        log_fail "CI 报告不存在: $ci_result"
        return 1
    fi

    # 解析 CI 报告
    local status=$(grep "status:" "$ci_result" | awk '{print $2}' || echo "UNKNOWN")
    local total_tests=$(grep "total_tests:" "$ci_result" | awk '{print $2}' || echo "0")
    local passed=$(grep "passed:" "$ci_result" | awk '{print $2}' || echo "0")

    # 检查三个条件
    if [[ "$status" != "SUCCESS" ]]; then
        log_fail "CI 状态不是 SUCCESS: $status"
        return 1
    fi

    if [[ "$total_tests" == "0" ]]; then
        log_fail "测试用例数为 0"
        return 1
    fi

    if [[ "$passed" != "$total_tests" ]]; then
        log_fail "测试通过数 ($passed) 不等于总测试数 ($total_tests)"
        return 1
    fi

    log_pass "CI 状态检查通过 (status=$status, tests=$total_tests, passed=$passed)"
    return 0
}

# 门禁 2: 评审报告完整性检查
check_review_completeness() {
    local change_dir=$1
    local review_dir="$change_dir/coding/review"

    log_info "检查评审报告完整性: $change_dir"

    # 检查评审目录是否存在
    if [[ ! -d "$review_dir" ]]; then
        log_fail "评审目录不存在: $review_dir"
        return 1
    fi

    # 查找最新的评审报告
    local latest_review=$(ls -t "$review_dir"/code_review_v*.md 2>/dev/null | head -1)
    if [[ -z "$latest_review" ]]; then
        log_fail "评审报告不存在"
        return 1
    fi

    # 检查必填章节
    local required_sections=("问题描述" "修改建议" "优先级分级")
    local missing_sections=()

    for section in "${required_sections[@]}"; do
        if ! grep -q "## $section" "$latest_review"; then
            missing_sections+=("$section")
        fi
    done

    if [[ ${#missing_sections[@]} -gt 0 ]]; then
        log_fail "评审报告缺少必填章节:"
        for section in "${missing_sections[@]}"; do
            echo "  - $section"
        done
        return 1
    fi

    log_pass "评审报告完整性检查通过"
    return 0
}

# 门禁 3: 文档同步检查
check_doc_sync() {
    local change_dir=$1

    log_info "检查文档同步: $change_dir"

    # 检查编码报告是否存在
    local coding_report=$(ls -t "$change_dir/coding"/coding_report_v*.md 2>/dev/null | head -1)
    if [[ -z "$coding_report" ]]; then
        log_fail "编码报告不存在"
        return 1
    fi

    # 检查是否包含文档更新记录
    if ! grep -q "文档更新" "$coding_report"; then
        log_warn "编码报告中未找到文档更新记录"
    fi

    log_pass "文档同步检查通过"
    return 0
}

# 门禁 4: 变更完整性检查
check_change_completeness() {
    local change_dir=$1

    log_info "检查变更完整性: $change_dir"

    # 检查必需的目录结构
    local required_dirs=("request_analysis" "coding" "unit_test" "ci_result")
    local missing_dirs=()

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$change_dir/$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done

    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log_fail "变更目录缺少必需的子目录:"
        for dir in "${missing_dirs[@]}"; do
            echo "  - $dir"
        done
        return 1
    fi

    # 检查必需的文件
    local required_files=("summary.md" "request_analysis/spec.md" "request_analysis/tasks.md")
    local missing_files=()

    for file in "${required_files[@]}"; do
        if [[ ! -f "$change_dir/$file" ]]; then
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_fail "变更目录缺少必需的文件:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi

    log_pass "变更完整性检查通过"
    return 0
}

# 门禁 5: 代码规范检查
check_code_standards() {
    local code_file=$1

    log_info "检查代码规范: $code_file"

    # 检查是否有 TODO/FIXME/HACK
    local todos=$(grep -cP "(TODO|FIXME|HACK|XXX)" "$code_file" 2>/dev/null || echo "0")

    if [[ $todos -gt 0 ]]; then
        log_warn "发现 $todos 个 TODO/FIXME/HACK 标记"
    fi

    # 检查是否有调试代码
    local debug_code=$(grep -cP "(printf|printk|console\.log|debugger)" "$code_file" 2>/dev/null || echo "0")

    if [[ $debug_code -gt 0 ]]; then
        log_warn "发现 $debug_code 个可能的调试代码"
    fi

    log_pass "代码规范检查通过"
    return 0
}

# 主函数
main() {
    local change_dir=$1

    if [[ ! -d "$change_dir" ]]; then
        log_fail "变更目录不存在: $change_dir"
        exit 1
    fi

    echo "=========================================="
    echo "通用质量门禁检查"
    echo "=========================================="
    echo "变更目录: $change_dir"
    echo "=========================================="

    local failed=0

    # 执行所有门禁检查
    check_change_completeness "$change_dir" || failed=1
    check_ci_status "$change_dir" || failed=1
    check_review_completeness "$change_dir" || failed=1
    check_doc_sync "$change_dir" || failed=1

    echo "=========================================="
    if [[ $failed -eq 0 ]]; then
        log_pass "所有门禁检查通过"
        exit 0
    else
        log_fail "部分门禁检查失败"
        exit 1
    fi
}

# 使用说明
usage() {
    echo "用法: $0 <变更目录>"
    echo ""
    echo "示例:"
    echo "  $0 changes/add-modbus-tcp"
    echo "  $0 /path/to/change/dir"
    echo ""
    echo "门禁检查项:"
    echo "  1. 变更完整性检查"
    echo "  2. CI 状态检查"
    echo "  3. 评审报告完整性检查"
    echo "  4. 文档同步检查"
    echo "  5. 代码规范检查"
}

# 参数检查
if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

# 执行主函数
main "$@"
