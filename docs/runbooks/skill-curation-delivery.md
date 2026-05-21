# Skill Curation Delivery Runbook

## 适用场景

- 需要从候选技能池中筛选、吸收并落地到当前工程能力目录。
- 需要明确技能是 `global-ready` 还是 `project-bound`，避免错误并入 core。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-commit-pr-quality-gate`
- `adk-verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill adk-requirements-triage --text "<候选技能描述>"
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 每个候选技能必须给出归属结论：`core` / `optional` / `reject`。
- 必须声明安装范围：`global-ready` 或 `project-bound`。
- 必须记录依赖边界：是否依赖项目内脚本、数据目录或私有上下文。
- 候选技能文档推荐使用结构化章节：`what-to-do` 与 `supporting-info`，降低路由歧义与冗余解释成本。

## Skill 结构契约（推荐）

- `what-to-do`：只写行动步骤、输入输出和完成判据。
- `supporting-info`：集中放约束、背景、反例与兼容说明。
- 两类信息分区后，优先让路由和执行读取 `what-to-do`，减少上下文开销。

## 候选筛选模板

```md
- Candidate Skill:
- Install Scope (global-ready/project-bound):
- Core/Optional Decision:
- Dependency Boundary:
- Routing Triggers:
- Evidence:
```

## 验收门禁

- `proposal.md` 必须包含归属决策与安装范围。
- 触发词路由必须可解释，且不与现有核心技能冲突。
- 缺少依赖边界声明或归属结论时，结论固定为 `needs-fix`。
