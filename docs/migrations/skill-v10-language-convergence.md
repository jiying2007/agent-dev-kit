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
3. The current transactional installer deliberately **does not prune** a managed destination omitted from the new Profile. A direct 9.x → 10.0.0 `install plan` returns `needs-review` with `managed destination is outside requested profile; rollback current install first`; it must not be forced or described as an automatic deletion.
4. Using the **trusted exact previous 9.x source and active receipt**, run the canonical `install rollback` workflow under the target lock. Verify the old files, modes and receipt first; if any managed file is modified, missing or inconsistent, stop for conflict resolution without deleting it. Confirm only the intended old managed assets were removed or restored; preserve unrelated/unmanaged files.
5. With the target free of managed retired assets, generate a fresh exact-10.0.0 `install plan`, review all creates and target identity, then `install apply` and verify its new receipt. Never write directly into a live home to bypass the plan/apply authority.
6. Verify target discovery uses the surviving primary Skills and that retired `adk-chinese-*` directories are absent. If a directory persists because it is unmanaged or user-edited, surface it as a conflict rather than deleting it.
7. Promote `llm_agent` pin and `~/codex -> ~/.codex` only after independent source/version/digest and native target verification. Do not infer runtime qualification from source CI.
8. To roll back, use a new reviewed source/release and its exact pin; never move existing immutable tags.

## Operational boundary
ADK build/control plane requires Python >=3.11, but consuming `SKILL.md` assets after deployment has no blanket Python requirement. Only specific Skill-owned external tools may require interpreters.

## 10.0.1 regression boundary

Both original `adk-chinese-code-review` and `adk-chinese-commit-conventions` names and their v9.0.0 `team-core` membership now receive isolated fixture-based migration tests. These fixtures use canonical v9 Manifest identities, but synthetic Skill bodies; they are **not** real previous source archives or target receipts. The installer still refuses modified managed files and requires exact trusted previous source + reviewed rollback/reinstall. No live target deployment has been verified.
