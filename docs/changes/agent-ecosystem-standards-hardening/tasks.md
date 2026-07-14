# 执行任务：agent-ecosystem-standards-hardening

- [x] T1 需求确认、来源复核、重复性审计与边界冻结
- [x] T2 在既有 SSOT 中增加六类治理契约和来源决策
- [x] T3 增加跨 manifest checker、正向 bundle 与负向 fixtures
- [x] T4 接入 strict/full tests，同步参考矩阵与调研报告
- [x] T5 执行定向、严格、全量验证和完成前证据审计

## Ownership 与并行冲突检查
- 写入范围（scope_write）：`agent-dev-kit/manifests/` 指定 SSOT、`scripts/` 新 checker 和 validation 接线、`tests/`、`fixtures/agent-ecosystem-standards/`、本 change、相关 adoption/report 文档。
- 读取范围（scope_read）：ADK README、AGENTS、RC2 change/report、既有 checker/fixtures、根仓 adoption ledger。
- must_not_touch：任务开始时已存在 dirty 状态的参考子仓；compiler/runtime；用户级 runtime install 目录。
- 是否与其他任务冲突（同文件/同 contract/同配置）：共享 manifests 串行修改；不使用子代理，避免写冲突。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist 工件：本文件与 `checklist.md`。
- 执行反馈/验收记录工件：`negative-results.md`、`session-state.md`、最终调研报告。
- 收敛结论或阻塞说明：实现、strict、quick/full regression 与 harden readiness 已通过；两次真实门禁负结果均已修复并留痕。根仓 aggregate 仅因本次未提交 strict 子仓 dirty 而 54/56，未通过自动 commit 或放宽门禁规避。
