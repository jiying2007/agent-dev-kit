# Runtime Routing Runbook

## 目标

把 adk 能力先统一路由到 `~/codex` 的 profile/skill/agent/workflow 声明，再由 `~/codex` apply 到 `~/.codex`，避免多套生态混装后的触发冲突。

## 默认入口

- 只读分析：不创建 change，输出结论与证据路径。
- 任务启动：先用 `adk-runtime-router` 输出 primary/supporting/fallback 裁决。
- 行为变更：进入 `propose -> apply -> verify -> review`。
- 高风险变更：使用核心 `adk-artifact-gating`，不再叠加 lite optional skill。
- 测试策略：使用 `adk-test-strategy` 判定 Level 0/1/2 与 TDD 需求。
- 独立代码审查：使用 `adk-code-review-loop`，再交给提交/PR 门禁。
- 并行子代理：使用 `adk-parallel-agent-governance` 判定准入、冲突矩阵和整合验证。
- worktree 隔离：使用 `adk-worktree-governance`，删除或清理前必须确认。
- 分支收尾：使用 `adk-branch-closeout`，先验证再选择合并、PR、保留或丢弃。
- 长任务：叠加 `adk-planning-execution-loop`。
- 团队交接：叠加 `adk-cross-team-handoff`。
- 上游吸收：使用 `research-intake` profile。

## Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## Skill 组合

- `adk-runtime-router` 只负责路由裁决，不替代具体执行 skill。
- 主技能只能有一个。
- 支撑技能只补充检查项，不抢占触发入口。
- fallback 必须显式声明，禁止多个技能同时争抢同一任务。
- 场景文档中的 Skill 列表统一按 `Primary -> Supporting` 排列。
- profile 只声明增量能力；若已通过 `extends` 继承，不得重复声明同名 Agent/Skill。

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill adk-runtime-router --text "开始任务前判断使用哪个技能"
bash scripts/devkit.sh match --skill adk-requirements-triage --text "<task>"
bash scripts/devkit.sh match --skill adk-test-strategy --text "这个功能需要先写测试"
bash scripts/devkit.sh match --skill adk-branch-closeout --text "开发完成，准备创建 PR"
bash scripts/check-profile-coherence.sh
bash scripts/check-fallback-sunset.sh
bash scripts/check-fallback-sunset.sh --score-tsv /tmp/adk-replacement-score.tsv
bash scripts/pilot-readiness.sh --summary-json
bash ~/codex/scripts/doctor.sh --scope governance
bash ../scripts/check-runtime-routing.sh ..
```

## 验收门禁

- `check-runtime-routing.sh` 通过。
- `check-fallback-sunset.sh` 通过。
- `pilot-readiness.sh --summary-json` 通过，且 `candidate-sunset` / `sunset` 不引用 planned pilot。
- 若要保留替代度证据，附上 `--score-tsv` 输出路径。
- `check-skill-routing-conflicts.sh` 通过。
- `check-profile-coherence.sh` 通过。
- `adk-runtime-router` 至少有一个自然语言触发回归样例。
- `~/codex` governance/build 关系通过。
- 任务场景能映射到 profile、Agent 链、主 Skill 和 Workflow 状态。
