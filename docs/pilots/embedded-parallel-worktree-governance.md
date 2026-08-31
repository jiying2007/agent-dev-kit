# Pilot: embedded-parallel-worktree-governance

status: evidence-ready

## 目标场景

嵌入式多模块任务需要在驱动、组件、测试或文档之间拆分并行工作，或需要 worktree 隔离分支执行。

## 预期路由

- primary: `adk-parallel-agent-governance`
- supporting: `adk-worktree-governance`, `adk-task-breakdown`, `adk-verification-before-completion`
- internal fallback: 平台子代理行为不稳定时降级为串行任务包执行

## 验证证据

### 原始任务输入

用户要求把子任务审查、`scope_write`、`must_not_touch` 和最终整合验证脚本化，形成 ADK 原生并行治理闭环。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot parallel-governance --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `task-packages.tsv` | 子任务 `scope_write` / `must_not_touch` / `verify` |
| `conflict-matrix.md` | 并行冲突矩阵 |
| `subagent-review.md` | 子任务交付审查 |
| `worktree-decision.md` | worktree 创建/跳过决策 |
| `integration-verify.md` | 最终整合验证命令 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot parallel-governance --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成任务包、冲突矩阵、子任务审查、worktree 决策和整合验证证据 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-parallel-worktree-governance/evidence.md` |

### Fallback Decision

只允许在 ADK 内部降级为串行执行：现有任务拆分、scope 审查和整合验证证据保持有效，外部参考流程不作为运行 fallback。

### 残留缺口

- 仍需在真实多 agent 写入场景中验证冲突处理。
- worktree 创建和清理仍需真实 git worktree pilot 补充。
