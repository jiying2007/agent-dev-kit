# Prompt Evolution Delivery Runbook

## 适用场景

- 变更以提示词、流程文本、策略文案为主。
- 需要证明“文本变更”确实改善行为，而不是只改描述。

## 推荐 Agent 链

`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<prompt 演进目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 变更前必须保存 baseline prompt snapshot。
- 至少保留一组“同输入对比”证据（before/after）。
- 失败样例必须入档，禁止只展示成功样例。
- 关键验证命令必须入命令级 Evidence Index（命令/退出码/结果摘要/证据路径/层级）。
- 工程任务提示必须像工单一样约束行为，默认包含背景、目标、范围、约束、验证和输出六项；缺少范围或验证时先补齐，不直接执行。
- 模板沉淀必须服务稳定任务类型，如 bug 修复、代码审查、测试补全、小步重构、前端实现或项目理解；一次性需求不升级为长期模板。
- 工程任务卡必须声明单一 `primary_action` 和 `action_mode`。`action_mode` 至少区分 `analyze_only`、`implement`、`verify`、`review`、`handoff`；多目标任务先拆分或升级为阶段计划，不在一个 prompt 中混写分析、实现、测试、文档和发布。
- 长任务必须声明 checkpoint 与 stop-on-failure 条件。每个 checkpoint 应说明已改范围、验证命令、下一步和失败时是否停止；若局部验证失败，先停下报告，不继续扩大改动范围。

## Prompt 回归模板

```md
- Prompt Baseline:
- Prompt Update:
- Test Inputs:
- Before/After Diff:
- Failure Cases:
- Evidence Index (command/exit_code/result_summary/evidence_path/layer):
- Final Decision:
```

## 工程任务卡模板

```md
- Background:
- Goal:
- Primary Action:
- Action Mode:
- Scope:
  - Prefer:
  - Must not touch:
- Constraints:
- Checkpoints:
- Stop On Failure:
- Verification:
- Output:
- Escalation:
```

任务卡只负责把本次任务说清楚，不替代项目级 `AGENTS.md`、runbook 或测试门禁。若任务涉及公共 API、schema、迁移、安全、发布、生产配置或新增依赖，必须在 `Escalation` 中声明人工确认点。

## Prompt 分层契约

Prompt 变更必须先说明作用层级，避免把长期规则、示例和当前任务混写：

| 层级 | 用途 | 写入位置 |
|---|---|---|
| System / project rule | 角色、不可违背约束、长期输出格式、安全边界 | `AGENTS.md`、runbook、Skill |
| Few-shot / example | 给稳定任务提供输入输出样例 | `references/`、模板、测试夹具 |
| User task | 本次目标、范围、验证、输出要求 | 任务卡或会话输入 |
| Retrieved knowledge | 项目地图、文档片段、证据摘要 | 上下文包，必须保留来源 |

设计规则：

- 角色设定必须服务任务边界，不写泛化身份口号。
- 规则约束同时写“必须做”和“禁止做”，并给出验证方式。
- 输出格式若进入下游程序，必须有 schema 或结构校验。
- Few-shot 样例只能覆盖稳定模式；过时样例要归档或设置复核时间。
- 知识注入优先引用项目地图和 runbook，不把大段背景永久塞进 prompt。

## 验收门禁

- `verify-report` 必须包含 prompt 回归证据（含至少一条失败样例）与命令级 Evidence Index。
- 若只改文本且无行为对比证据，结论固定为 `needs-fix`。
