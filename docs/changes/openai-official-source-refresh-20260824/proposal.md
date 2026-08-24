# 变更提案：openai-official-source-refresh-20260824

## 背景
- 27 条 OpenAI official source 于 2026-08-23 到期，strict/workflow 正确 fail closed。
- 本轮 goal 正在优化 Token、长任务和完成验证，需基于当前官方证据而不是过期快照。

## 问题陈述（单问题）
- 只解决：逐条复核已到期的 27 条官方来源并刷新 freshness metadata。
- 证据：official gate 列出 27 个 expired ID；官方网页 27/27 可访问且核心 decision 语义仍存在。

## 目标
- 复核并刷新二十七条 OpenAI 官方来源新鲜度

## 非目标
- 不改变 adoption decision/status，不复制实现，不启用 runtime/MCP/network/write，不刷新未到期来源。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（redirect、anchor 漂移、旧 decision 失真、仅改日期的假复核）
- [x] 已明确验证命令与通过标准
- [x] MCP docs 不可用已记录，按 openai-docs 技能降级为官方域 web 只读核验

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：官方来源治理元数据，不是 runtime 能力。

## 变更重复性检查
- 已检索历史 source refresh；沿用“官方一手来源、决策不自动升级、过期不放宽”的模式。
- 本轮覆盖 OpenAI 27 条 90 天窗口，历史 refresh 不包含本日期批次。

## Breaking Change 检查
- [x] 否：仅 metadata 日期变化
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements：27/27 页面和关键边界复核；只更新 dates。
- design：stable URL 保留，redirect 作为 evidence，不 silent rewrite provenance。
- tasks：T1-T4。

## 安装范围与依赖边界
- 安装范围：ADK governance metadata。
- 依赖边界：official web read-only；无新依赖/安装。

## Prompt 回归证据计划
- before/after：expired=27 -> expired=0。
- 失败样例：MCP/manual helper 不可用、redirect/anchor drift 均进入 negative evidence。

## 收敛模式与退出条件
- 当前模式：verification。
- 退出条件：official/strict/workflow/full gates 通过，decision diff 为空。

## 备选方案与取舍
- A：批量延长而不读页面，拒绝。
- B：逐页核验后机械更新匹配日期，选用。
- 理由：最小 metadata diff 且证据可追溯。

## 风险与回退
- 风险：部分 Codex URL redirect 到 ChatGPT Learn、Apps SDK redirect 到 Plugins；原 URL 仍有效，
  保留稳定 provenance，后续 canonical URL 迁移另审。
- 回退：恢复 27 条旧日期并让 gate 重新阻断。
