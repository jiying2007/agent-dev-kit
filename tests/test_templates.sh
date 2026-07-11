#!/usr/bin/env bash
set -euo pipefail

# 测试模板文件完整性

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# 测试1: 检查PRD模板存在
test_prd_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/prd-template.md" ]]
}

# 测试2: 检查UserStory模板存在
test_user_story_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/user-story-template.md" ]]
}

# 测试3: 检查DesignSpec模板存在
test_design_spec_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/design-spec-template.md" ]]
}

# 测试4: 检查SystemArch模板存在
test_system_arch_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/system-arch-template.md" ]]
}

# 测试5: 检查TaskBreakdown模板存在
test_task_breakdown_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/task-breakdown-template.md" ]]
}

# 测试6: 检查ImplementationPlan模板存在
test_implementation_plan_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/implementation-plan-template.md" ]]
}

# 测试7: 检查TargetArchitectureReport模板存在
test_target_architecture_report_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/target-architecture-report-template.md" ]]
}

# 测试8: 检查ReviewReport模板存在
test_review_report_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/review-report-template.md" ]]
}

# 测试9: 检查TestReport模板存在
test_test_report_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/test-report-template.md" ]]
}

# 测试10: 检查Approval模板存在
test_approval_template() {
    [[ -f "$ROOT_DIR/templates/artifacts/approval-template.md" ]]
}

# 测试11: 检查标准工作流模板存在
test_standard_workflow_template() {
    [[ -f "$ROOT_DIR/templates/workflows/standard-workflow-template.md" ]]
}

# 测试12: 检查紧急工作流模板存在
test_emergency_workflow_template() {
    [[ -f "$ROOT_DIR/templates/workflows/emergency-workflow-template.md" ]]
}

# 测试13: 检查模板包含artifact标签
test_template_artifact_tags() {
    local template="$ROOT_DIR/templates/artifacts/prd-template.md"
    grep -q "\[artifact:PRD\]" "$template"
}

# 测试14: 检查模板包含status字段
test_template_status_field() {
    local template="$ROOT_DIR/templates/artifacts/prd-template.md"
    grep -q "status:" "$template"
}

# 测试15: 检查模板包含owner字段
test_template_owner_field() {
    local template="$ROOT_DIR/templates/artifacts/prd-template.md"
    grep -q "owner:" "$template"
}

# 测试16: 检查TargetArchitectureReport模板包含V4闭环章节
test_target_architecture_report_v4_sections() {
    local template="$ROOT_DIR/templates/artifacts/target-architecture-report-template.md"
    grep -q "## Architecture Operating Model" "$template" &&
    grep -q "## SSOT Matrix" "$template" &&
    grep -q "## Landing Protocol" "$template" &&
    grep -q "## Runtime Delivery Contract" "$template" &&
    grep -q "## Knowledge Promotion Contract" "$template" &&
    grep -q "## State Reconciliation Contract" "$template" &&
    grep -q "## Status Consistency Gate" "$template"
}

# 测试17: 检查TargetArchitectureReport模板包含落地成熟度等级
test_target_architecture_report_landing_levels() {
    local template="$ROOT_DIR/templates/artifacts/target-architecture-report-template.md"
    grep -q "report-only" "$template" &&
    grep -q "source-staged" "$template" &&
    grep -q "source-committed" "$template" &&
    grep -q "dry-run-verified" "$template" &&
    grep -q "live-applied" "$template" &&
    grep -q "knowledge-promoted" "$template"
}

# 测试18: 检查TargetArchitectureReport模板包含运行态和知识提升门禁字段
test_target_architecture_report_delivery_and_promotion_fields() {
    local template="$ROOT_DIR/templates/artifacts/target-architecture-report-template.md"
    grep -q "Approval Boundary" "$template" &&
    grep -q "Dry-run Evidence" "$template" &&
    grep -q "Apply Evidence" "$template" &&
    grep -q "Health Gate" "$template" &&
    grep -q "Review Owner" "$template" &&
    grep -q "Promotion Mode" "$template" &&
    grep -q "Required Truth" "$template"
}

# 运行所有测试
echo "Running template tests..."
echo "======================================"

run_test "PRD template exists" test_prd_template
run_test "UserStory template exists" test_user_story_template
run_test "DesignSpec template exists" test_design_spec_template
run_test "SystemArch template exists" test_system_arch_template
run_test "TaskBreakdown template exists" test_task_breakdown_template
run_test "ImplementationPlan template exists" test_implementation_plan_template
run_test "TargetArchitectureReport template exists" test_target_architecture_report_template
run_test "ReviewReport template exists" test_review_report_template
run_test "TestReport template exists" test_test_report_template
run_test "Approval template exists" test_approval_template
run_test "Standard workflow template exists" test_standard_workflow_template
run_test "Emergency workflow template exists" test_emergency_workflow_template
run_test "Template artifact tags" test_template_artifact_tags
run_test "Template status field" test_template_status_field
run_test "Template owner field" test_template_owner_field
run_test "TargetArchitectureReport V4 sections" test_target_architecture_report_v4_sections
run_test "TargetArchitectureReport landing levels" test_target_architecture_report_landing_levels
run_test "TargetArchitectureReport delivery and promotion fields" test_target_architecture_report_delivery_and_promotion_fields

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All template tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some template tests failed${NC}"
    exit 1
fi
