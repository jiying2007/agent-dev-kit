# Repository workflow Skill efficiency (11.2.10)

## Purpose
Three existing Skills currently impose full PR/worktree/closeout templates on trivial requests. Optimize the human experience and source footprint without granting SCM writes or bypassing protected CI.

## Acceptance
- Message-only commit formatting does not require PR evidence or trigger commit/push. PR-readiness still binds exact source HEAD/diff/CI.
- Worktree stay-current path does not create a branch, environment, scheduler or duplicate worker. Dirty user files and provenance are preserved; only authorized isolated operations can mutate.
- Closeout status-only checks don't show all choices or execute operations; direct create-pr/merge/discard remains permission-checked and correct-snapshot-bound.
- High-risk release, DB/schema, MCP/control plane, secret isolation, CI and device safety still fail closed; only relevant checks load long references.
- No new Skill/Agent/Workflow, provider model calls, Codex/Work usage, private repo, timer or Root pin mutation.
- 18 source-only expected scenarios, routing positives/negatives and Python contract tests; actual behavior and token usage are not-measured.
