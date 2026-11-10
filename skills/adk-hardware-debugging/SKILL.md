---
name: adk-hardware-debugging
description: "用于板级电源、时钟、复位和硬件异常的假设验证与证据定位；不用于把 Linux oops 直接归咎硬件或未经许可执行带风险的硬件操作。"
version: 1.0.2
last_updated: 2026-11-10
triggers:
  - 硬件调试
  - oops 分析
  - panic 分析
  - 问题定位
  - HardFault
  - 随机复位
  - 低功耗后无法唤醒
non_triggers:
  - BSP 分析
  - 驱动开发
inputs:
  - kernel oops/panic 信息
  - 硬件现象描述
  - datasheet 文档
outputs:
  - 问题分析报告
  - 排查方向
  - 解决方案
constraints:
  - 必须说明排查方向的置信度
  - 必须提供验证方法
  - 不能假设应该可以工作
---

# adk-hardware-debugging

## Goal
- 基于日志、调用栈、寄存器和硬件证据定位异常根因，输出可复现的排查路径。

## Prerequisites
- 已收集复现步骤、硬件版本、软件版本、日志和相关符号文件。
- 已明确异常类型，例如 oops、panic、总线超时、DMA 错误或信号异常。
- 已知道可执行的现场验证手段，如 dmesg、设备调试通道、寄存器 dump 或波形采集。

## Workflow
1. 复现建模：记录触发步骤、频率、环境差异和最近变更。
2. 日志解析：解析 fault type、PC/LR、call trace、寄存器和 taint 信息。
3. 数据追踪：从故障点反向追踪状态来源、调用者和硬件事件。
4. 假设排序：按证据强弱列出候选根因和置信度。
5. 内核/芯片能力分流：首先核对 Cortex-M0/M0+/M23/M3/M4 等架构、厂商复位源寄存器与 SDK；不能对不具备 CFSR/HFSR/BFAR 的内核套用 M3/M4 故障寄存器流程。诊断 HardFault、看门狗重启、低功耗唤醒时按需读取 `references/mcu-fault-reset-wakeup.md`。
6. 最小验证：设计单变量验证动作，避免一次改变多个条件。
7. 结论闭环：给出根因、证据、修复方向、回归范围和残留风险。

## Commands
```bash
rg -n "dev_err|WARN_ON|BUG_ON|panic|timeout|ETIMEDOUT" <target-dir>
rg -n "request_irq|spin_lock|mutex_lock|dma_|completion|wait_event" <target-dir>
dmesg
addr2line -e <vmlinux> <pc-address>
```

## Evidence Template
```md
- Symptom:
- Reproduction:
- Logs:
- Call Trace:
- Register State:
- Hypotheses:
  - confidence: high|medium|low
    evidence:
    validation:
- Root Cause:
- Gate Result: pass|needs-fix
```

## Quality Gate
- 根因结论必须有日志、代码位置或硬件测量支撑。
- 每个候选原因都有置信度和验证动作。
- 输出必须包含 `pass` 或 `needs-fix`，缺少复现证据时不得给通过结论。
- 修复建议必须包含回归验证范围。
