---
name: skill-curation-delivery
description: 技能候选筛选、core/optional 归属和触发质量验证工作流
version: 1.0.0
last_updated: 2026-06-01
primary_agent: requirements-analyst
primary_skill: adk-requirements-triage
triggers:
  - "技能候选筛选"
  - "skill curation"
  - "core optional 归属"
profiles:
  - core
  - team-core
command_risk: low
stages:
  - intake
  - classify
  - contract
  - verify
  - review
artifacts:
  - intake-summary.md
  - trigger-matrix.md
  - verify-report.md
  - review-report.md
verification:
  - "rtk bash tests/test_catalog.sh"
  - "rtk bash tests/test_skill_sop_quality.sh"
failure_handling:
  - "无法证明复用价值时保持候选或拒绝"
  - "触发边界冲突时先修 description 和 non_triggers"
---

# skill-curation-delivery

## Goal
- 把候选 Skill 转为可路由、可验证、可维护的 core 或 optional 资产决策。
- 防止重复能力、触发冲突和未审查外部依赖进入生产 profile。

## Scope
- 适用于新增、吸收、合并或降级 Skill 的筛选流程。
- 不负责直接安装第三方 Skill；外部来源必须先经过供应链审查。

## Ownership
- Primary agent: `requirements-analyst`
- Primary skill: `adk-requirements-triage`
- Supporting skills: `adk-task-breakdown`, `adk-commit-pr-quality-gate`, `adk-verification-before-completion`

## Stage Contract
1. `intake`: 固定来源、用途、依赖、许可证和安全边界。
2. `classify`: 判定 core / optional / reject，并说明 profile 影响。
3. `contract`: 补齐 description、triggers、non_triggers、inputs、outputs、constraints。
4. `verify`: 跑 catalog、validate、trigger matrix 和 SOP 质量检查。
5. `review`: 审查重复能力、触发边界和回滚路径。

## Artifact Contract
- `intake-summary.md` 记录来源、授权、依赖和风险。
- `trigger-matrix.md` 记录主触发、非触发、fallback 和冲突项。
- `verify-report.md` 必须包含 catalog 与 strict validate 结果。

## Commands
```bash
rtk bash scripts/devkit.sh catalog build
rtk bash scripts/devkit.sh validate --strict
```

## Failure Handling
- 与现有 Skill 重叠时默认 merge，不新增资产。
- 无法声明权限边界或验证命令时不得进入 core。
- 触发质量不足时先改 description/triggers/non_triggers。

## Quality Gate
- 每个晋级 Skill 必须有唯一可辨识 description 和明确非触发条件。
- core/optional/reject 结论必须可复查。
