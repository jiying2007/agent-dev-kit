# Worker Contract

task_id:
owner:
agent_identity:
runtime_identity:
primary_skill:
supporting_skills:

## Goal

## Scope

scope_read:
- 

scope_write:
- 

must_not_touch:
- 

dependencies:
- 

context_strategy:
  context_health:
  branch_action: continue | rewind_to_evidence | fresh_brief | compact_with_goal | subtask
  raw_evidence:
  summary:

## Execution Rules

- Worker is not alone in the codebase.
- Agent identity, runtime profile, workspace and message entrypoint must be stated explicitly; do not infer identity from directory path alone.
- Do not revert or overwrite changes outside `scope_write`.
- Stop and report if the task requires editing `must_not_touch` or a shared contract.
- Keep implementation aligned with the assigned `primary_skill`.
- If context is polluted by failed attempts or irrelevant logs, stop and request a fresh brief instead of continuing from stale assumptions.

## Done Criteria

- 

## Verification Commands

verification_commands:
- 

## Report Schema

report_schema:

```json
{
  "task_id": "",
  "status": "DONE|BLOCKED|NEEDS_CONTEXT",
  "verified_facts": [],
  "inferences": [],
  "evidence": [],
  "changed_files": [],
  "verification": [],
  "risks": [],
  "handoff_summary": ""
}
```

## Conflict Policy

- Same-file write conflict: stop and return `BLOCKED`.
- Shared contract/schema/root config change: stop and return `NEEDS_CONTEXT`.
- Verification failure after local fix attempt: return `BLOCKED` with command output summary.
