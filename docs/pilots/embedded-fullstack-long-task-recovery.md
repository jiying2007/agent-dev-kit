# Pilot: embedded-fullstack-long-task-recovery

status: evidence-ready

## 目标场景

嵌入式全栈长任务，例如 Linux BSP 迁移、驱动到应用链路 bring-up、上位机产测工具联调或跨组件重构，需要阶段检查点、恢复摘要、中途改范围处理和失败回退。

## 预期路由

- primary: `adk-planning-execution-loop`
- supporting: `adk-task-breakdown`, `adk-verification-before-completion`
- internal fallback: 平台执行能力不足时降级为串行阶段检查点，不加载外部流程

## 验证证据

### 原始任务输入

用户要求 ADK 原生覆盖长任务执行和恢复能力，并保持嵌入式全栈目标。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot long-task --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `plan.md` | BSP/OTA 长任务阶段计划 |
| `checkpoints/01-discovery.md` | 第一阶段 checkpoint |
| `checkpoints/02-package-self-check.md` | 第二阶段 checkpoint |
| `scope-change.md` | 中途改范围记录，明确 HIL 推迟 |
| `recovery-summary.md` | 恢复摘要、下一步和回退锚点 |
| `verify-report.md` | 最终验证与残留缺口 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot long-task --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成阶段计划、两个 checkpoint、中途改范围、恢复摘要、回退锚点和验证报告 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-fullstack-long-task-recovery/evidence.md` |

### 残留缺口

- 仍需在真实 BSP 迁移或驱动 bring-up 上复跑。
- 本 pilot 证明工件闭环和恢复机制，不证明硬件行为。
