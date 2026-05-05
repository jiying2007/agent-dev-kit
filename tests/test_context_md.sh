#!/usr/bin/env bash
set -euo pipefail

# 测试CONTEXT.md完整性

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

# 测试1: 检查CONTEXT.md存在
test_context_exists() {
    [[ -f "$ROOT_DIR/CONTEXT.md" ]]
}

# 测试2: 检查CONTEXT.md包含核心概念
test_context_core_concepts() {
    local content
    content=$(cat "$ROOT_DIR/CONTEXT.md")
    [[ "$content" == *"Agent"* && "$content" == *"Skill"* && "$content" == *"Profile"* ]]
}

# 测试3: 检查CONTEXT.md包含Workflow概念
test_context_workflow() {
    grep -q "Workflow" "$ROOT_DIR/CONTEXT.md"
}

# 测试4: 检查CONTEXT.md包含Artifact概念
test_context_artifact() {
    grep -q "Artifact" "$ROOT_DIR/CONTEXT.md"
}

# 测试5: 检查CONTEXT.md包含Gate概念
test_context_gate() {
    grep -q "Gate" "$ROOT_DIR/CONTEXT.md"
}

# 测试6: 检查CONTEXT.md包含术语表
test_context_glossary() {
    grep -q "术语表" "$ROOT_DIR/CONTEXT.md"
}

# 测试7: 检查CONTEXT.md包含概念关系
test_context_relationships() {
    grep -q "概念关系" "$ROOT_DIR/CONTEXT.md"
}

# 测试8: 检查CONTEXT.md包含使用规范
test_context_usage() {
    grep -q "使用规范" "$ROOT_DIR/CONTEXT.md"
}

# 运行所有测试
echo "Running CONTEXT.md tests..."
echo "======================================"

run_test "CONTEXT.md exists" test_context_exists
run_test "Core concepts defined" test_context_core_concepts
run_test "Workflow concept" test_context_workflow
run_test "Artifact concept" test_context_artifact
run_test "Gate concept" test_context_gate
run_test "Glossary section" test_context_glossary
run_test "Relationships section" test_context_relationships
run_test "Usage guidelines" test_context_usage

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All CONTEXT.md tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some CONTEXT.md tests failed${NC}"
    exit 1
fi