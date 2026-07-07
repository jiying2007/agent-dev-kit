---
name: runtime-routing
description: 运行时技能路由、fallback 边界和 profile 闭包验证工作流
version: 1.1.0
last_updated: 2026-07-07
primary_agent: architecture-planner
primary_skill: adk-runtime-router
triggers:
  - "运行时路由"
  - "技能路由"
  - "runtime routing"
profiles:
  - core
  - embedded-fullstack
command_risk: low
stages:
  - inventory
  - route-design
  - runtime-control-plane-audit
  - closure-check
  - verify
  - review
artifacts:
  - route-decision.md
  - runtime-control-plane-audit.md
  - profile-closure.md
  - verify-report.md
  - review-report.md
verification:
  - "rtk bash tests/test_skill_trigger_matrix.sh"
  - "rtk bash tests/test_workflow_closure.sh"
failure_handling:
  - "多个 primary skill 争抢时必须先拆触发边界"
  - "profile 闭包失败时先修 manifest 再发布"
---

# runtime-routing

## Goal
- 固定任务意图到 primary/supporting/fallback Skill 的路由关系。
- 验证 Workflow、Profile、Agent 和 Skill 闭包一致。

## Scope
- 适用于 core 和 embedded-fullstack 的运行时路由、触发词调整和 fallback 下线。
- 不直接授予工具权限或绕过 tool policy。
- slash command、MCP/tool server、hook、permission profile、approval policy 和 sandbox 只作为控制面审计对象；启用或放宽权限必须另走安全/供应链和完成前验证。

## Ownership
- Primary agent: `architecture-planner`
- Primary skill: `adk-runtime-router`
- Supporting skills: `adk-verification-before-completion`, `adk-repo-drift-remediation`

## Stage Contract
1. `inventory`: 列出候选 Agent、Skill、Workflow 和 profile。
2. `route-design`: 判定 primary、supporting、fallback 和跳过条件。
3. `runtime-control-plane-audit`: 若路由变更触及 slash/MCP/hook/permission/sandbox，记录 `slash_command_runtime_audit`、`mcp_runtime_contract`、`permission_profile_decision`、`approval_boundary`、`deny_path_test`、`loaded_tools` 和 rollback；默认不得放宽权限。
4. `closure-check`: 验证所选 profile 能导出全部引用。
5. `verify`: 运行触发矩阵、workflow closure 和 routing 相关测试。
6. `review`: 审查冲突、遗漏、fallback 风险和文档同步。

## Artifact Contract
- `route-decision.md` 记录触发、非触发和 primary 选择依据。
- `runtime-control-plane-audit.md` 记录 slash/MCP/permission 控制面影响、deny-path、approval boundary、runtime config diff 和回滚。
- `profile-closure.md` 记录导出 profile、缺失引用和修复动作。
- `verify-report.md` 记录 matching、closure 和回归结果。

## Commands
```bash
rtk bash scripts/devkit.sh match --skill adk-runtime-router --text "技能路由"
rtk bash scripts/check-workflow-closure.sh --profile core
```

## Failure Handling
- 路由冲突时先调整 description/triggers/non_triggers，不把完整流程塞进全局规则。
- fallback 下线缺少 pilot 证据时保持兼容状态。
- profile closure 失败时禁止导出运行态资产。

## Quality Gate
- 一个场景只能有一个 primary skill。
- Workflow 引用必须能在声明 profile 中闭包通过。
- 运行控制面影响必须有 audit artifact；缺少 deny-path、approval boundary、loaded_tools 或 rollback 时不得发布运行态路由。
