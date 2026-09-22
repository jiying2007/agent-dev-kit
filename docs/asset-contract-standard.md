# Asset Contract Standard

## Goal

`agent-dev-kit` assets must keep Agent, Skill and Workflow boundaries explicit:

- Agent names describe accountable roles.
- Skill names describe reusable capabilities.
- Workflow names describe delivery or governance processes.
- Historical role-style assets are hard-cut over; no compatibility aliases are kept.

## Naming Rules

### Agents

- Use kebab-case role names without the `adk-` prefix.
- Prefer `<domain>-<role>` or `<responsibility>-<role>`.
- Agent names must not duplicate Skill names.
- Agents own decisions, handoff boundaries and review responsibility; they do not encode reusable procedures.

Examples:

- `requirements-analyst`
- `architecture-planner`
- `driver-engineer`
- `bsp-analyst`
- `hardware-debugger`
- `code-review-governor`

### Skills

- Use the `adk-` prefix for ADK-managed capability assets.
- Skill names describe actions, methods or governance capabilities, not people.
- Avoid role nouns such as `planner`, `generator`, `evaluator`, `developer`, `analyst` unless they are part of a domain term and cannot be expressed as an action.
- Prefer capability nouns such as `triage`, `analysis`, `review`, `governance`, `verification`, `planning`, `questioning`, `implementation` and `orchestration`.
- Avoid tool-like suffixes such as `*-analyzer` when the asset is a reusable method; use `*-analysis` instead.
- Avoid colloquial or metaphorical names; use the operational capability name that a reviewer can map to triggers and evidence.
- Avoid variant suffixes such as `*-lite`, `*-full`, `*-simple` and `*-advanced`. If a capability has different weight, encode it as the capability itself, profile membership, or workflow choice.
- New Skill proposals must include a naming risk check: role noun, tool suffix, colloquial wording, variant suffix, overlap with existing Skill, and profile boundary.

Examples:

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-bsp-analysis`
- `adk-driver-implementation`
- `adk-hardware-debugging`
- `adk-verification-before-completion`
- `adk-lightweight-planning`
- `adk-repo-prompt-analysis`
- `adk-skill-deep-analysis`
- `adk-structured-requirements-questioning`

### Workflows

- Use kebab-case process names.
- Prefer stable suffixes by intent:
  - `*-delivery` for implementation delivery.
  - `*-gate` for release or completion gates.
  - `*-routing` for runtime or selection logic.
  - `*-hardening` for release readiness and risk reduction.
  - `*-curation` for screening and ownership decisions.
- Each Workflow must declare `workflow_type`, `lifecycle_order`, `entry_conditions`, `exit_evidence`, `primary_agent`, `primary_skill`, `supporting_skills`, `command_risk`, `profiles` and verification commands.

## Boundary Rules

| Asset | Owns | Must Not Own |
|---|---|---|
| Agent | accountability, decisions, handoff, quality gate | reusable procedural steps that belong in a Skill |
| Skill | repeatable method, evidence template, command guidance, quality gate | role ownership or final release authority |
| Workflow | stage order, artifacts, routing, verification sequence | detailed implementation instructions already owned by a Skill |

## Profile Closure Rules

- A profile may declare only the incremental Agents and Skills it adds beyond its parent profile.
- Scalar `extends: <profile>` and list-style `extends` are both treated as inheritance.
- A child profile must not redeclare inherited Agents or Skills.
- After inheritance is resolved, every included Agent's `default_skills` must also be present in the resolved profile Skill set.
- If a Skill is only a recommendation and does not need runtime availability, it must not be listed under `default_skills`.

## Hard Cutover Decisions

Historical role-style assets are removed from live source, not aliased:

- BSP analysis is represented by Agent `bsp-analyst` and Skill `adk-bsp-analysis`.
- Hardware debugging is represented by Agent `hardware-debugger` and Skill `adk-hardware-debugging`.
- Driver implementation accountability belongs to Agent `driver-engineer`; reusable driver implementation method belongs to Skill `adk-driver-implementation`.
- Planning responsibilities belong to `requirements-analyst` and `architecture-planner`, with `adk-task-breakdown` and `adk-interface-contract-design` as reusable Skills.
- Implementation responsibilities belong to `driver-engineer`, `component-engineer` and `application-engineer`.
- Evaluation responsibilities belong to `test-validation-engineer` and `code-review-governor`, with `adk-code-review-loop` and `adk-verification-before-completion` as reusable Skills.

## Validation Expectations

- `rtk bash scripts/devkit.sh validate --strict`
- `rtk bash env PYTHONPATH=src python3 -m agent_dev_kit.profile_coherence_contract --root .`
- `rtk bash scripts/devkit.sh asset-taxonomy`
- `rtk bash tests/test_catalog.sh`
- `rtk bash tests/test_workflow_contract.sh`
- Residual scans for removed historical IDs must return no matches after cutover.

## Taxonomy and Routing Contract

每个 live Skill 和 Optional Skill 必须在 `manifest.json` 声明 `category`、`lifecycle_order`、`stage_order`、`activation_mode` 和 `pattern`。`lifecycle_order` 用于跨类别生命周期排序，`stage_order` 用于同一类别内的流程排序。每个 Workflow 必须声明 `workflow_type`、`lifecycle_order`、`entry_conditions` 和 `exit_evidence`。Profile 的 `include_skills` 必须按生命周期和阶段顺序排列。

场景级运行语义以 `manifest.json:routing` 为唯一 SSOT：一个 intent 只能有一个 `primary_skill`，`supporting_skills` 不得抢占入口，`fallback_skills` 必须指向已声明的 Skill 或 Optional Skill。`skill_routing_matrix` 只保留 `routing_intent` 引用与场景展示元数据；默认 catalog 从 routing IR 派生并同步更新 `docs/reference/skill-routing-matrix.md`，schema 禁止矩阵重复声明 primary/supporting/fallback/mutex/availability。
