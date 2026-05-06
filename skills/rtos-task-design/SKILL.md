---
name: rtos-task-design
description: RTOS 任务模型与优先级设计
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "RTOS任务"
  - "任务设计"
  - "实时任务"
non_triggers:
  - 无 RTOS 的裸机项目
inputs:
  - 任务列表、实时性指标
outputs:
  - 任务划分与调度策略
constraints:
  - 必须说明优先级与栈大小依据
---

# rtos-task-design

## Goal
- 构建可解释、可验证的 RTOS 任务调度模型。

## Prerequisites
- 收集任务周期、截止时间、共享资源与中断负载。
- 明确是否存在硬实时路径。

## Workflow
1. 任务分解：按功能与实时性划分任务边界。
2. 优先级分配：依据 deadline 和关键性设定优先级。
3. 栈与队列规划：给出栈大小估算和队列容量依据。
4. 竞争治理：定义互斥、优先级反转与死锁防护策略。
5. 调度验证：通过 trace 验证时延和抖动是否满足目标。

## Commands
```bash
<rtos-trace-cmd> --duration 60
rg -n "xTaskCreate|thread_create|mutex|semaphore" <src_path>
rg -n "priority|PRIO" <src_path>
rg -n "deadlock|DEADLOCK|lock_order" <src_path>
```

## 任务优先级设计
| 原则 | 说明 |
|------|------|
| Rate Monotonic | 周期越短优先级越高 |
| Deadline Monotonic | 截止时间越近优先级越高 |
| 关键性提升 | 安全关键任务可覆盖 deadline 排序 |
| 中断与任务分离 | ISR 仅做信号量/队列通知，不在 ISR 中处理逻辑 |

## 资源竞争与死锁预防
| 策略 | 说明 |
|------|------|
| 优先级继承 (PIP) | 低优先级任务持有锁时继承高优先级 |
| 优先级天花板 (PCP) | 锁创建时设定天花板优先级 |
| 锁序协议 | 全局统一锁获取顺序，禁止嵌套反转 |
| 无锁设计 | 用 ring buffer + 原子操作替代互斥锁 |
| 超时机制 | mutex 获取必须带超时，避免无限阻塞 |

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "任务少不需要优先级分析" | 即使 2 个任务也可能死锁 | 用 RMA/DMA 方法论分配优先级 |
| "互斥锁够用了" | 优先级反转会让高优先级任务饿死 | 引入 PIP 或 PCP 协议 |
| "死锁概率很低" | 死锁一旦发生系统完全挂死 | 必须有锁序或超时保护 |

## Evidence Template
```md
- Task List + Priority:
- Stack/Queue Sizing Basis:
- Shared Resource Policy:
- Worst-case Latency:
- Verification Result:
```

## Failure Handling
- 若关键任务 deadline 未达标，先降噪并重排优先级。
- 若出现优先级反转，优先引入优先级继承或协议修正。

## Quality Gate
- 每个任务必须有优先级与栈大小依据。
- 必须给出关键路径 worst-case latency 数据。
- 需包含至少一个竞争场景的防护方案。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
