# 设计说明：token-context-governance-v2

## 决策

- D1：soft warning 与 hard failure 分离；warning 用于演进余量，不能替代 hard gate。
- D2：task-cost 使用显式风险信号和确定性阈值，不用不可审计的模型分类。
- D3：working-tree 是开发期验证模式；稳定 fingerprint 只证明“测的是同一份改动”，不证明 release clean。
- D4：Codex v3 保存目标路径 identity digest；mutation 用期望输出判定 already-applied，keep 用原始 identity 判定未漂移。
- D5：workflow activation 是 profile 语义，不删除 vendor inventory；lazy 只改变加载时机。
- D6：same-run evidence 只跨同一父进程和相同 workspace fingerprint；复用失败退回真实命令。
- D7：Hub receipt 是显式 cache，保存 hash 与有界 summary；registry、workspace HEAD 或 selected evidence 变化即失效。
- D8：review packet 只排序和分批，不生成内容结论或 owner 决策。
- D9：跨仓 bundle 是 provenance，不是 release authorization。

## 安全与隐私

- 所有 receipt 只保存路径、计数、hash、耗时和枚举，不保存 raw prompt/query/diff/log。
- Hub cache 位于 `.cache/knowledge-hub/context-receipts/`，显式 key 仅允许安全字符。
- 任何 apply/active/memory/remote 权限保持现状。

## 验证策略

- ADK/root：定向 contract tests、quick/smoke/full 与 fingerprint 漂移负例。
- Codex：unit、doctor/governance、五 profile smoke、source-to-live v3 正负例。
- Hub：context/capture/review queue pytest、full pytest、knowledge-check。
- 终态：release bundle、final-ready、session coach、Hub reviewing candidate。
