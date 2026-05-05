---
name: test-flakiness-triage
description: 定位测试波动根因并给出稳定化方案
version: 1.0.0
last_updated: 2026-05-02
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

# test-flakiness-triage

## Goal
- 定位测试波动根因并给出稳定化方案

## Prerequisites
- 可获取最近多次失败/成功样本（至少各 3 组）。
- 可比对执行环境、依赖版本与资源状态。

## Workflow
1. 收集最近失败样本并按失败模式聚类。
2. 建立假设矩阵，单轮只验证一个假设并记录结论。
3. 对比环境差异、依赖版本和时序条件，保留负结果留痕。
4. 输出可复现实验、最小修复建议与回归方案。

## Commands
```bash
for i in {1..10}; do <test_cmd> || true; done
rg -n "timeout|race|port already in use|resource busy" <test_log_dir>
```

## Evidence Template
```md
- Sample Window:
- Failure Cluster:
- Hypothesis Matrix:
- Experiment Records:
- Ruled-out Causes:
- Stabilization Actions:
- Re-run Success Rate:
```

## Failure Handling
- 无法稳定复现时先固化环境镜像，不直接修改生产配置。
- 若疑似真实缺陷而非波动，切换至 `systematic-debugging` 并升级优先级。

## Quality Gate
- 结论需包含可复现实验与回归验证计划。
- 至少记录一条被排除假设，避免重复试错。
