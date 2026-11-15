---
name: adk-task-breakdown
description: "用于复杂需求拆解、公共契约迁移拆分及并行边界；单点小修无需拆包，也不替代已批准计划的持续执行。"
version: 1.5.0
last_updated: 2026-11-13
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
  - 任务清单、依赖图、优先级、ownership 与冲突矩阵
constraints:
  - 每个任务须有可执行验证，批次结果不等于最终集成通过
  - 默认禁止两个任务并行修改同一 shared contract/schema
  - 机器消费的任务包必须声明 structured_output_schema 和 strict_schema_decision
  - 任务包只接受 adk-task-package-schema-v2，work_item_kind 与 implementation_permission 必须满足跨字段规则
---

# adk-task-breakdown

## Goal
仅为复杂任务生成可执行、可验收的边界；小修或已有可用任务包时直接退出。

## Choose the smallest useful plan
- **single-slice**：目标明确且无跨模块资源冲突时给可观测的纵向切片；小任务不强制拆包、估时或并行。
- **multi-slice**：确有多个独立交付，按依赖拆分，每项有真实产物与验证；共享 schema/root config/接口由唯一 owner 负责。
- **machine-dispatched**：只有要交接给执行器/并行子代理时使用完整 `adk-task-package-schema-v2`；需要 `structured_output_schema`、`strict_schema_decision`、`refusal_handling` 与 v2 跨字段检查。
- 风险升高不能降低验证、授权和整合边界。计划已批准且只需执行时退出，交 `adk-planning-execution-loop`。

## Workflow
1. 对照原验收和计划，只修真实阻塞；普通功能优先 tracer-bullet 纵向切片。跨公共契约重构无法独立落地时，按 `references/vertical-slice-planning.md` 的 expand → migrate → contract 明确临时兼容、退出任务和最终集成，不能把中间批次当整体通过。
2. 划清 `scope_read`、`scope_write`、`global_constraints`、`interfaces`、共享文件和数据/权限边界；同文件及 shared contract 不允许并行写入。
3. 多项任务形成无环依赖图，只有**前置证据已通过、写冲突已解除且权限足够**的项才进入 Ready Frontier；阻塞项记录原因，不反复派发。
4. 人工阅读计划只需任务、依赖、真实验收、风险及下一步，不强制填写 v2 机器字段；机器交接的 `work_item_kind`、`question_to_resolve`、`evidence_required`、`implementation_permission`、`exit_gate`、`handoff_target`、`retention_decision` 必须按 schema 严格约束。
5. `decision/research/prototype` 不能凭任务包擅自执行产品代码；只有受批准的 `implementation` 才可写。prototype 要有 `prototype_evidence`，授权不能由模型推断或后补。
6. 估时用历史观测或不确定范围，**不硬套 0.5–8h 粒度和逐项三点估时**；只在排期/资源决策需要时细化，未知标 `not-estimated`。
7. 仅独立且值得并行时给并行建议，否则单线程。复杂交接/估时按需读 `references/task-packaging.md`。

## Quality Gate
- 每个拆出的交付须有可验证完成条件和 owner；不编造未经核实的路径或命令。
- 任务状态、权限和接口约束源于真实计划；v2 输出、冲突规则、`ready_to_handoff` 与最终整合验证在机器调度时不可省略。
- 任务数量、工时或填表不证明成功；小任务不为复盘/估时/并行新增无效模型调用。
