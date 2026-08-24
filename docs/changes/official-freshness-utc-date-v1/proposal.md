# 变更提案：official-freshness-utc-date-v1

## 背景
- 同一工作树在香港宿主（2026-08-24）与 UTC Docker（2026-08-23）运行 official freshness
  gate，前者失败、后者通过。

## 问题陈述（单问题）
- 本变更只解决：默认 freshness 评估日期不能随宿主本地时区变化。
- 证据：同一 source snapshot 的 host strict exit 1，Python 3.11 isolated full exit 0；唯一差异是日期。

## 目标
- 统一官方来源 freshness gate 的 UTC 日期语义

## 非目标
- 不延长或刷新任何 source expiry；不改变 `expires_at < today` 规则。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（时区、日期边界、报告可审计性）
- [x] 已明确验证命令与通过标准
- [x] 证据充分

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：跨环境一致的 release/governance gate。

## 变更重复性检查
- 已检索 official gate、readiness 和 UTC timestamp 实现；official gate 当前直接使用 `date.today()`。
- 本次只修复已复现入口；其他 date policy 作为后续审计候选。

## Breaking Change 检查
- [x] 否：日期比较规则不变，只统一默认时区
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements：UTC default + summary disclosure + cross-TZ regression。
- design：`datetime.now(timezone.utc).date()`。
- tasks：T1-T4。

## 安装范围与依赖边界
- 安装范围：ADK core governance。
- 依赖边界：Python 标准库；无网络/写入。

## Prompt 回归证据计划
- before/after：`TZ=Pacific/Kiritimati` 与 `TZ=America/Adak`。
- 失败样例：cross-TZ summary regression。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：两个 TZ 的 `evaluated_at` 相同且 `date_basis=utc`；workflow 回归恢复。

## 备选方案与取舍
- A：刷新 expiry 掩盖差异，拒绝。
- B：UTC canonical date + summary disclosure，选用。
- 理由：CI/host 可重放、无需平台配置。

## 风险与回退
- 风险：本地午夜附近的失败时间最多平移到 UTC 午夜；summary 明确披露评估日。
- 回退：恢复 date.today 并删除测试；不涉及数据迁移。
