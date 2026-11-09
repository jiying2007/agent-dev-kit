---
name: adk-test-flakiness-triage
description: "用于非确定性测试故障的复现、波动归因和消除不稳定方案验证；不用于把失败盲目重跑到绿或降低测试门禁。"
version: 1.0.2
last_updated: 2026-11-09
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

# adk-test-flakiness-triage

## Goal
- 定位测试波动根因并给出稳定化方案。
- 建立不稳定测试识别、分类、隔离和修复的完整流程。


## Prerequisites
- 获取足以支持初步假设的失败/成功样本；不足时记录样本数与采样偏差，不能伪造基线。
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


## Quality Gate
- 结论需包含可复现实验与回归验证计划。
- 至少记录一条被排除假设，避免重复试错。
- 记录失败率基线、样本数、失败数、环境与统计假设；目标失败率按风险确定。
- 隔离方法必须经过验证，确保不影响其他测试。
- 20 次有界重复可作为 smoke，但零失败不代表达成低失败率目标；独立同分布下 20 次零失败，单侧 95% 失败率上界仍约 13.9%，更严格目标须另行设计统计证据。

## Failure Handling
- 无法稳定复现时先固化环境镜像，不直接修改生产配置。
- 若疑似真实缺陷而非波动，切换至 `adk-systematic-debugging` 并升级优先级。
- 若重试策略仍无法稳定，必须隔离测试并标记为 `quarantine`。
- 若根因涉及外部依赖，必须建立 mock 或 stub 替代方案。


## Evidence Template

```md
status: pass | needs-fix | BLOCKED
commands:
- <command + exit code>
evidence:
- <path or output summary>
risks:
- <remaining risk or none>
```

## References
- 详细背景、命令、模板、示例和扩展检查项保存在 `references/details.md`。
- 入口文件只保留触发和执行所需的最小上下文，避免默认加载过多 token。
