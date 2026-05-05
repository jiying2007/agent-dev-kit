#!/usr/bin/env bash
set -euo pipefail

# 测试 match 自动匹配功能端到端验证

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MATCH_SCRIPT="$ROOT_DIR/scripts/skill_match.sh"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

# --- 正向测试用例 (should match with source=routing) ---

test_routing_needs_triage() {
    local output
    output=$("$MATCH_SCRIPT" --text "需求不清楚" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=requirements-triage"* ]]
}

test_routing_task_breakdown() {
    local output
    output=$("$MATCH_SCRIPT" --text "任务太大" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=task-breakdown"* ]]
}

test_routing_unit_test() {
    local output
    output=$("$MATCH_SCRIPT" --text "写单元测试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=unit-test-embedded"* ]]
}

test_routing_debugging() {
    local output
    output=$("$MATCH_SCRIPT" --text "调试问题" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=systematic-debugging"* ]]
}

test_routing_commit_pr() {
    local output
    output=$("$MATCH_SCRIPT" --text "提交代码" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=commit-pr-quality-gate"* ]]
}

test_routing_register_map() {
    local output
    output=$("$MATCH_SCRIPT" --text "设计寄存器" 2>&1) || true
    # 路由表 intent_zh 为"设计寄存器映射"，输入"设计寄存器"通过 skill_trigger 匹配
    [[ "$output" == *"match=true"* && "$output" == *"skill=register-map-design"* ]]
}

test_routing_driver() {
    local output
    output=$("$MATCH_SCRIPT" --text "写驱动" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=driver-bringup-checklist"* ]]
}

test_routing_release() {
    local output
    output=$("$MATCH_SCRIPT" --text "准备发布" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=release-versioning"* ]]
}

test_routing_bsp() {
    local output
    output=$("$MATCH_SCRIPT" --text "BSP移植" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=bsp-porting-playbook"* ]]
}

test_routing_performance() {
    local output
    output=$("$MATCH_SCRIPT" --text "性能分析" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=performance-profiling-embedded"* ]]
}

# --- 负向测试用例 (should NOT match) ---

test_negative_unrelated_xyz() {
    local output rc=0
    output=$("$MATCH_SCRIPT" --text "完全无关的文本xyz" 2>&1) || rc=$?
    [[ "$output" == *"match=false"* && $rc -ne 0 ]]
}

test_negative_weather() {
    local output rc=0
    output=$("$MATCH_SCRIPT" --text "今天天气很好" 2>&1) || rc=$?
    [[ "$output" == *"match=false"* && $rc -ne 0 ]]
}

test_negative_abc() {
    local output rc=0
    output=$("$MATCH_SCRIPT" --text "abc123" 2>&1) || rc=$?
    [[ "$output" == *"match=false"* && $rc -ne 0 ]]
}

# 运行所有测试
echo "=== Match Effectiveness Tests ==="
echo "================================="

echo ""
echo "--- Positive cases (should match routing) ---"
run_test "需求不清楚 -> requirements-triage" test_routing_needs_triage
run_test "任务太大 -> task-breakdown" test_routing_task_breakdown
run_test "写单元测试 -> unit-test-embedded" test_routing_unit_test
run_test "调试问题 -> systematic-debugging" test_routing_debugging
run_test "提交代码 -> commit-pr-quality-gate" test_routing_commit_pr
run_test "设计寄存器 -> register-map-design" test_routing_register_map
run_test "写驱动 -> driver-bringup-checklist" test_routing_driver
run_test "准备发布 -> release-versioning" test_routing_release
run_test "BSP移植 -> bsp-porting-playbook" test_routing_bsp
run_test "性能分析 -> performance-profiling-embedded" test_routing_performance

echo ""
echo "--- Negative cases (should not match) ---"
run_test "完全无关的文本xyz -> no match" test_negative_unrelated_xyz
run_test "今天天气很好 -> no match" test_negative_weather
run_test "abc123 -> no match" test_negative_abc

echo ""
echo "================================="
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All match effectiveness tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some match effectiveness tests failed${NC}"
    exit 1
fi
