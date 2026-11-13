---
name: adk-task-breakdown
description: "用于复杂需求拆解任务包、依赖关系及并行边界；单点小修无需拆包，也不用于替代已批准计划的持续执行。"
version: 1.5.0
last_updated: 2026-11-13
triggers:
  - "拆解任务"
  - "任务拆分"
  - "任务太大"
non_triggers:
  - 单点微调任务
  - 单文件小修且无共享依赖变更
inputs:
  - 需求范围、里程碑、模块边界与依赖关系
outputs:
  - 任务清单、依赖图、优先级、ownership 与冲突矩阵
constraints:
  - 每个任务必须可独立验证
  - 默认禁止两个任务并行修改同一 shared contract/schema
  - 机器消费的任务包必须声明 structured_output_schema 和 strict_schema_decision
  - 任务包只接受 adk-task-package-schema-v2，work_item_kind 与 implementation_permission 必须满足跨字段规则
---

# adk-task-breakdown

## Goal
只为**确实需要拆分的复杂任务**生成可执行、可验收的任务边界。小修或已有可用任务包时直接退出，不为了并行和模板制造更多工作。

## Choose the smallest useful plan
- **single-slice**：目标已明确、无跨模块资源冲突，直接给一个能产生可观测结果的纵向切片；不为单人小任务强制拆包、估时、并行分工。
- **multi-slice**：确有多个独立交付，按依赖拆分，每项有真实产物与验证；共享 schema/root config/接口由唯一 owner 负责。
- **machine-dispatched**：只有要交接给执行器/并行子代理时使用完整 `adk-task-package-schema-v2`；需要 `structured_output_schema`、`strict_schema_decision`、`refusal_handling` 与 v2 跨字段检查。
- 风险升高不能降低验证、授权和整合边界。计划已批准且只需执行时退出，交 `adk-planning-execution-loop`。

## Workflow
1. 对照需求、原验收和现有计划，只修真正的矛盾或阻塞，不重复规划已完成部分；优先确定当前可关闭的一条 tracer-bullet 纵向切片。按需读 `references/vertical-slice-planning.md`。
2. 划清 `scope_read`、`scope_write`、`global_constraints`、`interfaces`、共享文件和数据/权限边界；同文件及 shared contract 不允许并行写入。
3. 多项任务形成无环依赖图，只有**前置证据已通过、写冲突已解除且权限足够**的项才进入 Ready Frontier；阻塞项记录原因，不反复派发。
4. 人工阅读计划只需任务、依赖、真实验收、风险及下一步，不强制填写 v2 机器字段；机器交接的 `work_item_kind`、`question_to_resolve`、`evidence_required`、`implementation_permission`、`exit_gate`、`handoff_target`、`retention_decision` 必须按 schema 严格约束。
5. `decision/research/prototype` 不能凭任务包擅自执行产品代码；只有受批准的 `implementation` 才可写。prototype 要有 `prototype_evidence`，授权不能由模型推断或后补。
6. 估时使用已有历史观测或不确定范围，**不硬套 0.5–8h 粒度和逐项三点估时**；仅当排期/资源决策真正依赖估时时细化，未知标 `not-estimated`。
7. 有独立且值得并行的任务才给并行建议；否则直接单线程执行。大量任务、复杂交接及估时示例按需读 `references/task-packaging.md`。

## Quality Gate
- 每个实际拆出的交付有可验证完成条件和 owner；项目尚未提供的文件路径或命令不能编造。
- 任务状态、权限和接口约束源于真实计划；v2 输出、冲突规则、`ready_to_handoff` 与最终整合验证在机器调度时不可省略。
- 不用任务数量、工时区间或任务包填写完整度充当目标成功；小任务不得为复盘、估时或并行新增无效模型调用。
