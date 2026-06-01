# Review Report: workflow-agent-contract-standardization

## Verdict
PASS

## Findings
| Severity | Finding | Status |
|---|---|---|
| blocker | 无 | closed |
| major | 无 | closed |
| minor | 上下文压力较高，后续应新开线程继续 | accepted |

## Release Decision
可提交本仓 source 改动；2026-06-01 已完成 live runtime apply 与小场景试跑。

## Runtime Closeout: 2026-06-01

### Baseline
- Source baseline: `agent-dev-kit` commit `777f54f` (`feat(workflow): 规范化 agent 和 workflow 契约`)
- Runtime source: `~/codex` commit `20f529d` (`docs(codex): 收敛 adk 通用边界表述`)
- Apply plan: `~/codex/build/apply-plan.json`, generated at `2026-06-01T20:25:21+08:00`

### Apply Result
| Command | Result |
|---|---|
| `rtk bash ~/codex/scripts/apply.sh --plan ~/codex/build/apply-plan.json` | PASS: `copy=0 keep=422 overwrite=0 delete=0 mkdir=229 skip=0`, `dry_run=0` |
| `rtk bash ~/codex/scripts/check-routing-precedence.sh` | PASS: default profile `team-collab`, active Superpowers in default profile `0` |
| `rtk bash ~/codex/scripts/check.sh` | PASS: build/governance/live checks, 65 tests, profile smoke checks and live drift check all passed |

### Runtime Scenario Trial
- Scenario: skill 候选归属判断，验证 `skill-curation-delivery` 是否能从候选筛选意图落到可审查契约。
- Candidate sample: `adk-test-flakiness-triage` remains an optional skill; trigger `"测试波动"` is visible in manifest and catalog.
- Routed workflow: `skill-curation-delivery`.
- Primary agent/skill from matrix: `requirements-analyst` / `adk-requirements-triage`.
- Supporting skills from matrix: `adk-task-breakdown`, `adk-commit-pr-quality-gate`, `adk-verification-before-completion`.
- Verification commands: `rtk bash tests/test_catalog.sh` and `rtk bash tests/test_skill_sop_quality.sh`, both PASS.

### Review Decision
- Trigger accuracy: PASS. `技能候选筛选` maps to `skill-curation-delivery`; `测试波动` maps to the optional skill itself rather than the curation workflow.
- Matrix adequacy: PASS. `docs/workflow-contract-matrix.md` exposes workflow, profile, command risk, primary agent, primary skill, supporting skills and verification commands.
- `command_risk`: keep `low`; this workflow is catalog/review oriented and the required verification commands are non-destructive.
- Profile boundary: keep `core, team-core`; no evidence supports moving this workflow into broader runtime profiles.

## Asset Naming Hard Cutover: 2026-06-01

### Scope
- Hard-cut historical role-style assets without compatibility aliases.
- Keep Agent names role-oriented and Skill names capability-oriented.
- Remove redundant planning/generation/evaluation stage assets and route those responsibilities to existing stable roles.

### Result
- Agent count changed from `16` to `12`.
- Core Skill count changed from `56` to `53`.
- Domain roles retained as `bsp-analyst` and `hardware-debugger`.
- Domain capabilities retained as `adk-bsp-analysis`, `adk-driver-implementation` and `adk-hardware-debugging`.
- Driver implementation accountability is owned by `driver-engineer`.
- Planning, implementation and evaluation are owned by existing role families instead of legacy stage-role assets.

### Verification
| Command | Result |
|---|---|
| `rtk bash scripts/devkit.sh validate --strict --summary-json` | PASS: `agents=12`, `skills=53`, `optional_skills=9`, `profiles=9`, `workflows=6` |
| `rtk bash tests/test_catalog.sh` | PASS |
| `rtk bash tests/test_workflow_contract.sh` | PASS |
| `rtk bash tests/test_skill_trigger_matrix.sh` | PASS |
| removed historical ID residual scan | PASS: no matches |
| `rtk bash tests/run_all.sh` | PASS: `tests=40 pass=40 fail=0` |

## Profile Closure Hardening: 2026-06-01

### Scope
- Treat Agent `default_skills` as runtime availability contract, not a loose recommendation.
- Require resolved profile Skill sets to include every resolved Agent's `default_skills`.
- Treat scalar `extends: <profile>` and list-style `extends` consistently.
- Keep child profiles incremental: do not redeclare inherited Agents or Skills.

### Result
- `core` now includes default Skills required by its Agents: `adk-adr-writer`, `adk-component-api-stability`, `adk-driver-implementation` and `adk-driver-bringup-checklist`.
- Child profiles now declare only incremental Agent/Skill additions relative to their parent profile.
- `release-hardening`, `incident-response` and `research-intake` now include their standalone Agents' default Skills.
- `scripts/check-profile-coherence.sh` now fails on default Skill closure gaps and scalar/list `extends` redeclarations.

### Verification
| Command | Result |
|---|---|
| `rtk bash scripts/check-profile-coherence.sh` | PASS |
| `rtk bash tests/test_profile_coherence.sh` | PASS |
| `rtk bash tests/test_profile_coherence_enhanced.sh` | PASS |
| `rtk bash tests/test_catalog.sh` | PASS |
| `rtk bash tests/test_workflow_contract.sh` | PASS |
