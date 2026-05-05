#!/usr/bin/env bash
set -euo pipefail

# 边界条件测试

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

# 测试1: 空change-id
test_empty_change_id() {
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" propose --change "" --title "test" 2>&1 || true)
    [[ "$output" == *"FAIL"* ]]
}

# 测试2: 无效change-id格式
test_invalid_change_id() {
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" propose --change "Invalid_ID" --title "test" 2>&1 || true)
    [[ "$output" == *"FAIL"* ]]
}

# 测试3: 缺少title参数
test_missing_title() {
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" propose --change test-change 2>&1 || true)
    [[ "$output" == *"FAIL"* ]]
}

# 测试4: 不存在的change目录
test_nonexistent_change() {
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" apply --change nonexistent-change 2>&1 || true)
    [[ "$output" == *"FAIL"* ]]
}

# 测试5: 无效的result参数
test_invalid_result() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    cat > "$change_dir/state.yaml" <<'EOF'
stage: verified
owner: test
updated_at: 2026-05-05T00:00:00Z
EOF
    
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" review --change test-change --result invalid --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 测试6: 负数blockers
test_negative_blockers() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    cat > "$change_dir/state.yaml" <<'EOF'
stage: verified
owner: test
updated_at: 2026-05-05T00:00:00Z
EOF
    
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" review --change test-change --result pass --blockers -1 --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 测试7: 非数字blockers
test_non_numeric_blockers() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    cat > "$change_dir/state.yaml" <<'EOF'
stage: verified
owner: test
updated_at: 2026-05-05T00:00:00Z
EOF
    
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" review --change test-change --result pass --blockers abc --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 测试8: 重复创建change
test_duplicate_change() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" propose --change test-change --title "test" --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 测试9: 阶段顺序错误
test_wrong_stage_order() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    cat > "$change_dir/state.yaml" <<'EOF'
stage: proposed
owner: test
updated_at: 2026-05-05T00:00:00Z
EOF
    
    # 尝试在proposed阶段执行verify
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" verify --change test-change --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 测试10: pass review但有blockers
test_pass_with_blockers() {
    local tmp_dir=$(mktemp -d)
    local change_dir="$tmp_dir/changes/test-change"
    mkdir -p "$change_dir"
    
    cat > "$change_dir/state.yaml" <<'EOF'
stage: verified
owner: test
updated_at: 2026-05-05T00:00:00Z
EOF
    
    local output
    output=$("$ROOT_DIR/scripts/workflow.sh" review --change test-change --result pass --blockers 1 --root "$tmp_dir/changes" 2>&1 || true)
    
    rm -rf "$tmp_dir"
    [[ "$output" == *"FAIL"* ]]
}

# 运行所有测试
echo "Running boundary condition tests..."
echo "======================================"

run_test "Empty change-id" test_empty_change_id
run_test "Invalid change-id format" test_invalid_change_id
run_test "Missing title" test_missing_title
run_test "Nonexistent change" test_nonexistent_change
run_test "Invalid result" test_invalid_result
run_test "Negative blockers" test_negative_blockers
run_test "Non-numeric blockers" test_non_numeric_blockers
run_test "Duplicate change" test_duplicate_change
run_test "Wrong stage order" test_wrong_stage_order
run_test "Pass with blockers" test_pass_with_blockers

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All boundary condition tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some boundary condition tests failed${NC}"
    exit 1
fi