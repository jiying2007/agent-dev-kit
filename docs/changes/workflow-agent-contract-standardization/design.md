# Design: workflow-agent-contract-standardization

## 目标
将 Agent 和 Workflow 的职责边界提升为 manifest 可校验 contract，并生成可审查矩阵。

## 设计决策
- Workflow 一等资产路径固定为 `workflows/<name>/WORKFLOW.md`。
- Workflow manifest 必须声明 `profiles`、`command_risk`、`primary_agent`、`primary_skill`、`supporting_skills`、`commands`、`verification`。
- Agent manifest 必须声明 `owns`、`does_not_own`、`handoff_to`、`default_skills`、`quality_gate`。
- `catalog-assets.sh build` 输出 `Agent Contract Matrix` 与 `Workflow Matrix`，默认同步生成 `docs/workflow-contract-matrix.md`。

## 验证设计
- `validate-assets.sh --strict` 校验字段存在、引用闭包、command risk 枚举和仓内命令路径。
- `check-workflow-closure.sh` 按 workflow `profiles` 过滤适用范围。
- `test_workflow_contract.sh` 固定 workflow 数量和 profile 闭包预期。

## 回退设计
可回退 manifest 新字段、`workflows/` 目录、catalog 矩阵和新增 strict 校验；回退后继续使用旧的 `docs/workflows.md` 说明路径。
