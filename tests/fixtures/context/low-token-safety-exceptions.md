# Low Token Safety Exception Fixtures

## compressed status example

- trigger: user asked for low token status
- active_scope: status_update_only
- safety_exception: none
- full_clarity_required: false
- preserved: commands, paths, risks, verification evidence, blockers

## security warning example

- trigger: security warning in dependency or credential handling
- active_scope: security_warning
- safety_exception: security warning
- full_clarity_required: true
- must_include: affected path, secret boundary, risk, mitigation, verification evidence

## irreversible action confirmation example

- trigger: delete, overwrite, publish, reset, migration, or history rewrite request
- active_scope: approval_prompt
- safety_exception: irreversible action confirmation
- full_clarity_required: true
- must_include: exact command, affected paths, reversibility, rollback path, approval question

## multi-step ambiguity example

- trigger: compressed wording would make order or approval boundary ambiguous
- active_scope: task_plan
- safety_exception: multi-step ambiguity
- full_clarity_required: true
- must_include: ordered steps, approval points, blockers, verification command

## review finding precision example

- trigger: code review finding requires precise evidence
- active_scope: review_response
- safety_exception: review finding precision
- full_clarity_required: true
- must_include: file, line, behavior chain, impact, recommended fix, test gap
