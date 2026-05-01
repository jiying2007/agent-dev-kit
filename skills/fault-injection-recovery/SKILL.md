---
name: fault-injection-recovery
description: 故障注入与恢复策略验证
triggers:
  - 需要验证韧性与恢复能力时
non_triggers:
  - 无状态纯计算脚本
inputs:
  - 故障模型、恢复目标
outputs:
  - 注入方案与恢复结果
constraints:
  - 覆盖掉电、超时、资源耗尽
---

# fault-injection-recovery

## Goal
- 验证系统在故障场景下可检测、可恢复、可回归。

## Prerequisites
- 定义故障模型（掉电、超时、资源耗尽、链路中断）。
- 设定恢复 SLA 与允许的数据损失边界。

## Workflow
1. 选择注入点：按影响和可复现性排序。
2. 设计注入实验：一次只注入一种故障并记录前置状态。
3. 观察恢复行为：检测、隔离、重试、降级、恢复时延。
4. 回归核验：故障解除后验证功能恢复与数据一致性。
5. 输出改进项：恢复盲点、告警缺口、监控增强建议。

## Commands
```bash
<fault-inject-cmd> --type timeout --target <module>
<recovery-verify-cmd> --scenario timeout_recover
```

## Evidence Template
```md
- Fault Model:
- Injection Point:
- Detection Result:
- Recovery Time:
- Post-recovery Verification:
```

## Failure Handling
- 出现不可逆破坏风险时立即停止注入并回滚环境。
- 恢复失败时先保留现场，再进行最小化复现实验。

## Quality Gate
- 必须覆盖掉电、超时、资源耗尽中的至少两类。
- 必须记录检测时间和恢复时间。
- 结论需包含是否满足恢复 SLA。
