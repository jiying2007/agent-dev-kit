---
name: interrupt-dma-patterns
description: 中断与 DMA 协作模式设计
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 高吞吐或低时延 I/O 场景
non_triggers:
  - 轮询足够且低频场景
inputs:
  - 外设速率、缓冲策略
outputs:
  - ISR/DMA 模式建议
constraints:
  - 禁止在 ISR 做重计算
---

# interrupt-dma-patterns

## Goal
- 设计低抖动、可恢复的 ISR + DMA 协作方案。

## Prerequisites
- 明确数据速率、缓冲深度、丢包容忍度和中断预算。
- 确认 DMA 通道与缓存一致性要求。

## Workflow
1. 模式选择：中断驱动、DMA、混合模式按负载对比。
2. 缓冲设计：单缓冲/双缓冲/ring buffer 取舍。
3. ISR 约束：仅做标记与唤醒，不做复杂逻辑。
4. DMA 完成处理：回调时序、错误中断、重提交流程。
5. 回归验证：高负载、突发流量、错误注入下稳定性验证。

## Commands
```bash
rg -n "ISR|IRQ|DMA|callback" <driver_path>
<latency-measure-cmd> --irq --dma
```

## Evidence Template
```md
- Selected Pattern:
- Buffer Strategy:
- ISR Budget:
- DMA Error Handling:
- Stress Result:
```

## Failure Handling
- IRQ 丢失或风暴时，先降速并确认中断屏蔽策略。
- DMA 异常频发时，退回中断最小路径定位根因。

## Quality Gate
- 必须说明 ISR 时间预算与 DMA 回调策略。
- 必须覆盖至少一个错误恢复路径。
- 压测结果需包含吞吐与时延双指标。
