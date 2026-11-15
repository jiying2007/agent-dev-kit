---
name: adk-rtos-task-design
description: "用于 RTOS 任务优先级、时序约束、同步资源与调度风险设计；不用于纯裸机单循环程序或未经测量声称实时性达标。"
version: 2.0.2
last_updated: 2026-11-15
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
3. **响应时间分析**：先确认模型适用性，再按下节计算 `R = C + B + interference` 或使用目标已有分析器；列出迭代与输入依据，不能仅填写总公式。
4. **ISR interference**：把高优先级 ISR、critical section、scheduler lock、关中断区间纳入预算，不能只分析 task-to-task 抢占。
5. **共享资源**：明确 PIP/PCP/lock-order/message-passing/lock-free 方案以及最坏 blocking time。
6. **栈与队列**：结合静态估算、stack high-water mark、burst/backpressure 样本给出容量依据。
7. **运行验证**：用 trace/周期统计核对 response time、jitter、deadline miss、queue high-water、stack high-water 和 CPU load。
8. **降级与恢复**：出现 deadline miss 时先识别 `C/B/interference` 主因，再调整优先级、临界区、任务划分或负载；禁止只“提高优先级”。

## Analysis Notes
- `RMA` 在本 Skill 中指 Rate Monotonic Analysis，不与 Direct Memory Access (`DMA`) 混用。
- Deadline Monotonic 只在适用固定优先级模型下使用；混合关键级、SMP 或动态优先级需记录模型限制。
- 对无法静态证明的路径，保留 `needs-runtime-evidence`，以目标板 trace/HIL 证据闭环。

### 固定优先级计算（仅适用时）
单核、抢占式、固定优先级、独立周期/有界 sporadic 任务、deadline 不大于 period、无未建模 release jitter 或自挂起时，使用同一时间单位：
```text
R0 = Ci + Bi
Rnext = Ci + Bi + sum(ceil(R / Tj) * Cj, j in higher-priority tasks) + Ii(R)
```
`C` 是有依据的 WCET 上界，`B` 是一次作业的最坏阻塞，`T` 是周期/最小到达间隔；`Ii(R)` 汇总窗口 R 内 IRQ 干扰。调度开销纳入对应项，中断不得又计为 task 又重复相加。收敛且 `R <= deadline` 仅证明所声明模型及上界条件下可调度；超过 deadline 停止，缺上界/不收敛记未知。SMP、jitter、自挂起或任意 deadline 需适配模型，不能硬套本式。

例如 `Ci=2, Bi=1, Di=5`、高优先级任务 `Cj=1,Tj=4`：`3→4→4`；再加 `Cirq=0.5,Tirq=3`，得到 `3→4.5→6`，超过 deadline。此为计算示例，不是板端实测。方法背景：https://www.cs.york.ac.uk/rts/publications/Davis2008a.html 。

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
- trace 超出模型上界时查漏项并修正模型；短期观测低于保守上界不能证明可降低 WCET。实测最大值与已证明上界分开，保留差异原因。
- 无目标板或 trace 能力时：最多输出 `needs-runtime-evidence`，不得声称硬实时目标已满足。

## Quality Gate
- 每条关键实时路径必须有 deadline/latency budget 和 WCET 状态。
- 硬/准实时任务必须给 response-time 或等价可调度性证据。
- 必须核对 ISR interference 与共享资源 blocking；确无相关干扰/资源时给出 `I=0/B=0` 的依据，不虚构场景。
- 每个任务必须有优先级与 stack sizing 依据；关键队列必须有 burst/backpressure 依据。
- 结论中的数值必须来自目标约束、测量或显式估算，不得使用无来源固定经验阈值。
