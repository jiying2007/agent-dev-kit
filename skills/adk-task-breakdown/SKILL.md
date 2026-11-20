---
name: adk-task-breakdown
description: "用于复杂任务拆解、公共契约迁移及并行边界；单点小修无需拆包，不替代已批准计划的执行。"
version: 1.5.1
last_updated: 2026-11-17
triggers:
  - "拆解任务"
  - "任务拆分"
  - "任务太大"
  - "公共契约迁移拆分"
non_triggers:
  - 单点微调任务
  - 单文件小修且无共享依赖变更
inputs:
  - 需求范围、里程碑、模块边界与依赖关系
outputs:
  - 任务、依赖、owner、冲突与验证
constraints:
  - 每项有可执行验证，批次不代表最终集成通过
  - 同一 shared contract/schema 不并行写
  - 机器包仅 adk-task-package-schema-v2；structured_output_schema、strict_schema_decision 及跨字段规则须校验
---

# adk-task-breakdown

## Goal
为复杂任务划清交付边界；小修或已有任务包直接退出。

## Choose the smallest useful plan
- **single-slice**：最小可观察纵向交付，不强制拆包、估时或并行。
- **multi-slice**：按真实依赖拆分，每项有产物、owner 和验证；共享 schema/root config/接口只设一个 writer。
- **machine-dispatched**：交执行器时按随包 `references/task-packaging.md` 的完整 v2 示例、类型及 `refusal_handling` 校验；不依赖未分发的源仓 schema。
- 已批准计划交 `adk-planning-execution-loop`；不得降低风险对应的验证和授权。

## Workflow
1. 对照原验收；普通功能先做 tracer-bullet。公共契约无法独立落地时读 `references/vertical-slice-planning.md`，按 expand → migrate → contract 保留临时兼容、退出任务和最终集成，中间批次不代表整体通过。
2. 明确 `scope_read/scope_write/global_constraints/interfaces`、共享文件及权限。v2 将这些约束写入 `constraints` 字符串条目；worker 信封另存，同文件/shared contract 不并行写。
3. 依赖图无环；前置证据通过、写冲突解除、权限足够才进 Ready Frontier。`ready_to_handoff` 是调度判定，不是 v2 顶层字段；阻塞项不反复派发。
4. `work_item_kind` 与 `implementation_permission/exit_gate` 按 reference 校验；decision/research/prototype 禁止产品写入，prototype 附 `prototype_evidence`；只有已批准 implementation 可写，模型不能补造授权。
5. 人工计划只需任务、依赖、验收、风险和下一步。估时用历史或不确定范围，**不硬套 0.5–8h**，未知 `not-estimated`；仅资源决策需要时细化，只有独立且收益明确时建议并行。

## Spec-to-slice 追踪
- 已有 Canonical Change Contract 的非平凡功能，每个 Ready 任务绑定原始 `REQ-NNN/ACC-NNN`、可观察 delta、`VERIFY-NNN` 与失败反例；以一个端到端 tracer bullet 优先验证主要风险，不按文件层或 Agent 角色机械分包。
- 跨仓共享协议仅允许一个契约 writer；SoC、MCU 的实现可独立切片，但最后一项必须验证双方相同的 protocol/spec digest 与端到端故障路径。未具备设备/工具条件时标明 `not-tested`，不假关闭父验收。
- 批末对实际可观察行为做 code→spec 反向核对；没有行为变化时不强制生成 Delta Spec。不要派生第二套任务状态机。

## Quality Gate
- 每项有 owner、可执行 verify；未知路径/命令标待查。状态、权限和接口来自实际计划。
- 机器包拒绝缺字段、未知字段及错误类型/权限；未实际校验标未验证，不冒充 ready。
- 最终整合须验证；任务数量、估时或填表不证明成功。
