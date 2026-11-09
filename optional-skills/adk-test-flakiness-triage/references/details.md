# 测试波动 — 按需诊断示例

此参考文件仅保存日志分析、重试与隔离示例。主工作流、风险、权限、统计判断与放行条件均以 `../SKILL.md` 为准。任何固定重复次数都只是 smoke，不作为低失败率保证。

## 不稳定测试识别
```bash
# 从 CI 日志中提取失败测试
rg -n "FAILED|ERROR" ci-log.txt | grep -i "test"

# 统计测试失败率
for test in $(cat test-list.txt); do
  count=$(rg -c "$test" ci-log.txt 2>/dev/null || echo 0)
  echo "$test: $count failures"
done | sort -t: -k2 -rn

# 列出最近失败的测试
git log --oneline --all --grep="flaky" | head -20

# 检查测试历史通过率
rg -n "pass_rate|flaky" test-reports/ | sort -t: -k2 -rn
```

## 重试策略模板
```md
[retry-strategy]
test_name: <测试名称>
current_retry: <当前重试次数>
recommended_retry: <建议重试次数>
backoff_strategy: linear | exponential | fixed
max_wait: <最大等待时间>
conditions:
  - <重试条件 1>
  - <重试条件 2>
rationale: <选择此策略的原因>
```

## 隔离方法
```md
[isolation-method]
test_name: <测试名称>
isolation_type: environment | data | timing | resource
steps:
  1. <隔离步骤 1>
  2. <隔离步骤 2>
  3. <隔离步骤 3>
expected_behavior: <隔离后预期行为>
verification: <验证命令>
```

## 根因分析模板
```md
[root-cause-analysis]
test_name: <测试名称>
failure_pattern: <失败模式>
5-why:
  why-1: <直接原因>
  why-2: <中间原因>
  why-3: <系统性根因>
root_cause_category: timing | resource_leak | external_dependency | race_condition | environment
fix_type: code_change | test_rewrite | environment_setup | retry_config
fix_description: <修复描述>
regression_test: <回归测试命令>
```

## Commands
```bash
# 运行测试多次统计失败率
for i in {1..10}; do <test_cmd> 2>&1 | tee -a test-run-$i.log; done

# 搜索常见波动原因
rg -n "timeout|race|port already in use|resource busy|connection refused" <test_log_dir>

# 检查测试依赖
rg -n "import|require|from" <test_file> | head -20

# 检查环境变量
env | grep -i "test\|ci\|debug" | sort

# 对比成功与失败的日志差异
diff <(rg -n "INFO|DEBUG" success.log) <(rg -n "INFO|DEBUG" failure.log) | head -50

# 检查端口占用
ss -tlnp | grep <test_port>

# 检查文件锁
lsof | grep <test_data_dir>
```

