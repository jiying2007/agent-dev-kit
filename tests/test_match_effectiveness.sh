#!/usr/bin/env bash
set -euo pipefail

# 测试 match 自动匹配功能端到端验证

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MATCH_SCRIPT="$ROOT_DIR/scripts/skill-match.sh"

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
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-requirements-triage"* ]]
}

test_routing_runtime_router() {
    local output
    output=$("$MATCH_SCRIPT" --text "开始任务前判断使用哪个技能" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-runtime-router"* ]]
}

test_routing_feature_triage_natural_language() {
    local output
    output=$("$MATCH_SCRIPT" --text "帮我实现一个新功能，需要先明确目标、边界和验收标准" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-requirements-triage"* ]]
}

test_routing_test_strategy() {
    local output
    output=$("$MATCH_SCRIPT" --text "这个功能需要先写测试并设计测试矩阵" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-test-strategy"* ]]
}

test_routing_code_review_loop() {
    local output
    output=$("$MATCH_SCRIPT" --text "收到 review 反馈后需要做审查反馈闭环" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-code-review-loop"* ]]
}

test_routing_parallel_agent_governance() {
    local output
    output=$("$MATCH_SCRIPT" --text "多 agent 并行施工需要明确 scope_write" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-parallel-agent-governance"* ]]
}

test_routing_worktree_governance() {
    local output
    output=$("$MATCH_SCRIPT" --text "需要创建 worktree 做隔离分支开发" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-worktree-governance"* ]]
}

test_routing_branch_closeout() {
    local output
    output=$("$MATCH_SCRIPT" --text "开发完成后准备创建 PR 并做分支收尾" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-branch-closeout"* ]]
}

test_routing_task_breakdown() {
    local output
    output=$("$MATCH_SCRIPT" --text "任务太大" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-task-breakdown"* ]]
}

test_routing_unit_test() {
    local output
    output=$("$MATCH_SCRIPT" --text "写单元测试" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-unit-test-embedded"* ]]
}

test_routing_debugging() {
    local output
    output=$("$MATCH_SCRIPT" --text "调试问题" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-systematic-debugging"* ]]
}

test_routing_debugging_natural_language() {
    local output
    output=$("$MATCH_SCRIPT" --text "真实问题排查需要定位根因再修复" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-systematic-debugging"* ]]
}

test_routing_commit_pr() {
    local output
    output=$("$MATCH_SCRIPT" --text "提交代码" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-commit-pr-quality-gate"* ]]
}

test_routing_register_map() {
    local output
    output=$("$MATCH_SCRIPT" --text "设计寄存器" 2>&1) || true
    # 路由表 intent_zh 为"设计寄存器映射"，输入"设计寄存器"通过 skill_trigger 匹配
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-register-map-design"* ]]
}

test_routing_driver() {
    local output
    output=$("$MATCH_SCRIPT" --text "写驱动" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-driver-bringup-checklist"* ]]
}

test_routing_release() {
    local output
    output=$("$MATCH_SCRIPT" --text "准备发布" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-release-versioning"* ]]
}

test_routing_bsp() {
    local output
    output=$("$MATCH_SCRIPT" --text "BSP移植" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-bsp-porting-playbook"* ]]
}

test_routing_boot_chain() {
    local output
    output=$("$MATCH_SCRIPT" --text "启动链 bring-up BootROM SPL U-Boot kernel rootfs" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-bsp-porting-playbook"* ]]
}

test_routing_production_field() {
    local output
    output=$("$MATCH_SCRIPT" --text "量产产测诊断烧录 OTA升级 回滚 现场维护" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-production-field-readiness"* ]]
}

test_routing_performance() {
    local output
    output=$("$MATCH_SCRIPT" --text "性能分析" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-performance-profiling-embedded"* ]]
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
run_test "开始任务前判断技能 -> adk-runtime-router" test_routing_runtime_router
run_test "需求不清楚 -> adk-requirements-triage" test_routing_needs_triage
run_test "新功能自然语言 -> adk-requirements-triage" test_routing_feature_triage_natural_language
run_test "测试矩阵 -> adk-test-strategy" test_routing_test_strategy
run_test "review 反馈闭环 -> adk-code-review-loop" test_routing_code_review_loop
run_test "多 agent 并行 -> adk-parallel-agent-governance" test_routing_parallel_agent_governance
run_test "worktree 隔离 -> adk-worktree-governance" test_routing_worktree_governance
run_test "分支收尾 -> adk-branch-closeout" test_routing_branch_closeout
run_test "任务太大 -> adk-task-breakdown" test_routing_task_breakdown
run_test "写单元测试 -> adk-unit-test-embedded" test_routing_unit_test
run_test "调试问题 -> adk-systematic-debugging" test_routing_debugging
run_test "真实问题排查 -> adk-systematic-debugging" test_routing_debugging_natural_language
run_test "提交代码 -> adk-commit-pr-quality-gate" test_routing_commit_pr
run_test "设计寄存器 -> adk-register-map-design" test_routing_register_map
run_test "写驱动 -> adk-driver-bringup-checklist" test_routing_driver
run_test "准备发布 -> adk-release-versioning" test_routing_release
run_test "BSP移植 -> adk-bsp-porting-playbook" test_routing_bsp
run_test "启动链 -> adk-bsp-porting-playbook" test_routing_boot_chain
run_test "量产现场 -> adk-production-field-readiness" test_routing_production_field
run_test "性能分析 -> adk-performance-profiling-embedded" test_routing_performance

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
