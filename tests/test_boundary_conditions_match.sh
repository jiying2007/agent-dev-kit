#!/usr/bin/env bash
set -euo pipefail

# 边界条件测试 - skill_match.sh match 函数
# 测试: 空输入、超长输入、特殊字符、Unicode/emoji、
#       全部22个routing关键词逐一匹配、多'/'的intent_zh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MATCH_SCRIPT="$ROOT_DIR/scripts/skill_match.sh"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# 测试计数
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_func="$2"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "Testing $test_name... "

    if $test_func; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# ============================================================
# 边界条件: 空字符串输入
# ============================================================
test_empty_string() {
    local output
    output=$("$MATCH_SCRIPT" --text "" 2>&1) || true
    # 空输入应 match=false 或 报错
    [[ "$output" == *"match=false"* || "$output" == *"FAIL"* ]]
}

# ============================================================
# 边界条件: 超长输入 (1000+ 字符)
# ============================================================
test_very_long_input() {
    local long_text
    long_text=$(printf '%0.sA' $(seq 1 1024))
    local output
    output=$("$MATCH_SCRIPT" --text "$long_text" 2>&1) || true
    # 不应崩溃，应返回 match=false
    [[ "$output" == *"match=false"* ]]
}

# ============================================================
# 边界条件: 特殊字符 - 双引号
# ============================================================
test_special_chars_double_quotes() {
    local output
    output=$("$MATCH_SCRIPT" --text '输入包含"双引号"的文本' 2>&1) || true
    [[ "$output" == *"match="* ]]
}

# ============================================================
# 边界条件: 特殊字符 - 单引号
# ============================================================
test_special_chars_single_quotes() {
    local output
    output=$("$MATCH_SCRIPT" --text "输入包含'单引号'的文本" 2>&1) || true
    [[ "$output" == *"match="* ]]
}

# ============================================================
# 边界条件: 特殊字符 - 反斜杠
# ============================================================
test_special_chars_backslash() {
    local output
    output=$("$MATCH_SCRIPT" --text '路径C:\windows\system32' 2>&1) || true
    [[ "$output" == *"match="* ]]
}

# ============================================================
# 边界条件: 特殊字符 - 管道符
# ============================================================
test_special_chars_pipe() {
    local output
    output=$("$MATCH_SCRIPT" --text 'echo "hello" | grep hello' 2>&1) || true
    [[ "$output" == *"match="* ]]
}

# ============================================================
# 边界条件: Unicode 中文
# ============================================================
test_unicode_chinese() {
    local output
    output=$("$MATCH_SCRIPT" --text '需求不清楚，需要澄清一下这个功能' 2>&1) || true
    [[ "$output" == *"match=true"* ]]
}

# ============================================================
# 边界条件: Emoji 输入
# ============================================================
test_emoji_input() {
    local output
    output=$("$MATCH_SCRIPT" --text '🚗 驱动开发需要帮忙 🚀' 2>&1) || true
    # 应能匹配到 driver-bringup-checklist
    [[ "$output" == *"match=true"* ]]
}

# ============================================================
# 边界条件: Unicode 混合
# ============================================================
test_unicode_mixed() {
    local output
    output=$("$MATCH_SCRIPT" --text 'Write 单元测试 for module' 2>&1) || true
    [[ "$output" == *"match=true"* ]]
}

# ============================================================
# 22 个 Routing 关键词逐一匹配测试
# ============================================================

# 1. requirements-triage
test_routing_01_needs_triage() {
    local output
    output=$("$MATCH_SCRIPT" --text "需求不清楚" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=requirements-triage"* ]]
}

# 2. task-breakdown
test_routing_02_task_breakdown() {
    local output
    output=$("$MATCH_SCRIPT" --text "拆解大任务" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=task-breakdown"* ]]
}

# 3. interface-contract-design
test_routing_03_interface_design() {
    local output
    output=$("$MATCH_SCRIPT" --text "设计接口" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=interface-contract-design"* ]]
}

# 4. unit-test-embedded
test_routing_04_unit_test() {
    local output
    output=$("$MATCH_SCRIPT" --text "写单元测试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=unit-test-embedded"* ]]
}

# 5. static-analysis-c-cpp
test_routing_05_static_analysis() {
    local output
    output=$("$MATCH_SCRIPT" --text "静态分析" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=static-analysis-c-cpp"* ]]
}

# 6. systematic-debugging
test_routing_06_debugging() {
    local output
    output=$("$MATCH_SCRIPT" --text "调试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=systematic-debugging"* ]]
}

# 7. verification-before-completion
test_routing_07_ready_to_complete() {
    local output
    output=$("$MATCH_SCRIPT" --text "准备完成" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=verification-before-completion"* ]]
}

# 8. commit-pr-quality-gate
test_routing_08_submit_code() {
    local output
    output=$("$MATCH_SCRIPT" --text "提交代码" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=commit-pr-quality-gate"* ]]
}

# 9. adr-writer
test_routing_09_adr() {
    local output
    output=$("$MATCH_SCRIPT" --text "写ADR" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adr-writer"* ]]
}

# 10. register-map-design
test_routing_10_register_map() {
    local output
    output=$("$MATCH_SCRIPT" --text "设计寄存器映射" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=register-map-design"* ]]
}

# 11. driver-bringup-checklist
test_routing_11_driver_bringup() {
    local output
    output=$("$MATCH_SCRIPT" --text "驱动开发" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=driver-bringup-checklist"* ]]
}

# 12. bsp-porting-playbook
test_routing_12_bsp_porting() {
    local output
    output=$("$MATCH_SCRIPT" --text "BSP移植" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=bsp-porting-playbook"* ]]
}

# 13. rtos-task-design
test_routing_13_rtos_task() {
    local output
    output=$("$MATCH_SCRIPT" --text "RTOS任务设计" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=rtos-task-design"* ]]
}

# 14. interrupt-dma-patterns
test_routing_14_interrupt_dma() {
    local output
    output=$("$MATCH_SCRIPT" --text "中断处理" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=interrupt-dma-patterns"* ]]
}

# 15. protocol-stack-integration
test_routing_15_protocol_stack() {
    local output
    output=$("$MATCH_SCRIPT" --text "协议栈集成" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=protocol-stack-integration"* ]]
}

# 16. component-api-stability
test_routing_16_api_stability() {
    local output
    output=$("$MATCH_SCRIPT" --text "API稳定性" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=component-api-stability"* ]]
}

# 17. cmake-cross-build
test_routing_17_cmake_cross() {
    local output
    output=$("$MATCH_SCRIPT" --text "CMake交叉编译" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=cmake-cross-build"* ]]
}

# 18. toolchain-debug-openocd-gdb
test_routing_18_openocd_gdb() {
    local output
    output=$("$MATCH_SCRIPT" --text "OpenOCD" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=toolchain-debug-openocd-gdb"* ]]
}

# 19. integration-hil-sil
test_routing_19_hil_sil() {
    local output
    output=$("$MATCH_SCRIPT" --text "HIL/SIL集成测试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=integration-hil-sil"* ]]
}

# 20. fault-injection-recovery
test_routing_20_fault_injection() {
    local output
    output=$("$MATCH_SCRIPT" --text "故障注入测试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=fault-injection-recovery"* ]]
}

# 21. performance-profiling-embedded
test_routing_21_performance() {
    local output
    output=$("$MATCH_SCRIPT" --text "性能分析" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=performance-profiling-embedded"* ]]
}

# 22. release-versioning
test_routing_22_release() {
    local output
    output=$("$MATCH_SCRIPT" --text "版本发布" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=release-versioning"* ]]
}

# ============================================================
# 边界条件: intent_zh 中多 '/' 分隔符
# ============================================================
test_multi_slash_intent_zh_first() {
    # "需求不清楚/需要澄清/需求模糊/需求不明确" - 匹配第一段
    local output
    output=$("$MATCH_SCRIPT" --text "需求模糊" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=requirements-triage"* ]]
}

test_multi_slash_intent_zh_last() {
    # "需求不清楚/需要澄清/需求模糊/需求不明确" - 匹配最后一段
    local output
    output=$("$MATCH_SCRIPT" --text "需求不明确" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=requirements-triage"* ]]
}

test_multi_slash_intent_zh_substring() {
    # "驱动开发/驱动调试/写驱动/驱动bringup" - 匹配写驱动段
    local output
    output=$("$MATCH_SCRIPT" --text "写驱动" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=driver-bringup-checklist"* ]]
}

test_multi_slash_intent_zh_partial() {
    # "中断处理/DMA处理/中断DMA" - 匹配部分
    local output
    output=$("$MATCH_SCRIPT" --text "DMA处理" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=interrupt-dma-patterns"* ]]
}

# ============================================================
# 运行所有测试
# ============================================================
echo "Running match boundary condition tests..."
echo "=========================================="

# 边界条件测试
run_test "Empty string input" test_empty_string
run_test "Very long input (1024 chars)" test_very_long_input
run_test "Special chars: double quotes" test_special_chars_double_quotes
run_test "Special chars: single quotes" test_special_chars_single_quotes
run_test "Special chars: backslash" test_special_chars_backslash
run_test "Special chars: pipe" test_special_chars_pipe
run_test "Unicode Chinese" test_unicode_chinese
run_test "Emoji input" test_emoji_input
run_test "Unicode mixed (EN+CN)" test_unicode_mixed

# 22 routing keyword tests
run_test "Routing 01: requirements-triage" test_routing_01_needs_triage
run_test "Routing 02: task-breakdown" test_routing_02_task_breakdown
run_test "Routing 03: interface-contract-design" test_routing_03_interface_design
run_test "Routing 04: unit-test-embedded" test_routing_04_unit_test
run_test "Routing 05: static-analysis-c-cpp" test_routing_05_static_analysis
run_test "Routing 06: systematic-debugging" test_routing_06_debugging
run_test "Routing 07: verification-before-completion" test_routing_07_ready_to_complete
run_test "Routing 08: commit-pr-quality-gate" test_routing_08_submit_code
run_test "Routing 09: adr-writer" test_routing_09_adr
run_test "Routing 10: register-map-design" test_routing_10_register_map
run_test "Routing 11: driver-bringup-checklist" test_routing_11_driver_bringup
run_test "Routing 12: bsp-porting-playbook" test_routing_12_bsp_porting
run_test "Routing 13: rtos-task-design" test_routing_13_rtos_task
run_test "Routing 14: interrupt-dma-patterns" test_routing_14_interrupt_dma
run_test "Routing 15: protocol-stack-integration" test_routing_15_protocol_stack
run_test "Routing 16: component-api-stability" test_routing_16_api_stability
run_test "Routing 17: cmake-cross-build" test_routing_17_cmake_cross
run_test "Routing 18: toolchain-debug-openocd-gdb" test_routing_18_openocd_gdb
run_test "Routing 19: integration-hil-sil" test_routing_19_hil_sil
run_test "Routing 20: fault-injection-recovery" test_routing_20_fault_injection
run_test "Routing 21: performance-profiling-embedded" test_routing_21_performance
run_test "Routing 22: release-versioning" test_routing_22_release

# Multi-slash intent_zh tests
run_test "Multi-slash: first segment" test_multi_slash_intent_zh_first
run_test "Multi-slash: last segment" test_multi_slash_intent_zh_last
run_test "Multi-slash: middle segment" test_multi_slash_intent_zh_substring
run_test "Multi-slash: partial match" test_multi_slash_intent_zh_partial

echo "=========================================="
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All match boundary condition tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some match boundary condition tests failed${NC}"
    exit 1
fi
