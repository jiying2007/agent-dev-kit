---
name: adk-rtos-task-design
description: RTOS 任务、优先级、共享资源和实时性验证设计
version: 2.0.0
last_updated: 2026-09-17
triggers:
  - "RTOS任务"
  - "任务设计"
  - "实时任务"
  - "调度分析"
non_triggers:
  - 无 RTOS 的裸机项目
  - 只需要普通线程划分且无实时约束
inputs:
  - 任务周期、deadline、WCET/测量样本、中断负载、共享资源、栈与队列约束
outputs:
  - 任务模型、优先级依据、response-time/trace 证据、共享资源策略、残留风险
constraints:
  - 不使用固定经验阈值替代目标系统 deadline/latency budget
  - 必须区分测量值、估算值和未知值
  - 必须说明优先级、栈大小和共享资源策略依据
---

# adk-rtos-task-design

## Goal
- 建立可解释、可计算、可测量的 RTOS 调度模型。
- 用目标系统的 deadline、WCET、blocking 和 ISR interference 判断可调度性，而不是套用通用固定阈值。

## Prerequisites
- 锁定 RTOS/MCU/clock/tick 或 tickless 配置与调度策略。
- 列出任务周期或最小到达间隔、deadline、优先级候选、共享资源和 ISR 来源。
- WCET 不可获得时必须标记 `estimated` 或 `unknown`，不得伪装成已验证值。

## Workflow
1. **任务模型**：为每个 task/ISR 记录 period 或 sporadic arrival、deadline、WCET、priority、stack、blocking resource。
2. **优先级策略**：选择 Rate Monotonic、Deadline Monotonic、固定业务关键级或平台既有策略，并写出适用前提。
3. **响应时间分析**：对硬/准实时路径计算或保守估计 `R = C + B + interference`；多轮迭代至收敛或超过 deadline。
4. **ISR interference**：把高优先级 ISR、critical section、scheduler lock、关中断区间纳入预算，不能只分析 task-to-task 抢占。
5. **共享资源**：明确 PIP/PCP/lock-order/message-passing/lock-free 方案以及最坏 blocking time。
6. **栈与队列**：结合静态估算、stack high-water mark、burst/backpressure 样本给出容量依据。
7. **运行验证**：用 trace/周期统计核对 response time、jitter、deadline miss、queue high-water、stack high-water 和 CPU load。
8. **降级与恢复**：出现 deadline miss 时先识别 `C/B/interference` 主因，再调整优先级、临界区、任务划分或负载；禁止只“提高优先级”。

## Analysis Notes
- `RMA` 在本 Skill 中指 Rate Monotonic Analysis，不与 Direct Memory Access (`DMA`) 混用。
- Deadline Monotonic 只在适用固定优先级模型下使用；混合关键级、SMP 或动态优先级需记录模型限制。
- 对无法静态证明的路径，保留 `needs-runtime-evidence`，以目标板 trace/HIL 证据闭环。

## Commands
```bash
<rtos-trace-cmd> --duration <representative-window>
rg -n "xTaskCreate|thread_create|osThread|mutex|semaphore|critical|irq" <src_path>
rg -n "priority|PRIO|stack|queue|tickless|watchdog" <src_path>
<stack-high-water-command>
<deadline-or-latency-report-command>
```

## Evidence Template
```md
- Runtime Identity: RTOS / MCU / clock / tick-mode / scheduler
- Task Model:
  | Task/ISR | Period/Arrival | Deadline | WCET(status) | Priority | Stack | Blocking Resource |
- Priority Policy + Preconditions:
- Response-Time Analysis: C / B / interference / R / deadline
- ISR Interference Budget:
- Shared Resource Policy:
- Stack High-Water / Queue High-Water:
- Runtime Trace: response-time / jitter / misses / CPU load
- Unknowns / Model Limits:
- Verification Result: pass | needs-runtime-evidence | needs-fix
```

## Failure Handling
- response time 超 deadline：定位 WCET、blocking、ISR interference 或 overload 主因后 replan。
- stack/queue high-water 接近配置上限：补 burst 场景与安全余量依据，不直接拍脑袋扩容。
- trace 与静态模型冲突：以可重复运行证据为准修正模型，并保留差异原因。
- 无目标板或 trace 能力时：最多输出 `needs-runtime-evidence`，不得声称硬实时目标已满足。

## Quality Gate
- 每条关键实时路径必须有 deadline/latency budget 和 WCET 状态。
- 硬/准实时任务必须给 response-time 或等价可调度性证据。
- 必须纳入至少一个 ISR interference 与一个共享资源 blocking 场景。
- 每个任务必须有优先级与 stack sizing 依据；关键队列必须有 burst/backpressure 依据。
- 结论中的数值必须来自目标约束、测量或显式估算，不得使用无来源固定经验阈值。
