---
name: adk-interrupt-dma-patterns
description: 中断与 DMA 协作模式设计
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "中断处理"
  - "DMA处理"
  - "中断DMA"
non_triggers:
  - 轮询足够且低频场景
inputs:
  - 外设速率、缓冲策略
outputs:
  - ISR/DMA 模式建议
constraints:
  - 禁止在 ISR 做重计算
---

# adk-interrupt-dma-patterns

## Goal
- 设计低抖动、可恢复的 ISR + DMA 协作方案。
- 确保中断响应时延满足实时性要求，DMA 传输可靠无丢帧。

## Prerequisites
- 明确数据速率、缓冲深度、丢包容忍度和中断预算。
- 确认 DMA 通道与缓存一致性要求。
- 获取目标芯片中断控制器文档（NVIC/GIC）与 DMA 控制器手册。

## Workflow
1. **中断优先级配置**：按实时性需求分配优先级。
   ```c
   /* STM32 NVIC 优先级配置示例 */
   HAL_NVIC_SetPriority(TIM1_UP_IRQn, 0, 0);   /* 最高：控制环 */
   HAL_NVIC_SetPriority(DMA1_Stream5_IRQn, 1, 0); /* 高：数据采集 */
   HAL_NVIC_SetPriority(USART1_IRQn, 2, 0);     /* 中：通信 */
   HAL_NVIC_SetPriority(I2C1_EV_IRQn, 3, 0);    /* 低：传感器 */
   
   /* Linux 中断亲和性设置 */
   echo 1 > /proc/irq/<irq_num>/smp_affinity  /* 绑定 CPU0 */
   echo <priority> > /proc/irq/<irq_num>/priority  /* RT 优先级 */
   ```
2. **模式选择**：中断驱动、DMA、混合模式按负载对比。
   | 模式 | 适用场景 | CPU 占用 | 延迟 |
   |------|---------|---------|------|
   | 纯中断 | 低速率 (<10KB/s) | 中 | 低 |
   | 纯 DMA | 高速率、CPU 不介入 | 低 | 中 |
   | 中断+DMA | 混合负载 | 低 | 低 |
3. **缓冲设计**：单缓冲/双缓冲/ring buffer 取舍。
   ```c
   /* 双缓冲 DMA 配置（STM32 HAL） */
   HAL_DMA_Start_IT(&hdma_memtomem_dma1_stream0,
                    (uint32_t)src_buf, (uint32_t)dst_buf, TRANSFER_SIZE);
   /* Ring Buffer 示例 */
   #define RING_SIZE  256
   static volatile uint8_t ring_buf[RING_SIZE];
   static volatile uint32_t ring_head = 0, ring_tail = 0;
   ```
4. **ISR 约束**：仅做标记与唤醒，不做复杂逻辑。
   ```c
   /* ISR 最小化示例 */
   void DMA1_Stream5_IRQHandler(void) {
       if (__HAL_DMA_GET_FLAG(&hdma, DMA_FLAG_TCIF0_4)) {
           __HAL_DMA_CLEAR_FLAG(&hdma, DMA_FLAG_TCIF0_4);
           g_dma_complete = 1;                    /* 标记 */
           osSignalSet(task_id, SIG_DMA_DONE);   /* 唤醒任务 */
       }
   }
   ```
5. **DMA 通道管理与冲突检测**。
   ```bash
   # Linux DMA 通道状态
   cat /sys/class/dma/dma0chan*/in_use
   # 检查 DMA 中断
   cat /proc/interrupts | grep dma
   # RTOS DMA 通道分配检查
   rg -n "DMA.*Channel\|dma.*ch" src/ include/
   ```
6. **并发问题诊断**：竞态、优先级反转、缓存一致性。
   ```bash
   # Linux: 检查中断延迟
   cyclictest -p 99 -i 1000 -l 10000 -m
   # 检查软中断分布
   cat /proc/softirqs
   # 检查抢占配置
   cat /proc/config.gz | gunzip | grep PREEMPT
   # 缓存一致性检查（DMA 缓冲区）
   rg -n "dma_alloc_coherent\|dma_map_single\|cache_flush" src/
   ```
7. **回归验证**：高负载、突发流量、错误注入下稳定性验证。

## Commands
```bash
# 中断统计
cat /proc/interrupts
watch -n 1 "cat /proc/interrupts | grep <device>"

# 中断延迟测试
cyclictest -p 99 -i 1000 -l 10000 --mlockall -m

# DMA 状态
cat /sys/class/dma/dma0chan*/in_use

# ISR 代码审查
rg -n "ISR|IRQ|irq_handler|DMA.*IRQ" <driver_path>

# 寄存器级别中断检查
devmem2 <NVIC_ISER_addr>    # 中断使能寄存器
devmem2 <NVIC_IPR_addr>     # 中断优先级寄存器

# 逻辑分析仪 / 示波器触发
# （硬件工具，记录 GPIO toggle 测量 ISR 延迟）

# 压力测试
stress-ng --cpu 4 --io 4 --timeout 60s &
<latency-measure-cmd> --irq --dma --duration 60
```

## Evidence Template
```md
- Selected Pattern: [中断驱动/DMA/混合]
- Priority Config:
  | IRQ | Priority | Handler | Budget (us) |
  |-----|----------|---------|-------------|
  | TIM1_UP | 0,0 | ctrl_loop | <10 |
  | DMA1_CH5 | 1,0 | data_acq | <50 |
  | USART1 | 2,0 | uart_rx | <100 |
- Buffer Strategy: [single/double/ring] size=____
- ISR Budget: max=____ us, avg=____ us
- DMA Channel: ch____, direction=____, mode=circular/normal
- DMA Error Handling: [timeout/overflow/underrun recovery]
- Cache Coherency: [coherent/non-coherent + flush strategy]
- Stress Result:
  - Throughput: ____ KB/s
  - Latency: p50=____ us, p99=____ us, max=____ us
  - IRQ Loss: ____
  - DMA Error: ____
```

## Failure Handling
- IRQ 丢失或风暴时，先降速并确认中断屏蔽策略（检查 NVIC 优先级分组）。
- DMA 异常频发时，退回中断最小路径定位根因（检查 DMA 传输完成标志）。
- 优先级反转时，引入优先级继承或调整任务/中断优先级分配。
- 缓存一致性问题导致 DMA 数据错乱，改用 `dma_alloc_coherent` 或手动 cache flush。

## Quality Gate
- 必须说明 ISR 时间预算与 DMA 回调策略。
- 必须覆盖至少一个错误恢复路径。
- 压测结果需包含吞吐与时延双指标。
- ISR 执行时间必须 < 中断周期的 50%。
- DMA 缓冲区必须有溢出/欠载检测机制。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
