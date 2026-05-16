#!/usr/bin/env bash
# scripts/quality-gates-embedded.sh
# 嵌入式专用质量门禁脚本
#
# 用途：检查嵌入式代码的安全性和规范性
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

# 门禁 1: 内核 API 版本检查
check_kernel_api_version() {
    local code_file=$1
    local kernel_version=${2:-"5.10"}

    log_info "检查内核 API 版本: $code_file (目标版本: $kernel_version)"

    # 检查是否使用了过时的 API
    # 这里只是示例，实际需要根据具体内核版本维护过时 API 列表
    local deprecated_apis=(
        "ioremap_nocache"    # 5.6+ 改用 ioremap
        "pci_dma_supported"  # 5.10+ 改用 dma_supported
        "virt_to_phys"       # 不推荐用于新代码
    )

    local found_deprecated=0
    for api in "${deprecated_apis[@]}"; do
        if grep -q "$api" "$code_file" 2>/dev/null; then
            log_warn "发现可能过时的 API: $api"
            found_deprecated=1
        fi
    done

    if [[ $found_deprecated -eq 1 ]]; then
        log_warn "发现可能过时的内核 API，请人工确认是否适用于内核版本 $kernel_version"
        return 0  # 警告不阻塞
    fi

    log_pass "内核 API 版本检查通过"
    return 0
}

# 门禁 2: 中断安全性检查
check_interrupt_safety() {
    local code_file=$1

    log_info "检查中断安全性: $code_file"

    # 检查中断处理函数中是否有禁用调用
    local forbidden_calls=(
        "mutex_lock"
        "kmalloc.*GFP_KERNEL"
        "dev_info"
        "msleep"
        "usleep"
        "ssleep"
        "schedule_timeout"
        "wait_for_completion"
        "spin_lock_irqsave"  # 需要确认是否有对应的 spin_unlock_irqrestore
    )

    local violations=()
    for call in "${forbidden_calls[@]}"; do
        if grep -qP "$call" "$code_file" 2>/dev/null; then
            violations+=("$call")
        fi
    done

    if [[ ${#violations[@]} -gt 0 ]]; then
        log_fail "中断处理函数中发现禁用调用:"
        for violation in "${violations[@]}"; do
            echo "  - $violation"
        done
        return 1
    fi

    log_pass "中断安全性检查通过"
    return 0
}

# 门禁 3: 寄存器位定义验证
check_register_bit_definition() {
    local code_file=$1

    log_info "检查寄存器位定义: $code_file"

    # 检查是否有寄存器定义但没有引用 datasheet
    local has_register_def=$(grep -cP "#define\s+\w+_(REG|CTRL|STATUS|CONFIG)" "$code_file" 2>/dev/null || echo "0")
    local has_datasheet_ref=$(grep -cP "(datasheet|RM|page|section)" "$code_file" 2>/dev/null || echo "0")

    if [[ $has_register_def -gt 0 ]] && [[ $has_datasheet_ref -eq 0 ]]; then
        log_warn "发现寄存器定义但未引用 datasheet，请确认是否需要添加引用"
        return 0  # 警告不阻塞
    fi

    log_pass "寄存器位定义验证通过"
    return 0
}

# 门禁 4: 内存约束检查
check_memory_constraints() {
    local code_file=$1
    local stack_limit=${2:-2048}  # 默认 2KB

    log_info "检查内存约束: $code_file (栈限制: ${stack_limit} bytes)"

    # 检查是否有大数组在栈上
    local large_arrays=$(grep -nP "(char|int|uint8_t|uint16_t|uint32_t)\s+\w+\[" "$code_file" 2>/dev/null | grep -v "^\s*//" || true)

    if [[ -n "$large_arrays" ]]; then
        log_warn "发现可能的大数组在栈上，请确认是否超过栈限制:"
        echo "$large_arrays" | head -5
        return 0  # 警告不阻塞
    fi

    log_pass "内存约束检查通过"
    return 0
}

# 门禁 5: DMA 安全性检查
check_dma_safety() {
    local code_file=$1

    log_info "检查 DMA 安全性: $code_file"

    # 检查 DMA 相关代码是否有同步机制
    local has_dma=$(grep -cP "dma_|DMA_" "$code_file" 2>/dev/null || echo "0")
    local has_barrier=$(grep -cP "(mb|rmb|wmb|dma_wmb|dma_rmb|smp_mb)" "$code_file" 2>/dev/null || echo "0")

    if [[ $has_dma -gt 0 ]] && [[ $has_barrier -eq 0 ]]; then
        log_warn "发现 DMA 操作但未使用内存屏障，请确认是否需要添加同步机制"
        return 0  # 警告不阻塞
    fi

    log_pass "DMA 安全性检查通过"
    return 0
}

# 门禁 6: 并发安全性检查
check_concurrency_safety() {
    local code_file=$1

    log_info "检查并发安全性: $code_file"

    # 检查是否有全局变量但没有锁保护
    local global_vars=$(grep -nP "^(static|extern)\s+\w+\s+\w+" "$code_file" 2>/dev/null | grep -v "const" || true)
    local has_lock=$(grep -cP "(spin_lock|mutex_lock|atomic_t)" "$code_file" 2>/dev/null || echo "0")

    if [[ -n "$global_vars" ]] && [[ $has_lock -eq 0 ]]; then
        log_warn "发现全局变量但未使用锁保护，请确认是否需要添加同步机制"
        return 0  # 警告不阻塞
    fi

    log_pass "并发安全性检查通过"
    return 0
}

# 主函数
main() {
    local code_file=$1
    local kernel_version=${2:-"5.10"}

    if [[ ! -f "$code_file" ]]; then
        log_fail "文件不存在: $code_file"
        exit 1
    fi

    echo "=========================================="
    echo "嵌入式专用质量门禁检查"
    echo "=========================================="
    echo "文件: $code_file"
    echo "内核版本: $kernel_version"
    echo "=========================================="

    local failed=0

    # 执行所有门禁检查
    check_kernel_api_version "$code_file" "$kernel_version" || failed=1
    check_interrupt_safety "$code_file" || failed=1
    check_register_bit_definition "$code_file" || failed=1
    check_memory_constraints "$code_file" || failed=1
    check_dma_safety "$code_file" || failed=1
    check_concurrency_safety "$code_file" || failed=1

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
    echo "用法: $0 <代码文件> [内核版本]"
    echo ""
    echo "示例:"
    echo "  $0 driver.c 5.10"
    echo "  $0 /path/to/file.c 5.15"
    echo ""
    echo "门禁检查项:"
    echo "  1. 内核 API 版本检查"
    echo "  2. 中断安全性检查"
    echo "  3. 寄存器位定义验证"
    echo "  4. 内存约束检查"
    echo "  5. DMA 安全性检查"
    echo "  6. 并发安全性检查"
}

# 参数检查
if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

# 执行主函数
main "$@"
