#!/usr/bin/env bash
set -euo pipefail

# 测试质量门禁检查脚本

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

# 测试1: 检查脚本存在
test_script_exists() {
    [[ -f "$ROOT_DIR/scripts/quality-gate-check.sh" ]]
}

# 测试2: 检查脚本可执行
test_script_executable() {
    [[ -x "$ROOT_DIR/scripts/quality-gate-check.sh" ]]
}

# 测试3: 检查帮助信息
test_help_output() {
    local output
    output=$("$ROOT_DIR/scripts/quality-gate-check.sh" check-all --help 2>&1 || true)
    [[ "$output" == *"质量门禁检查脚本"* ]] && [[ "$output" != *"--strict"* ]]
}

# 测试4: 检查所有质量门禁
test_check_all() {
    local output
    output=$("$ROOT_DIR/scripts/quality-gate-check.sh" check-all 2>&1 || true)
    [[ "$output" == *"所有质量门禁检查通过"* ]]
}

# 测试5: 退役 strict 兼容参数必须 fail closed
test_retired_strict_rejected() {
    local output
    if output=$("$ROOT_DIR/scripts/quality-gate-check.sh" check-all --strict 2>&1); then
        return 1
    fi
    [[ "$output" == *"未知参数: --strict"* ]]
}

# 运行所有测试
echo "Running enhanced gate check tests..."
echo "======================================"

run_test "script exists" test_script_exists
run_test "script executable" test_script_executable
run_test "help output" test_help_output
run_test "check all" test_check_all
run_test "retired strict rejected" test_retired_strict_rejected

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All enhanced gate check tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some enhanced gate check tests failed${NC}"
    exit 1
fi
