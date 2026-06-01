# Proposal: workflow-agent-contract-standardization

## 问题陈述（单问题）
Agent 与 Workflow 已具备基础资产结构，但 Workflow 不是完整一等契约，Agent 的 manifest contract 也缺少 ownership、handoff、默认 skill 与 quality gate 字段，导致审查时难以机器校验职责边界和 profile 闭包。

## 上下文充分性检查
- 已确认现有 `manifest.yaml` 是 Agent、Skill、Profile、Workflow 的单一事实源。
- 已确认 `validate-assets.sh --strict` 是结构门禁入口。
- 已确认 `catalog-assets.sh build` 是能力索引生成入口。

## Core/Optional 边界检查
本次只治理 ADK core 的 Agent/Workflow 契约，不新增 optional skill，不启用外部工具，不写入 live runtime。

## 变更重复性检查
现有 `docs/workflows.md` 有场景说明，但缺少 `workflows/<name>/WORKFLOW.md` 一等资产和机器校验；本次是将说明提升为可校验契约，不重复已有 Skill SOP。

## Breaking Change 检查
对资产校验更严格，属于治理门禁增强。现有 16 个 Agent、56 个 core Skill、9 个 optional Skill、9 个 Profile 均已通过新 strict 校验。

## Spec 链路检查
- Requirements: Agent/Workflow 契约必须可审查、可闭包、可验证。
- Design: manifest 记录索引和引用闭包，`WORKFLOW.md` 记录阶段和工件契约。
- Tasks: 更新 manifest、脚本、文档、测试和生成目录。

## 安装范围与依赖边界
安装范围保持仓内 source 资产；source-to-live 只执行 dry-run 验证，不直接 apply 到 `~/.codex`。

## Prompt 回归证据计划
通过 `test_skill_trigger_matrix.sh`、`test_match_effectiveness.sh`、`test_workflow_contract.sh` 和全量 `tests/run_all.sh --fail-fast` 验证路由、契约和文档一致性。

## 收敛模式与退出条件
退出条件为 strict validate 通过、workflow contract 测试通过、全量回归通过、source-to-live dry-run 通过或明确记录阻塞。
