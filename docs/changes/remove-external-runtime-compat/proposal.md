# 变更提案：remove-external-runtime-compat

## 背景
- ADK 已具备需求、计划、调试、审查、并行、worktree、完成验证和分支收尾的原生能力，默认运行链也没有激活外部兼容流程。
- 当前仍保留显式外部 fallback 文案、下线矩阵和兼容门禁，造成运行策略与实际主链不一致。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：从 ADK 生产资产中移除外部运行兼容面，同时保留根仓只读参考来源。
- 触发证据（日志/复现/反馈）：用户明确决定“根仓参考保留，ADK 中不再兼容”。

## 目标
- 移除外部运行兼容面

## 非目标
- 不删除或清理根工作区对应参考子模块。
- 不修改历史 archive、参考原文或既有 provenance。
- 不绕过 clean release 和 source-to-live 门禁写入 `~/.codex`。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：修改 runtime router 与全局治理门禁，属于 core policy，不是 optional Skill。

## 变更重复性检查
- 已检索是否存在相同 change-id/同类方案：已有 fallback sunset 治理和历史吸收报告，但没有“完全移除兼容运行面”的 active change。
- 若有历史方案，本次差异与必要性：过去目标是逐项 sunset，本次 owner 决策直接终止兼容产品面；历史材料继续作为 provenance。

## Breaking Change 检查
- [ ] 否：不涉及兼容性破坏
- [x] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：`requirements.md`
- design 决策：`design.md`
- tasks 追溯关系：`tasks.md`

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：global-ready ADK runtime bundle。
- 依赖边界（脚本/数据/上下文）：ADK manifest/skills/tests/pilots；团队资产仅通过 release bundle 导入；根参考仓不进入 runtime。

## Prompt 回归证据计划
- before/after 对比输入：显式旧外部 brainstorming 名称、复杂只读 review 反馈、调试和计划请求。
- 失败样例保留方式：更新 `tests/fixtures/skill_trigger_cases.tsv` 和定向 matcher 测试；负结果进入 `negative-results.md`。

## 收敛模式与退出条件
- 当前模式（diagnosis/repro/planning/execution）：execution。
- 退出条件（进入执行/收敛）：ADK source checks 通过；clean release 不满足时按 `source-ready/live-pending` 收口。

## 备选方案与取舍
- 方案 A：保留隐藏兼容 profile，仅去掉用户可见文案。
- 方案 B：删除 ADK runtime fallback 契约，保留根仓参考输入。
- 选型理由：用户明确选择方案 B；它同时消除重复产品面和默认/兼容路由歧义。

## 风险与回退
- 风险：显式点名旧 Skill 的用户不再获得原实现；迁移为按意图选择 ADK 原生 Skill。
- 回退：回退本 change 的 source commit，并从上一份 clean runtime bundle 重新导入和 apply；不依赖根参考仓直接安装。
