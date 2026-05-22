# Worker Contract

task_id:
owner:
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

## Execution Rules

- Worker is not alone in the codebase.
- Do not revert or overwrite changes outside `scope_write`.
- Stop and report if the task requires editing `must_not_touch` or a shared contract.
- Keep implementation aligned with the assigned `primary_skill`.

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
