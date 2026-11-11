---
name: adk-goal-authoring
description: "用于新建或实质修订 Goal 合同、原验收映射和可关闭交付批次；不用于已有 Goal 的日常执行、CI 状态查询或只读计划。"
version: 0.1.2
last_updated: 2026-11-11
triggers:
  - "生成Goal"
  - "Goal怎么写"
  - "目标合同"
  - "重写Goal验收"
  - "目标过大"
non_triggers:
  - "已有Goal继续执行"
  - "只查看CI状态"
  - "只读计划"
  - "单点修复或纯格式修改"
inputs:
  - 用户原目标、验收分母、边界和已有状态
outputs:
  - Goal 合同、当前1–4个可关闭交付、只读恢复入口
constraints:
  - 不重建活动 Goal、不清零历史、不自行设置权限或宿主预算
  - 结构校验不等于证据验真和任务完成
---

# Goal 合同生成

## Goal
将新目标或实质变更转成可验证的交付合同；**已存在有效合同时只改受影响条目，不重新规划全部历史**。日常执行交给 `adk-planning-execution-loop`，不是本 Skill 的触发条件。

## Workflow
1. 先检查是否已有 Goal/合同、唯一 current-state 与原始验收 ID。只是继续执行、等待 CI 或查看进展时停止合同生成，交现有执行/查询入口。
2. 明确完成后可观察的行为、失败反例、权限、非目标及验收证据；研究任务区分直接证据、代理证据和未知。
3. 保留原验收分母与父子映射，拆出可实际关闭的交付。仅选 1–4 项当前可执行且依赖已满足的子项；每项绑定真实范围、验证命令、done criteria 与证据层级。
4. 验证分层：改动时先定向验证，批次末复核受影响范围，**整个 Goal 完成时才做整体 final**；共享契约、生产或权限变化立即使用原门禁。
5. 预算只能提出有依据的估计；尚无可靠用量时 `budget_proposal.tokens=null`，写明待测量原因，**不编造 Token 数字**，不操作宿主预算。停止/重排条件与成本观测相互独立，不设每日费用硬限。
6. 只有目标、验收、依赖或验证路径发生实质变化才重规划；保留未关闭项及旧证据链接，不因更换编号、重复证明或提高预算重置累计。
7. 当前恢复入口默认 ≤8 KiB，证据引用 ≤8、历史索引 ≤3、下一动作 ≤3。历史与原始工具结果按需读取，合同生成后交现有执行流程。

## Commands
从实际 ADK 源根调用；跨仓需核验源位置：
```bash
rtk bash scripts/devkit.sh goal plan-check --plan <goal.json> --state <current.json>
rtk bash scripts/devkit.sh goal render --plan <goal.json>
rtk bash scripts/devkit.sh goal resume --plan <goal.json> --state <current.json>
```
按需读取 [合同示例](references/goal-plan.json)。简单任务可用文字，不强制 JSON；这些命令均只读，不能验证业务证据或创建原生 Goal。

## Quality Gate
核对原验收映射完整、依赖无环、选中项有退出标准、无假关闭、权限不扩张及恢复状态有界。重复/未变化的证据不算进展；外部阻塞等待真实触发事件，不轮询模型。缺证据标记 UNKNOWN；结构通过不是模型行为评测或 Goal 完成。
