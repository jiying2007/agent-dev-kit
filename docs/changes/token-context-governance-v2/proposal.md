# 变更提案：token-context-governance-v2

## 问题

v1 已压缩默认上下文，但任务成本仍主要靠文字约定，跨仓验证与 Knowledge Hub
候选治理缺少可复用 receipt。结果是规则接近硬上限、合法 dirty 集成态被误报、
同轮 smoke 重复执行，以及 reviewing 候选持续积压。

## 目标

- 把 task-cost、上下文成本、working-tree 集成态和跨仓交付身份变成机器可验 receipt。
- 为 `AGENTS.md` 保留演进余量，hard limit 不变，新增 soft warning。
- 强化 Codex plan 前置条件与 lazy activation 语义，并减少同轮 smoke 重复执行。
- 为 Hub 提供有界 capture、可失效 context receipt 和带 SLA 的人工 review packet。

## 非目标

- 不自动批准 Hub 内容、提升 active、关闭 owner gate或写 memory。
- 不放宽 release clean-state、source-to-live、权限和安全门禁。
- 不自动 commit、push、merge、rebase、tag 或发布。

## 边界与退出条件

- scope_write：本 change、相关 ADK/root/Codex/Hub 实现、测试与文档。
- must_not_touch：参考子仓业务内容、远端、凭证、`~/.codex` 手工资产。
- retry_budget：同一根因最多 2 次；第三次前 replan。
- staleness_threshold：相关仓 HEAD 或冻结的 dirty fingerprint 改变即停止整合。
- stop_condition：`pass | replan | split | blocked | abort`。

## Breaking Change

Codex apply plan 从 schema v2 升级到 v3；旧 plan 必须重新生成。回退方式是恢复
v2 producer/validator，并重新 plan，不复用跨版本 receipt。
