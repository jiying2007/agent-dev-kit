#!/usr/bin/env bash
set -euo pipefail

# 集成测试

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

# 测试1: 完整工作流流程
test_full_workflow() {
    local tmp_dir=$(mktemp -d)
    
    # Propose
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" propose --change integration-test --title "Integration Test" --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    # Apply
    output=$("$ROOT_DIR/scripts/workflow.sh" apply --change integration-test --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    # Verify
    output=$("$ROOT_DIR/scripts/workflow.sh" verify --change integration-test --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    # Review
    output=$("$ROOT_DIR/scripts/workflow.sh" review --change integration-test --result pass --blockers 0 --majors 0 --minors 0 --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    # Archive
    output=$("$ROOT_DIR/scripts/workflow.sh" archive --change integration-test --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试2: 状态文件正确更新
test_state_file_updates() {
    local tmp_dir=$(mktemp -d)
    
    # Propose
    "$ROOT_DIR/scripts/workflow.sh" propose --change state-test --title "State Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查proposed状态
    local stage
    stage=$(awk '/^stage:/ {print $2; exit}' "$tmp_dir/changes/state-test/state.yaml")
    [[ "$stage" == "proposed" ]] || return 1
    
    # Apply
    "$ROOT_DIR/scripts/workflow.sh" apply --change state-test --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查applied状态
    stage=$(awk '/^stage:/ {print $2; exit}' "$tmp_dir/changes/state-test/state.yaml")
    [[ "$stage" == "applied" ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试3: 历史记录正确记录
test_history_logging() {
    local tmp_dir=$(mktemp -d)
    
    # Propose
    "$ROOT_DIR/scripts/workflow.sh" propose --change history-test --title "History Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查历史记录
    [[ -f "$tmp_dir/changes/history-test/history.log" ]] || return 1
    
    local lines
    lines=$(wc -l < "$tmp_dir/changes/history-test/history.log")
    [[ "$lines" -ge 1 ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试4: 必需文件创建
test_required_files_created() {
    local tmp_dir=$(mktemp -d)
    
    # Propose
    "$ROOT_DIR/scripts/workflow.sh" propose --change files-test --title "Files Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查必需文件
    [[ -f "$tmp_dir/changes/files-test/proposal.md" ]] || return 1
    [[ -f "$tmp_dir/changes/files-test/design.md" ]] || return 1
    [[ -f "$tmp_dir/changes/files-test/tasks.md" ]] || return 1
    [[ -f "$tmp_dir/changes/files-test/checklist.md" ]] || return 1
    [[ -f "$tmp_dir/changes/files-test/negative-results.md" ]] || return 1
    [[ -f "$tmp_dir/changes/files-test/state.yaml" ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试5: 验证报告生成
test_verify_report_generation() {
    local tmp_dir=$(mktemp -d)
    
    # Propose and Apply
    "$ROOT_DIR/scripts/workflow.sh" propose --change verify-test --title "Verify Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" apply --change verify-test --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # Verify
    "$ROOT_DIR/scripts/workflow.sh" verify --change verify-test --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查验证报告
    [[ -f "$tmp_dir/changes/verify-test/verify-report.md" ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试6: 评审报告生成
test_review_report_generation() {
    local tmp_dir=$(mktemp -d)
    
    # Propose, Apply, Verify
    "$ROOT_DIR/scripts/workflow.sh" propose --change review-test --title "Review Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" apply --change review-test --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" verify --change review-test --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # Review
    "$ROOT_DIR/scripts/workflow.sh" review --change review-test --result pass --blockers 0 --majors 0 --minors 0 --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查评审报告
    [[ -f "$tmp_dir/changes/review-test/review-report.md" ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试7: 归档功能
test_archive_functionality() {
    local tmp_dir=$(mktemp -d)
    
    # 完整流程
    "$ROOT_DIR/scripts/workflow.sh" propose --change archive-test --title "Archive Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" apply --change archive-test --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" verify --change archive-test --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" review --change archive-test --result pass --blockers 0 --majors 0 --minors 0 --root "$tmp_dir/changes" >/dev/null 2>&1
    "$ROOT_DIR/scripts/workflow.sh" archive --change archive-test --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 检查归档目录
    [[ -d "$tmp_dir/changes/archive" ]] || return 1
    
    local archived
    archived=$(find "$tmp_dir/changes/archive" -type d -name "*archive-test" | head -1)
    [[ -n "$archived" ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 测试8: 强制归档
test_force_archive() {
    local tmp_dir=$(mktemp -d)
    
    # Propose（不完成完整流程）
    "$ROOT_DIR/scripts/workflow.sh" propose --change force-archive-test --title "Force Archive Test" --root "$tmp_dir/changes" >/dev/null 2>&1
    
    # 强制归档
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" archive --change force-archive-test --force --root "$tmp_dir/changes" 2>&1)
    [[ "$output" == *"OK"* ]] || return 1
    
    rm -rf "$tmp_dir"
    return 0
}

# 运行所有测试
echo "Running integration tests..."
echo "======================================"

run_test "Full workflow" test_full_workflow
run_test "State file updates" test_state_file_updates
run_test "History logging" test_history_logging
run_test "Required files created" test_required_files_created
run_test "Verify report generation" test_verify_report_generation
run_test "Review report generation" test_review_report_generation
run_test "Archive functionality" test_archive_functionality
run_test "Force archive" test_force_archive

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All integration tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some integration tests failed${NC}"
    exit 1
fi