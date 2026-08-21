# Requirements

## Goal

优化共享代码审查闭环，使审查结论能够绑定输入快照，并明确区分外部语义扫描、本地事实核验和机械验证门禁。

## Scope

- 更新 `adk-code-review-loop` 的输入、流程、报告和质量门禁。
- 补充 staged/working-tree 边界、unstaged overlay 和 reviewer independence。
- 增加确定性文本契约测试。

## Non-goals

- 不要求不同审查工具输出完全一致。
- 不替代项目自己的构建、测试和提交门禁。
- 不把 AI 审查提升为高风险变更的最终 owner 决策。

## Acceptance

- 报告可记录 Review Target、Snapshot ID、Working Tree Overlay 和 Reviewer Independence。
- 机械门禁通过不能被解释为语义审查通过或最终可交付。
- staged 修复未重新暂存时不能声称已复审最新修复。
- quick、SOP 定向测试与完整回归通过。

## Rollback

回退本 change 对 skill、fixture 和 SOP 测试的修改；已导出的下游版本按其资产生命周期单独回退。
