---
name: adk-fault-injection-recovery
description: 故障注入与恢复策略验证
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "故障注入"
  - "故障恢复"
  - "容错测试"
non_triggers:
  - 无状态纯计算脚本
inputs:
  - 故障模型、恢复目标
outputs:
  - 注入方案与恢复结果
constraints:
  - 覆盖掉电、超时、资源耗尽
---

# adk-fault-injection-recovery

## Goal
- 验证系统在故障场景下可检测、可恢复、可回归。
- 量化检测时延与恢复时延，确认满足恢复 SLA。

## Prerequisites
- 定义故障模型（掉电、超时、资源耗尽、链路中断、看门狗超时）。
- 设定恢复 SLA 与允许的数据损失边界。
- 准备注入工具（debug transport 脚本、fault-injection 框架、硬件断电装置）。

## Workflow
1. **选择注入点**：按影响范围和可复现性排序。
   - 软件注入：内存分配失败、I/O 返回错误、信号模拟。
   - 硬件注入：断电、信号干扰、温度异常。
2. **看门狗配置与验证**：确保看门狗能捕获系统挂死。
3. **设计注入实验**：一次只注入一种故障并记录前置状态。
4. **观察恢复行为**：检测、隔离、重试、降级、恢复时延。
5. **日志分析**：提取故障检测时间、恢复时间、数据一致性。
6. **回归核验**：故障解除后验证功能恢复与数据一致性。
7. **输出改进项**：恢复盲点、告警缺口、监控增强建议。

## Commands
```bash
echo 1 > /sys/kernel/debug/failslab/verbose
echo 100 > /sys/kernel/debug/failslab/probability
echo -1 > /sys/kernel/debug/failslab/times
echo 1 > /dev/watchdog
<debug-transport> inject --target <target> --point <func> --value <bad_value>
<recovery-verify-cmd> --scenario <scenario>
dmesg | grep -iE "fault|error|panic|recover"
journalctl -p err --since "10 min ago"
stress-ng --vm 2 --vm-bytes 256M --timeout 60s
minicom -D /dev/ttyUSB0 -b 115200 -C fault_test.log
```

## Evidence Template
```md
- Fault Model: [掉电/超时/资源耗尽/链路中断]
- Injection Method: [software/hardware]
- Injection Point: [module, function, line]
- Watchdog Config: [timeout=___s, action=reset/interrupt]
- Detection Time: ____ ms
- Recovery Time: ____ ms
- Recovery Strategy: [retry/degrade/failover/restart]
- Data Loss: [none/___ bytes/logged]
- Post-recovery Verification: [functional test pass/fail]
- Log Analysis: [key timestamps and error distribution]
```

## Failure Handling
- 出现不可逆破坏风险时立即停止注入并回滚环境。
- 恢复失败时先保留现场（coredump + 日志），再进行最小化复现实验。
- 看门狗未触发时，检查喂狗逻辑是否在异常路径中被错误调用。
- 注入后系统 panic，保存串口日志与 coredump 后再重启。

## Quality Gate
- 必须覆盖掉电、超时、资源耗尽中的至少两类。
- 必须记录检测时间和恢复时间。
- 结论需包含是否满足恢复 SLA。
- 看门狗配置必须经过验证（注入 hang 场景确认触发 reset）。
- 恢复后必须通过功能回归测试。

---

## 健壮性规范
- 注入前校验恢复路径、备份和停止条件。
- 外部命令记录命令、退出码、耗时和故障类型。
- 出现不可逆风险时停止注入并保留现场。
