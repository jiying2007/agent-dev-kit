#!/usr/bin/env bash
# bash 测试辅助库
# 来源: superpowers shell test helper，已按 adk 通用测试裁剪

# 断言: 等于
assert_equals() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-assert_equals}"
    if [[ "$expected" != "$actual" ]]; then
        echo "FAIL: $msg"
        echo "  expected: $expected"
        echo "  actual:   $actual"
        return 1
    fi
}

# 断言: 包含
assert_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-assert_contains}"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "FAIL: $msg"
        echo "  expected to contain: $needle"
        echo "  in: $haystack"
        return 1
    fi
}

# 断言: 不包含
assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-assert_not_contains}"
    if [[ "$haystack" == *"$needle"* ]]; then
        echo "FAIL: $msg"
        echo "  expected NOT to contain: $needle"
        echo "  in: $haystack"
        return 1
    fi
}

# 断言: 正则匹配
assert_matches() {
    local text="$1"
    local pattern="$2"
    local msg="${3:-assert_matches}"
    if ! [[ "$text" =~ $pattern ]]; then
        echo "FAIL: $msg"
        echo "  expected match: $pattern"
        echo "  in: $text"
        return 1
    fi
}

# 断言: 路径不存在
assert_path_absent() {
    local path="$1"
    local msg="${2:-assert_path_absent}"
    if [[ -e "$path" ]]; then
        echo "FAIL: $msg"
        echo "  expected absent: $path"
        return 1
    fi
}

# 断言: 路径存在
assert_path_present() {
    local path="$1"
    local msg="${2:-assert_path_present}"
    if [[ ! -e "$path" ]]; then
        echo "FAIL: $msg"
        echo "  expected present: $path"
        return 1
    fi
}

# 断言: 命令退出码
assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-assert_exit_code}"
    if [[ "$expected" != "$actual" ]]; then
        echo "FAIL: $msg"
        echo "  expected exit code: $expected"
        echo "  actual exit code:   $actual"
        return 1
    fi
}

# 测试运行器
run_test() {
    local test_name="$1"
    local test_func="$2"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "Testing $test_name... "
    if $test_func; then
        echo -e "\033[0;32mPASS\033[0m"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "\033[0;31mFAIL\033[0m"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}
