# Runtime Routing Runbook

## 目标

把 `~/.codex` 中的任务入口统一路由到合适的 Agent、Skill、Workflow，避免多套生态混装后的触发冲突。

## 默认入口

- 只读分析：不创建 change，输出结论与证据路径。
- 行为变更：进入 `propose -> apply -> verify -> review`。
- 高风险变更：叠加 `adk-artifact-gated-lite`。
- 长任务：叠加 `adk-planning-execution-loop`。
- 团队交接：叠加 `adk-cross-team-handoff`。
- 上游吸收：使用 `research-intake` profile。

## Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## Skill 组合

- 主技能只能有一个。
- 支撑技能只补充检查项，不抢占触发入口。
- fallback 必须显式声明，禁止多个技能同时争抢同一任务。
- 场景文档中的 Skill 列表统一按 `Primary -> Supporting` 排列。
- profile 只声明增量能力；若已通过 `extends` 继承，不得重复声明同名 Agent/Skill。

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill adk-requirements-triage --text "<task>"
bash scripts/check_profile_coherence.sh
bash ../scripts/check-runtime-routing.sh ..
```

## 验收门禁

- `check-runtime-routing.sh` 通过。
- `check-skill-routing-conflicts.sh` 通过。
- `check_profile_coherence.sh` 通过。
- 任务场景能映射到 profile、Agent 链、主 Skill 和 Workflow 状态。
