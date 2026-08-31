# 执行任务：remove-external-runtime-compat

- [x] 需求确认与边界冻结
- [x] 实施改动并补充测试
- [x] 本地验证（lint/test/build/smoke）
- [x] 代码评审与分级闭环（blocker/major/minor）
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围（scope_write）：ADK router/pilot/control scripts/tests/change docs；根仓集成门禁；clean bundle 可用后更新团队资产。
- 读取范围（scope_read）：根参考 registry/lifecycle、`~/codex` source/live 状态、历史 evidence。
- 是否与其他任务冲突（同文件/同 contract/同配置）：共享 routing/manifest/CI contract，必须串行；`~/codex` manifests 有用户改动，不在本阶段写入。

## 轻量工件与收敛结论
- 需求梳理工件：`requirements.md`、`proposal.md`、`design.md`
- task checklist 工件：本文件、`checklist.md`
- 执行反馈/验收记录工件：`negative-results.md`、后续 `verify-report.md`
- 收敛结论或阻塞说明：ADK source-ready；团队 Bundle plan-ready。clean release、团队 apply 和 live prune 受未提交 source 与用户 dirty `~/codex` 约束，保持 live-pending。

## Goal Closure

- goal_statement：保留根仓参考输入，ADK 不再提供外部运行兼容。
- completion_claim：ADK source、路由、pilot、退役 tombstone、runtime required/forbidden footprint 和团队 Bundle plan 已实现并验证。
- required_evidence：双 Python full parity、routing 30/30、runtime target/footprint tests、无外部兼容文本的 team-core Bundle、团队 import plan。
- claimant：主 Agent。
- verifier：author-self-review + deterministic gates；未冒充独立 reviewer。
- open_items：clean commit/release、团队 Bundle apply、`~/codex -> ~/.codex` prune/apply 与 strict footprint pass。
- retry_budget：2；已用 2 次负路径收敛版本不可变与 parity tombstone 问题。
- staleness_threshold：连续 2 次同类失败无新证据即 replan。
- heartbeat：source、bundle plan、full parity 均已有检查点。
- stop_condition：source pass；live 阶段 split，等待 clean release 和集成窗口。
