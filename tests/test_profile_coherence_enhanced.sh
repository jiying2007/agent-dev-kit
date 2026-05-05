#!/usr/bin/env bash
set -euo pipefail

# Profile coherence测试

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

# 测试1: manifest.yaml存在
test_manifest_exists() {
    [[ -f "$ROOT_DIR/manifest.yaml" ]]
}

# 测试2: manifest.yaml包含profiles节
test_manifest_has_profiles() {
    grep -q "^profiles:" "$ROOT_DIR/manifest.yaml"
}

# 测试3: manifest.yaml包含default_profile
test_manifest_has_default_profile() {
    grep -q "^default_profile:" "$ROOT_DIR/manifest.yaml"
}

# 测试4: manifest.yaml包含agents节
test_manifest_has_agents() {
    grep -q "^agents:" "$ROOT_DIR/manifest.yaml"
}

# 测试5: manifest.yaml包含skills节
test_manifest_has_skills() {
    grep -q "^skills:" "$ROOT_DIR/manifest.yaml"
}

# 运行所有测试
echo "Running Profile coherence tests..."
echo "======================================"

run_test "manifest.yaml exists" test_manifest_exists
run_test "manifest has profiles" test_manifest_has_profiles
run_test "manifest has default_profile" test_manifest_has_default_profile
run_test "manifest has agents" test_manifest_has_agents
run_test "manifest has skills" test_manifest_has_skills

echo "======================================"
echo "Total: $TESTS_TOTAL, Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All Profile coherence tests passed${NC}"
    exit 0
else
    echo -e "${RED}Some Profile coherence tests failed${NC}"
    exit 1
fi
