# Requirements: Runtime Control V1

## R1 唯一实现
- ADK 仅一个 `agent_dev_kit.runtime_control` Engine；Codex adapter 不含 policy/decision。
- 旧 token monitor、execution guard、usage dashboard、session coach 决策全部删除。

## R2 唯一合同
- 仅保留 `runtime_control.event/v1`、`runtime_control.state/v1`、`runtime_control.decision/v1`。
- usage 只使用累计 snapshot，不兼容 delta 或旧 schema。

## R3 唯一 Goal SSOT
- Runtime Control Journal 是唯一 active goal/checkpoint/retry/evidence/progress store。
- 不读取 `thread_goals`，不从 thread title/session 正文推断，不迁移旧 goal。

## R4 唯一策略
- 优先级固定：invalid -> invalid completion -> pass -> exhausted -> replan -> compact -> checkpoint -> continue。
- completed 需 checkpoint、evidence、open items、retry/stale/no-progress 全闭环。

## R5 唯一配置
- Codex 仅 `manifests/runtime_control.json`；删除 `session_coach.json`、`goal_templates.json` 运行策略。
- 所有阈值、retention、gate policy 只出现一次。

## R6 唯一 CLI
- 仅 `scripts/runtime-control.sh`，支持 goal/heartbeat/progress/checkpoint/retry/evidence/snapshot/watch/gate。
- 删除 usage-report、usage-tail、session-coach、final-ready 与 ADK token/execution CLI；无 alias。

## R7 安全与隐私
- journal 不存 prompt/messages/tool output/objective 原文；只存 ID、hash、计数、时间、状态。
- adapter 只读 Codex SQLite/rollout；Engine 不读取 Codex 私有路径；副作用命令需原审批边界。

## R8 分发
- ADK Engine 以 pinned wheel + SHA 进入 Codex build；Codex 无源码副本、fallback Engine 或 sibling path。
- 依赖缺失/版本/hash 不一致 fail closed。

## R9 Zero residual
- 旧 active module/command/schema/manifest/import/build/live 路径为 0；archive/Git history 仅作 provenance。
- 旧 runtime state 不读取；受管旧 live asset 由 apply plan 删除。

## R10 验收
- reducer replay/idempotency、goal/usage/progress/retry/evidence/gate、adapter SQLite/rollout、跨仓和 live smoke 全覆盖。
- 三仓 full、build/doctor/plan/dry-run/apply/check/runtime health 与 independent review 通过。

## Blocker policy
- dirty overlap、wheel 不可复现、zero-residual 非零、apply plan 无法精确删除、live health 失败均停止。
- retry budget=2；staleness threshold=45 分钟；stop=pass|replan|split|blocked|abort。
