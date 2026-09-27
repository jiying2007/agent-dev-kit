# 任务：native-python38-support-20260927

- [x] T1 冻结目标、工作区边界与 3.8 导入/语法/依赖基线。
- [x] T2 修复 3.8 标准库、语法与运行时类型求值阻断；3.8 quick 48/48、路由 30/30 已通过。
- [x] T3 迁移构建/运行依赖、doctor、SBOM 与发布契约；3.8 wheel、doctor、Draft 2020-12、release 门禁和依赖审计已通过。
- [x] T4 接入 3.8/3.11/3.12 完整回归与本机复验；同快照完整矩阵各版本测试 90/90、路由 30/30、依赖审计通过，回执位于 `.cache/local-ci/full-parity-receipt.json`。
- [ ] T5 在新的 clean ADK 身份和审查成立后处理 Codex 来源绑定与 source-to-live。
- [ ] T6 更新四仓交付记录；Hub 仅 reviewing，不提升 active。

## 执行控制

- retry budget：同一失败最多重试 2 次，第二次仍无新增证据时回到假设矩阵。
- staleness threshold：每次门禁只接受最终改动后的源码快照，旧 7.8.0 回执仅作对照。
- heartbeat：完成导入、依赖、完整回归、Codex 绑定各阶段后更新本文件。
- plan completeness：T1–T6 均有明确退出证据，任一阶段失败不跨越到 live。
- stop condition：pass / replan / split / blocked / abort；未取得 clean 来源身份时保持 source-ready，不声明 release/live 完成。
- completion claim：3.8 原生公开功能与三版本门禁通过，Codex/Hub 层级按各自证据单列。
