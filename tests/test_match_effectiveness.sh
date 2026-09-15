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

test_routing_external_name_review_intent() {
    local output
    output=$("$MATCH_SCRIPT" --text "Superpowers receiving-code-review：review 反馈核验，冻结 HEAD 和工作树叠加后判断是真实缺陷还是误报" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-code-review-loop"* && "$output" != *"skill=adk-worktree-governance"* ]]
}

test_routing_parallel_agent_governance() {
    local output
    output=$("$MATCH_SCRIPT" --text "多 agent 并行施工需要明确 scope_write" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-parallel-agent-governance"* ]]
}

test_routing_parallel_agent_over_driver_phrase() {
    local output
    output=$("$MATCH_SCRIPT" --text "子代理驱动开发并复审" 2>&1) || true
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

test_routing_production_field_pilot_id() {
    local output
    output=$("$MATCH_SCRIPT" --text "embedded-production-field-readiness，模拟设备自动推进" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"skill=adk-production-field-readiness"* ]]
}

test_routing_performance() {
    local output
    output=$("$MATCH_SCRIPT" --text "性能分析" 2>&1) || true
    [[ "$output" == *"match=true"* && "$output" == *"source=routing"* && "$output" == *"skill=adk-performance-profiling-embedded"* ]]
}

test_routing_planning_execution_positive() {
    local output
    output=$("$MATCH_SCRIPT" --text "长任务，需要执行计划并分阶段执行" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"source=routing"* &&
       "$output" == *"skill=adk-planning-execution-loop"* &&
       "$output" == *"task_mode=implementation"* &&
       "$output" == *"mutation_permission=workspace-write"* &&
       "$output" == *"artifact_mode=implementation"* ]]
}

test_routing_debugging_contrastive_positive() {
    local output
    output=$("$MATCH_SCRIPT" --text "根因未明，需要调试并定位根因" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"skill=adk-systematic-debugging"* &&
       "$output" == *"task_mode=debugging"* &&
       "$output" == *"mutation_permission=deny"* &&
       "$output" == *"artifact_mode=readonly"* ]]
}

test_routing_debugging_intent_caps_implementation_signal() {
    local output
    output=$("$MATCH_SCRIPT" --text "根因未明，需要调试并修复" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"skill=adk-systematic-debugging"* &&
       "$output" == *"task_mode=debugging"* &&
       "$output" == *"mutation_permission=deny"* &&
       "$output" == *"artifact_mode=readonly"* ]]
}

test_negated_non_trigger_does_not_veto_debugging() {
    local output
    output=$("$MATCH_SCRIPT" --text "这不是纯文档或命名修改；根因未明，请调试并定位根因" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"skill=adk-systematic-debugging"* &&
       "$output" == *"task_mode=debugging"* &&
       "$output" == *"mutation_permission=deny"* ]]
}

test_routing_release_contrastive_positive() {
    local output
    output=$("$MATCH_SCRIPT" --text "准备发布并执行发布前检查" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"skill=adk-release-versioning"* &&
       "$output" == *"task_mode=release"* &&
       "$output" == *"mutation_permission=explicit-authorization-required"* &&
       "$output" == *"artifact_mode=release"* ]]
}

test_review_maps_to_readonly_artifacts() {
    local output
    output=$("$MATCH_SCRIPT" --text "代码审查" 2>&1) || true
    [[ "$output" == *"match=true"* &&
       "$output" == *"skill=adk-code-review-loop"* &&
       "$output" == *"task_mode=review"* &&
       "$output" == *"mutation_permission=deny"* &&
       "$output" == *"artifact_mode=readonly"* ]]
}

# --- 负向测试用例 (should NOT match) ---

assert_readonly_abstain() {
    local text="$1"
    local negated_intent="$2"
    local output rc=0
    output=$("$MATCH_SCRIPT" --text "$text" 2>&1) || rc=$?
    [[ $rc -ne 0 &&
       "$output" == *"match=false"* &&
       "$output" == *"decision=abstain"* &&
       "$output" == *"reason=needs-triage"* &&
       "$output" == *"task_mode=readonly"* &&
       "$output" == *"mutation_permission=deny"* &&
       "$output" == *"artifact_mode=readonly"* &&
       "$output" == *"negated_intents="*"$negated_intent"* ]]
}

test_negative_readonly_long_task() {
    assert_readonly_abstain \
        "长任务但只做只读分析且无需执行计划" \
        "planning_execution"
}

test_negative_architecture_without_debugging() {
    assert_readonly_abstain \
        "根因不明但不要调试只做架构评估" \
        "systematic_debugging"
}

test_negative_release_explanation_only() {
    assert_readonly_abstain \
        "准备发布但只需要解释现状不执行发布" \
        "release_versioning"
}

test_negation_phrase_classes_metamorphic_planning() {
    local marker
    assert_readonly_abstain \
        "长任务，只分析，不需要执行计划" \
        "planning_execution" || return 1
    for marker in "无需" "别" "不要" "请勿" "不过别"; do
        assert_readonly_abstain \
            "长任务，只读分析，${marker}执行计划" \
            "planning_execution" || return 1
    done
}

test_negation_phrase_classes_metamorphic_debugging() {
    local marker
    for marker in "不需要" "无需" "别" "不要" "请勿" "不过别"; do
        assert_readonly_abstain \
            "根因不明，只做架构评估，${marker}调试" \
            "systematic_debugging" || return 1
    done
}

test_negation_phrase_classes_metamorphic_release() {
    local marker
    assert_readonly_abstain \
        "准备发布，不过请勿执行，只说明现状" \
        "release_versioning" || return 1
    for marker in "不需要" "无需" "别" "不要" "不过别"; do
        assert_readonly_abstain \
            "准备发布，只说明现状，${marker}发布" \
            "release_versioning" || return 1
    done
}

test_multiturn_latest_turn_release_to_readonly() {
    local turn1 turn2 turn2_rc=0
    turn1=$("$MATCH_SCRIPT" --text "准备发布" 2>&1) || return 1
    turn2=$("$MATCH_SCRIPT" --text "只说明现状不执行" 2>&1) || turn2_rc=$?
    [[ "$turn1" == *"match=true"* &&
       "$turn1" == *"skill=adk-release-versioning"* &&
       "$turn1" == *"task_mode=release"* &&
       "$turn1" == *"mutation_permission=explicit-authorization-required"* &&
       $turn2_rc -ne 0 &&
       "$turn2" == *"decision=abstain"* &&
       "$turn2" == *"task_mode=readonly"* &&
       "$turn2" == *"mutation_permission=deny"* ]]
}

test_multiturn_latest_turn_readonly_to_implementation() {
    local turn1 turn1_rc=0 turn2
    turn1=$("$MATCH_SCRIPT" --text "仅做架构评估" 2>&1) || turn1_rc=$?
    turn2=$("$MATCH_SCRIPT" --text "现在明确授权实现新功能并修改代码" 2>&1) || return 1
    [[ $turn1_rc -ne 0 &&
       "$turn1" == *"decision=abstain"* &&
       "$turn1" == *"task_mode=readonly"* &&
       "$turn1" == *"mutation_permission=deny"* &&
       "$turn2" == *"match=true"* &&
       "$turn2" == *"skill=adk-requirements-triage"* &&
       "$turn2" == *"task_mode=implementation"* &&
       "$turn2" == *"mutation_permission=deny"* &&
       "$turn2" != *"task_mode=readonly"* ]]
}

test_negative_unrelated_xyz() {
    local output rc=0
    output=$("$MATCH_SCRIPT" --text "完全无关的文本xyz" 2>&1) || rc=$?
    [[ "$output" == *"match=false"* && "$output" == *"decision=abstain"* &&
       "$output" == *"reason=needs-triage"* && "$output" == *"artifact_mode=not-applicable"* &&
       $rc -ne 0 ]]
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
run_test "外部 Skill 名称只保留 review 意图 -> adk-code-review-loop" test_routing_external_name_review_intent
run_test "多 agent 并行 -> adk-parallel-agent-governance" test_routing_parallel_agent_governance
run_test "子代理驱动开发 -> adk-parallel-agent-governance" test_routing_parallel_agent_over_driver_phrase
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
run_test "production-field pilot id -> adk-production-field-readiness" test_routing_production_field_pilot_id
run_test "性能分析 -> adk-performance-profiling-embedded" test_routing_performance
run_test "长任务执行计划 -> adk-planning-execution-loop" test_routing_planning_execution_positive
run_test "调试正向对照 -> adk-systematic-debugging" test_routing_debugging_contrastive_positive
run_test "调试 intent 限制实现权限" test_routing_debugging_intent_caps_implementation_signal
run_test "否定 non-trigger 不得压制调试" test_negated_non_trigger_does_not_veto_debugging
run_test "发布正向对照 -> adk-release-versioning" test_routing_release_contrastive_positive
run_test "review mode -> readonly artifact mode + selection-group primary" test_review_maps_to_readonly_artifacts

echo ""
echo "--- Negative cases (should not match) ---"
run_test "只读长任务且无需执行 -> abstain" test_negative_readonly_long_task
run_test "架构评估且不要调试 -> abstain" test_negative_architecture_without_debugging
run_test "只解释发布现状且不执行 -> abstain" test_negative_release_explanation_only
run_test "规划动作否定 phrase classes 变形 -> abstain" test_negation_phrase_classes_metamorphic_planning
run_test "调试动作否定 phrase classes 变形 -> abstain" test_negation_phrase_classes_metamorphic_debugging
run_test "发布动作否定 phrase classes 变形 -> abstain" test_negation_phrase_classes_metamorphic_release
run_test "多轮 release -> readonly 以最新 turn 为准" test_multiturn_latest_turn_release_to_readonly
run_test "多轮 readonly -> implementation mode 仍受 Skill effect ceiling 限制" test_multiturn_latest_turn_readonly_to_implementation
run_test "完全无关的文本xyz -> no match" test_negative_unrelated_xyz
run_test "今天天气很好 -> no match" test_negative_weather
run_test "abc123 -> no match" test_negative_abc

echo ""
echo "================================="
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    PYTHONPATH="$ROOT_DIR/src" python3 "$ROOT_DIR/tests/test_routing_ir_contract.py"
    echo -e "${GREEN}All match effectiveness tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some match effectiveness tests failed${NC}"
    exit 1
fi
