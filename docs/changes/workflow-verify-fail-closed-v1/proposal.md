# 变更提案：workflow-verify-fail-closed-v1

## 背景
- `workflow.sh verify` 在 Bash `if ... && run_verify_checks` 条件上下文中调用验证函数。
- Bash 会在该上下文抑制函数内部的 `set -e`；前置 strict gate 失败后，后续 format 成功会把
  函数最终状态覆盖为 0。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：任一 verify 子门禁失败时，workflow 必须 fail closed，不能写
  `stage: verified`。
- 触发证据：`realtime-token-usage-monitor-v1/verify-report.md` 含 27 条 `[FAIL]`，但命令退出 0
  且 state 被写为 verified。

## 目标
- 修复 verify 条件上下文吞掉底层门禁失败的假绿状态

## 非目标
- 不修改 official freshness 日期语义、不刷新 expiry、不改变 review/archive gate。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（Bash errexit 条件上下文、失败码传播、后续 gate 误覆盖）
- [x] 已明确验证命令与通过标准
- [x] 信息充分，有真实复现和最小 deterministic fixture

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：通用 change lifecycle 的完成验证正确性。

## 变更重复性检查
- 已检索 `workflow.sh`、`test_workflow.sh`、change governance；没有首门禁失败、末门禁成功的负例。
- 本次只补显式短路和真实脚本副本回归，不创建新 workflow。

## Breaking Change 检查
- [x] 否：成功路径不变；仅修复错误的假绿路径
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：proposal 单问题 + design D1-D3。
- design 决策：显式 `&&`/return status，不依赖 `set -e` 隐式语义。
- tasks 追溯关系：T1-T4。

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：ADK core lifecycle。
- 依赖边界（脚本/数据/上下文）：Bash；无网络、依赖、runtime 或权限变化。

## Prompt 回归证据计划
- before/after 对比输入：validate exit 23 + format exit 0。
- 失败样例保留方式：`tests/test_workflow_verify_fail_closed.sh`。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：负例从假 verified 变为 verify-failed，现有 workflow/full regression 通过。

## 备选方案与取舍
- 方案 A：继续依赖 `set -e`，拒绝；调用上下文会改变语义。
- 方案 B：在函数内显式短路并返回失败，选用。
- 选型理由：最小、确定性、保留原失败码和报告。

## 风险与回退
- 风险：修复后暴露此前被吞掉的真实失败，这是正确 fail closed，不是兼容回归。
- 回退：单行函数改动和独立测试可撤销；不涉及数据迁移。
