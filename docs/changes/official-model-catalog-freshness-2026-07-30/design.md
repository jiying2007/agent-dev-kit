# 设计：official-model-catalog-freshness-2026-07-30

## 决策

采用“稳定 provenance ID + 易变内容显式更新”：

- 保留 `openai-latest-model-gpt-5-5`，避免破坏历史 candidate、decision 和 adoption 引用。
- 标题改为不绑定单一模型版本的 current catalog/guidance。
- 增加 `freshness_decision=update` 和 `verified_claim`，让本轮 keep/update/supersede/retire 选择可机器读取。
- `retrieved_at=2026-07-30`，`expires_at=2026-10-28`，严格遵守 90 天上限。
- decision 只允许把该页面作为 volatile model-selection evidence；任何默认值变更必须另走 eval 和 owner review。

## 兼容性

不改变 schema、source ID、provider coverage 或 runtime 边界。新增字段由当前 JSON consumer 忽略或保留，不需要兼容 reader。

## 风险与回滚

- 官方页面继续变化：expiry 到期后重新进入 review queue，不自动续期。
- source ID 名称含历史版本：由 `legacy_id_note` 明确解释；后续如需重命名，必须先迁移所有引用。
- 复核判断错误：恢复原记录会重新触发过期失败，确保不能带着未知 freshness 继续发布。
