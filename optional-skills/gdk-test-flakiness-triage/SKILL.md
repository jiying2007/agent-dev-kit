---
name: gdk-test-flakiness-triage
description: 定位测试波动根因并给出稳定化方案
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "测试波动"
  - "flaky test"
  - "测试不稳定"
non_triggers:
  - 测试稳定失败且根因明确
inputs:
  - 失败日志、执行环境、历史通过率
outputs:
  - 波动根因假设、验证实验、修复建议
constraints:
  - 必须区分环境噪声与真实缺陷
  - 调查阶段默认只读优先，不先行改动生产配置
---

# gdk-test-flakiness-triage

## Goal
- 定位测试波动根因并给出稳定化方案。
- 建立不稳定测试识别、分类、隔离和修复的完整流程。

## Prerequisites
- 可获取最近多次失败/成功样本（至少各 3 组）。
- 可比对执行环境、依赖版本与资源状态。

## Workflow
1. 不稳定测试识别：从 CI 历史中提取失败率异常的测试。
2. 失败模式聚类：按错误类型、失败阶段和环境条件分类。
3. 建立假设矩阵：列出可能根因，单轮只验证一个假设。
4. 环境差异对比：检查依赖版本、资源状态和时序条件。
5. 重试策略评估：确定是否需要重试、重试次数和退避策略。
6. 隔离方法实施：将不稳定测试隔离到独立执行环境。
7. 根因分析：使用 5-Why 方法穿透到系统性根因。
8. 修复验证：确认修复后测试稳定性，回归验证通过。

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

## Evidence Template
```md
- Sample Window:
- Failure Cluster:
- Failure Rate:
- Hypothesis Matrix:
- Experiment Records:
- Ruled-out Causes:
- Root Cause Analysis:
- Isolation Method:
- Retry Strategy:
- Stabilization Actions:
- Re-run Success Rate:
- Regression Test Results:
```

## Failure Handling
- 无法稳定复现时先固化环境镜像，不直接修改生产配置。
- 若疑似真实缺陷而非波动，切换至 `gdk-systematic-debugging` 并升级优先级。
- 若重试策略仍无法稳定，必须隔离测试并标记为 `quarantine`。
- 若根因涉及外部依赖，必须建立 mock 或 stub 替代方案。

## Quality Gate
- 结论需包含可复现实验与回归验证计划。
- 至少记录一条被排除假设，避免重复试错。
- 不稳定测试必须有明确的失败率基线（如 < 1%）。
- 隔离方法必须经过验证，确保不影响其他测试。
- 修复后必须运行至少 20 次回归测试确认稳定性。
