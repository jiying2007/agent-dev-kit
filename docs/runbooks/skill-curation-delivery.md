# Skill Curation Delivery Runbook

## 适用场景

- 需要从候选技能池中筛选、吸收并落地到当前工程能力目录。
- 需要明确技能是 `global-ready` 还是 `project-bound`，避免错误并入 core。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `task-breakdown`
- `commit-pr-quality-gate`
- `verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill requirements-triage --text "<候选技能描述>"
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 每个候选技能必须给出归属结论：`core` / `optional` / `reject`。
- 必须声明安装范围：`global-ready` 或 `project-bound`。
- 必须记录依赖边界：是否依赖项目内脚本、数据目录或私有上下文。

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
