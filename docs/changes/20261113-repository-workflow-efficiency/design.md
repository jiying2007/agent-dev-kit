# Design and external method basis

- Existing `adk-commit-pr-quality-gate`, `adk-worktree-governance` and `adk-branch-closeout` remain the sole capability owners. Separate **message-only / PR-readiness / high-risk**, **stay-current / isolated / automation**, and **status-only / create-pr / merge / keep-discard**.
- No new Skill/Agent/Workflow. Preserve current triggering identity and permission ceilings; do not create new global policy or event scheduler.
- Only read long `references/` if that exact risk is present. Never make `SKILL.md` short by hiding mandatory checks without a trigger. Maintain original contract markers `Runtime Control Plane`, `permission_profile_decision`, `deny-path test`, `Dirty Worktree Decision`, `Automation Risk Decision`, `Heartbeat / Staleness Threshold`.
- OpenAI skill-creator method: https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md — concise methods, progressive disclosure, flexible instruction degree for safe vs fragile tasks.
- OpenAI skill discovery budget: https://learn.chatgpt.com/docs/build-skills — entries loaded when chosen; descriptions must remain specific and bounded.
- Anthropic best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices — preserve conditional rules, quality tests and independent real evaluation.
- References are **method-only**; no external code/Skill copied.
- Evidence: static source/checks only, model user-value improvements and actual billed token use remain **not-measured**. No new daily fee ceiling.
- Revert PR to restore old three SKILL.md files and reference/docs fixtures. GitHub branch protections and runtime permissions remain enforced by existing host.
