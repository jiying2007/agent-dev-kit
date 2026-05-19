# Pilot: embedded-branch-closeout

status: evidence-ready

## 目标场景

嵌入式开发分支完成后，基于验证证据选择合并、创建 PR、保留分支或丢弃实验分支，并明确远端操作、回滚和人工确认边界。

## 预期路由

- primary: `adk-branch-closeout`
- supporting: `adk-verification-before-completion`, `adk-commit-pr-quality-gate`
- fallback: 仅当远端 PR 工具或组织流程必须使用迁移期流程时显式使用

## 验证证据

### 原始任务输入

用户要求补齐 Superpowers finishing-a-development-branch 的分支收尾决策能力，同时遵守本地验证、PR/远端操作人工确认和回滚记录。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot branch-closeout --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `branch-status.md` | 分支状态、dirty/untracked 和远端操作边界 |
| `verification-index.md` | 验证命令和退出码 |
| `risk-rollback.md` | 风险和回滚策略 |
| `closeout-decision.md` | 收尾决策 |
| `pr-checklist.md` | PR 必填项 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot branch-closeout --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成分支状态、验证索引、风险回滚、收尾决策和 PR checklist | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-branch-closeout/evidence.md` |

### 残留缺口

- 真实 merge、push、PR 创建仍需用户明确授权。
- 本 pilot 证明收尾决策链路，不执行远端操作。
