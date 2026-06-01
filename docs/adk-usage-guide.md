# ADK Usage Guide

## 1. What ADK Is

`agent-dev-kit` is a platform-neutral asset kit for Agent, Skill, Profile and Workflow governance.

Use ADK when you need to:

- Turn unclear work into verifiable requirements, tasks and evidence.
- Select the right Agent/Skill/Workflow for a delivery path.
- Export curated assets to a declared runtime target.
- Keep profile composition, routing, validation and release gates auditable.
- Prevent historical compatibility residue, unclear ownership and unverified assets from entering active source.

ADK is not a runtime-specific home directory, a hidden compatibility bridge, or a replacement for project-specific engineering tests.

## 2. Core Concepts

| Concept | Purpose | Source of Truth |
|---|---|---|
| Agent | Accountable role, ownership, handoff and quality gate | `manifest.yaml:agents`, `agents/<name>/AGENTS.md` |
| Skill | Reusable method, commands, evidence template and quality gate | `manifest.yaml:skills`, `skills/<name>/SKILL.md` |
| Optional Skill | Opt-in capability that is not part of core profiles by default | `manifest.yaml:optional_skills`, `optional-skills/<name>/SKILL.md` |
| Profile | Resolved runtime asset set for a scenario | `manifest.yaml:profiles` |
| Workflow | Stage contract, artifact contract and verification sequence | `manifest.yaml:workflows`, `workflows/<name>/WORKFLOW.md` |
| Change Set | Reviewable change artifacts and state gates | `docs/changes/<change-id>/` |

Naming and boundary rules are defined in `docs/asset-contract-standard.md`.

## 3. Command Prefix

The scripts themselves are plain shell scripts. In a normal shell, examples can be run as `bash ...`.

Inside Codex-managed sessions on this machine, run commands through `rtk`:

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/run_all.sh
```

## 4. Choose a Profile

| Profile | Use When |
|---|---|
| `core` | General requirements, implementation, validation and review work |
| `personal-core` | Personal project work with extra summary and archive skills |
| `team-core` | Team handoff, review and communication workflows |
| `embedded-fullstack` | SoC, BSP, driver, RTOS, device app, tooling, production and field readiness |
| `release-hardening` | Release readiness, versioning, security, performance and rollback checks |
| `openspec-driven` | Spec-driven requirement/design/task changes |
| `large-refactor` | Broad refactors with API and simplification governance |
| `incident-response` | Incident diagnosis, reliability and security response |
| `research-intake` | External reference analysis and adoption decisions |

Profiles are inherited and checked as closed sets. If a profile includes an Agent, the profile must also resolve that Agent's `default_skills`.

Check profile coherence:

```bash
rtk bash scripts/check-profile-coherence.sh
```

## 5. Validate the Repository

Run these before relying on generated assets:

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/devkit.sh runtime-boundary
rtk bash scripts/devkit.sh openai-governance --summary-json
rtk bash tests/run_all.sh
```

Use `validate --quick` only for local edit loops. It intentionally skips heavier dependency checks.

## 6. Find the Right Asset

Build the catalog:

```bash
rtk bash scripts/devkit.sh catalog build
```

Search assets:

```bash
rtk bash scripts/devkit.sh catalog find --type agent --keyword 需求
rtk bash scripts/devkit.sh catalog find --type skill --keyword bring-up
rtk bash scripts/devkit.sh catalog find --type workflow --keyword 发布
```

Check trigger matching:

```bash
rtk bash scripts/devkit.sh match --skill adk-requirements-triage --text "需求不清楚，需要先梳理验收标准"
rtk bash scripts/devkit.sh match --skill adk-systematic-debugging --text "问题根因不明确，需要定位后修复"
```

Routing rules:

- One scenario has one primary Skill.
- Supporting Skills add checks; they do not take over the entry point.
- Agent ownership decides responsibility; Skill ownership decides reusable method.
- Workflow ownership decides stage order and required evidence.

## 7. Use Workflows for Changes

For reviewable changes, use a change directory under `docs/changes/<change-id>/`.

Typical lifecycle:

```bash
rtk bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"
rtk bash scripts/devkit.sh apply --change can-fd-bringup
rtk bash scripts/devkit.sh verify --change can-fd-bringup
rtk bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 0
rtk bash scripts/devkit.sh archive --change can-fd-bringup
```

Minimum artifact expectations:

- `proposal.md`: problem, goal, non-goal, sufficiency, risk and breaking-change decision.
- `design.md`: interface, compatibility, migration and rollback boundaries.
- `tasks.md`: owners, scope, verification command and completion criteria.
- `verify-report.md`: command evidence and results.
- `review-report.md`: findings, risk decision and release decision.
- `negative-results.md`: failed attempts and rejected paths.

## 8. Install or Convert Assets

Install to a declared target:

```bash
rtk bash scripts/devkit.sh install --tool claude-code --target /tmp/adk-target --mode copy --profile core
```

Convert to target format:

```bash
rtk bash scripts/devkit.sh convert --target claude-code --profile embedded-fullstack --out dist/claude-code --clean
```

Rules:

- `--target` must be declared in `manifest.yaml:tool_targets`.
- Do not write directly to a user runtime directory without backup, dry-run or an explicit rollback path.
- Do not add platform-specific active paths to ADK core.
- Generated `dist/` output is disposable; source truth stays in `manifest.yaml`, `agents/`, `skills/`, `optional-skills/`, `workflows/` and `docs/`.

## 9. Change Agent, Skill or Workflow Assets

Before changing assets, decide the asset type:

- Add or edit an Agent when ownership, handoff or decision authority changes.
- Add or edit a Skill when a reusable method, command pattern or evidence template changes.
- Add or edit a Workflow when stage order, artifact contract or verification sequence changes.
- Add an Optional Skill when the capability is useful but should not be active in default profiles.

After asset changes:

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/devkit.sh catalog build
rtk bash tests/test_catalog.sh
rtk bash tests/test_workflow_contract.sh
rtk bash tests/run_all.sh
```

Hard boundaries:

- Agents do not use the `adk-` prefix.
- Core Skills use the `adk-` prefix.
- Agent names must not duplicate Skill names.
- Historical role-style assets are hard-cut, not aliased.
- Profile closure must include every resolved Agent's `default_skills`.

## 10. Commit and Release Gate

Before commit:

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/check-profile-coherence.sh
rtk bash scripts/devkit.sh runtime-boundary
rtk bash tests/run_all.sh
rtk git diff --cached --check
```

Commit format:

```text
<type>(scope): <中文动词短句>
```

Examples:

```text
feat(profile): 收敛资产命名和 profile 闭包
docs(usage): 增加 ADK 使用指南
fix(catalog): 修复 workflow matrix 生成格式
```

Before pushing, check:

- Working tree status is expected.
- All intended deletes and renames are staged.
- Residual scans for removed IDs are clean when doing hard cutovers.
- Full regression has passed.

## 11. Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| `profile coherence` fails | profile redeclares inherited assets or misses Agent default Skills | Remove inherited duplicates or add missing Skills to the resolved profile |
| catalog differs after generation | `manifest.yaml` changed but docs were not regenerated | Run `rtk bash scripts/devkit.sh catalog build` |
| `file_modes` fails on deleted files | deletion is not staged in Git index | Stage intended deletes with `rtk git add -A` |
| `runtime-boundary` fails | active source contains platform-specific runtime path or handoff | Move platform details to reference/archive metadata or declare an explicit target |
| `workflow contract` fails | Workflow references Agent/Skill outside profile closure | Update profile membership or Workflow contract |

## 12. Minimal Daily Checklist

For normal edits:

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/test_catalog.sh
rtk bash tests/test_workflow_contract.sh
```

For asset or manifest changes:

```bash
rtk bash scripts/check-profile-coherence.sh
rtk bash scripts/devkit.sh catalog build
rtk bash tests/run_all.sh
```

For release or push:

```bash
rtk bash tests/run_all.sh
rtk bash ~/codex/scripts/final-ready.sh
```
