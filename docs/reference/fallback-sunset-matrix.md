# Fallback 下线矩阵

## 目标

本矩阵用于跟踪 Superpowers skill 在 adk-first 体系中的替代状态。原则是先补 adk 等价能力和验证证据，再把 Superpowers 从默认 fallback 降级为显式 fallback，最后按场景下线。

结构化源文件：`fallback-sunset-matrix.tsv`。人工说明以本文为主，门禁检查以 TSV 为准。

## 状态定义

| 状态 | 含义 |
|---|---|
| active-fallback | 仍保留默认 fallback |
| explicit-fallback | 仅用户点名、adk 不覆盖或迁移期对照时使用 |
| candidate-sunset | adk 等价能力、触发回归和 pilot 证据均已具备 |
| sunset | 默认不再路由到该 Superpowers skill |

## 下线准入

1. adk 有等价 primary skill 或 workflow。
2. `scripts/devkit.sh match --text` 能把 TSV 中 `match_text` 路由到 `adk_equivalent` 内的 skill。
3. `active-fallback` 必须有 owner、next_step 和未过期的 `review_by`。
4. `candidate-sunset` / `sunset` 必须引用 `evidence-ready` 或 `regression-ready` pilot。
5. `tests/run_all.sh` 和 `check-adk-harden-readiness.sh --require-pilot --skip-full-suite` 通过。
6. 通用 handoff 不产生重复 skill name 或 manifest 漂移。
7. 真实嵌入式全栈 pilot 至少覆盖一次该能力面。

## live_requirement 与评分阈值

`fallback-sunset-matrix.tsv` 的 `live_requirement` 用于区分运行态安装要求：

| live_requirement | 含义 |
|---|---|
| core-live-required | 期望运行时 skills 目录中的 `<skill>/SKILL.md` 已存在；缺失会记为 live gap |
| optional-live-allowed | optional skill 可只在 adk handoff/profile 中就绪；若已安装到运行时目录则记为 pass |
| handoff-ready-only | 只要求 adk 侧 handoff/profile 就绪，不要求当前运行目录已安装 |

replacement score 固定为 5 项：routing、profile、pilot、handoff、live。当前阈值：

| 状态 | 最低分 |
|---|---:|
| active-fallback | 3/5 |
| explicit-fallback | 3/5 |
| candidate-sunset | 4/5 |
| sunset | 5/5 |

阈值不满足时 `scripts/check-fallback-sunset.sh` 直接失败。planned pilot 不计 pilot 分，避免把待验证事项当作下线证据。

## 能力矩阵

| Superpowers Skill | adk 等价能力 | 当前状态 | 缺口 | 下一步 |
|---|---|---|---|---|
| using-superpowers | adk-runtime-router | explicit-fallback | 需要更多真实任务触发语料 | 扩充 prompt 回归 |
| brainstorming | adk-requirements-triage + adk-structured-requirements-questioning | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live 使用，无 fallback 需求则推进 sunset |
| writing-plans | adk-task-breakdown + adk-planning-execution-loop | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live 长任务计划使用 |
| executing-plans | adk-planning-execution-loop | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live 阶段执行使用 |
| test-driven-development | adk-test-strategy + adk-unit-test-embedded | explicit-fallback | 已有测试策略 evidence-ready，需要真实 C/C++/ctest/HIL 项目入口 | 接入真实项目测试入口 |
| systematic-debugging | adk-systematic-debugging | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live 调试使用 |
| requesting-code-review | adk-code-review-loop + adk-commit-pr-quality-gate | explicit-fallback | 已有 review evidence-ready，需要真实 diff/reviewer 反馈 | 绑定真实 review 样例 |
| receiving-code-review | adk-code-review-loop | explicit-fallback | 已有误报/越界反馈 evidence-ready，需要真实反馈样例 | 绑定真实反馈样例 |
| verification-before-completion | adk-verification-before-completion | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live completion 使用 |
| dispatching-parallel-agents | adk-parallel-agent-governance | explicit-fallback | 已有并行治理 evidence-ready，需要真实多 agent 写入复跑 | 绑定真实多 agent 写入样例 |
| subagent-driven-development | adk-parallel-agent-governance + adk-code-review-loop | explicit-fallback | 已有 scope/review/integration evidence-ready，需要真实平台子代理复跑 | 评估 candidate-sunset 前补真实多 agent 复审 |
| using-git-worktrees | adk-worktree-governance | explicit-fallback | worktree 创建清理和 PR 场景仍需真实 git 样例 | 补真实 worktree pilot |
| finishing-a-development-branch | adk-branch-closeout | explicit-fallback | 已有 closeout evidence-ready，远端 PR 操作仍需人工确认 | 绑定真实分支 closeout |
| writing-skills | skill-creator + adk-skill-composition-governance | candidate-sunset | routing/profile/pilot/handoff/live 均已就绪 | 观察一轮 live skill 生命周期使用 |

## 维护规则

- 每次新增 adk 等价能力后，同步更新本矩阵。
- 每次修改本文状态后，同步更新 `fallback-sunset-matrix.tsv` 并运行 `scripts/check-fallback-sunset.sh`。
- `scripts/check-fallback-sunset.sh` 会输出 replacement score，包含 routing、profile、pilot、handoff、live health 五项。
- 需要归档评分明细时使用 `scripts/check-fallback-sunset.sh --score-tsv <path>`；需要候选队列时使用 `--candidate-tsv <path>`；需要低 token 摘要时使用 `--summary-json`。
- Pilot 证据成熟度单独用 `scripts/pilot-readiness.sh` 检查；需要低 token 摘要时使用 `scripts/pilot-readiness.sh --summary-json`。
- Pilot index 与 evidence 文件必须同步：`status:` 行必须与 `docs/pilots/index.tsv` 一致，planned pilot 必须有待补证据，ready pilot 必须有验证证据；`workflow_readiness`、`artifact_readiness`、`device_readiness` 用于区分流程证据、制品证据和设备侧 readiness；`device_readiness=simulated-pass` 只代表模拟设备闭环，不代表真实硬件放行。
- 状态不能从 `active-fallback` 直接跳到 `sunset`，必须经过 `explicit-fallback` 或 `candidate-sunset`。
- 若真实任务中出现漏匹配、过重流程或验证缺口，状态降级并补回归样例。
- 下线不是删除上游资产，而是从默认路由中移除；用户点名仍可使用。
