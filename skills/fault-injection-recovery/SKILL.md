---
name: fault-injection-recovery
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

# fault-injection-recovery

## Goal
- 验证系统在故障场景下可检测、可恢复、可回归。
- 量化检测时延与恢复时延，确认满足恢复 SLA。

## Prerequisites
- 定义故障模型（掉电、超时、资源耗尽、链路中断、看门狗超时）。
- 设定恢复 SLA 与允许的数据损失边界。
- 准备注入工具（gdb 脚本、fault-injection 框架、硬件断电装置）。

## Workflow
1. **选择注入点**：按影响范围和可复现性排序。
   - 软件注入：内存分配失败、I/O 返回错误、信号模拟。
   - 硬件注入：断电、信号干扰、温度异常。
2. **看门狗配置与验证**：确保看门狗能捕获系统挂死。
   ```bash
   # Linux 看门狗
   echo 1 > /dev/watchdog
   # 检查看门狗状态
   cat /dev/watchdog
   # RTOS 看门狗配置检查
   rg -n "watchdog|wdt|WDT" src/ include/
   ```
3. **设计注入实验**：一次只注入一种故障并记录前置状态。
   ```bash
   # 内存分配失败注入
   echo 1 > /sys/kernel/debug/failslab/verbose
   echo 100 > /sys/kernel/debug/failslab/probability
   echo 1 > /sys/kernel/debug/failslab/times
   # I/O 错误注入
   echo "1 block 0" > /sys/kernel/debug/fail_make_request/inject
   # GDB 断点注入
   gdb-multiarch firmware.elf -ex "target remote :3333" \
     -ex "break module_send" \
     -ex "commands" \
     -ex "set ret = -1" \
     -ex "continue" \
     -ex "end"
   ```
4. **观察恢复行为**：检测、隔离、重试、降级、恢复时延。
   ```bash
   # 抓取恢复过程日志
   dmesg -w | grep -i "recover\|fail\|timeout\|reset"
   # 测量恢复时间
   time <recovery-verify-cmd> --scenario <fault_type>
   ```
5. **日志分析**：提取故障检测时间、恢复时间、数据一致性。
   ```bash
   # 提取关键事件时间戳
   dmesg | grep -E "fault|error|recover|reset" | awk '{print $1, $0}'
   # 统计错误分布
   journalctl --since "1 hour ago" | grep -c "ERROR"
   ```
6. **回归核验**：故障解除后验证功能恢复与数据一致性。
7. **输出改进项**：恢复盲点、告警缺口、监控增强建议。

## Commands
```bash
# Linux fault injection 框架
echo 1 > /sys/kernel/debug/failslab/verbose
echo 100 > /sys/kernel/debug/failslab/probability
echo -1 > /sys/kernel/debug/failslab/times

# 看门狗操作
echo 1 > /dev/watchdog        # 启动
echo V > /dev/watchdog         # 停止（喂狗）

# GDB 故障注入
gdb-multiarch <elf> -ex "target remote :3333" \
  -ex "break <func>" -ex "set variable <var> = <bad_value>" -ex "continue"

# 恢复验证
<recovery-verify-cmd> --scenario <scenario>

# 日志分析
dmesg | grep -iE "fault|error|panic|recover"
journalctl -p err --since "10 min ago"

# 内存压力测试
stress-ng --vm 2 --vm-bytes 256M --timeout 60s

# 串口日志抓取（嵌入式）
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

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
