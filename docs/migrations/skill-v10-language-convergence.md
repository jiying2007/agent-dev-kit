# ADK 10.0.0 Skill capability and language convergence

## Breaking change
Remove `adk-chinese-code-review` and `adk-chinese-commit-conventions` from core and `team-core`. This is intentional: language is output policy, not a separate Skill execution workflow.

## Replacement
- `adk-code-review-loop`: code review in the user's requested language (default: `manifest.locale=zh-CN`), unified evidence and `blocker/major/minor` severity.
- `adk-commit-pr-quality-gate`: commit/PR quality. Use repository Commit Policy; optional syntax validator `python3 -m agent_dev_kit.commit_message_policy --message "fix(runtime): 修复回退判断"` runs only in ADK build environment.
- No compatibility aliases, mirroring, implicit git commits or required Issue number for normal fixes.

## Installation and rollback
1. Preserve existing source/live target identity and back up managed installer inventory.
2. After immutable 10.0.0 release verification, regenerate install/export plan from exact source/tag.
3. Review the diff; remove *managed, unmodified* retired assets through the normal plan/apply path only. Do not overwrite user-edited files; report unmanaged conflicts.
4. Verify target discovery uses the surviving primary Skills, and that previously installed language-only directories no longer shadow them.
5. Promote `llm_agent` pin and `~/codex -> ~/.codex` only after independent source/version/digest and native target verification. Do not infer runtime qualification from source CI.
6. To roll back, use a new reviewed source/release and its exact pin; never move existing immutable tags.

## Operational boundary
ADK build/control plane requires Python >=3.11, but consuming `SKILL.md` assets after deployment has no blanket Python requirement. Only specific Skill-owned external tools may require interpreters.
