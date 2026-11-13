# Task packaging and estimates (on demand)

Only load for multi-slice scheduling, machine-dispatched task packages or genuinely decision-relevant time estimates.

## Evidence-oriented decomposition
- For human plans: goal, owner, dependencies, independently observable done-when, real validation evidence and risk.
- For machine-dispatched work: `adk-task-package-schema-v2` with `structured_output_schema`, `strict_schema_decision`, `refusal_handling`, `work_item_kind`, `question_to_resolve`, `evidence_required`, `implementation_permission`, `exit_gate`, `handoff_target`, `retention_decision`, `global_constraints`, `interfaces`, `scope_read`, `scope_write`, `ready_to_handoff`.
- `decision/research/prototype` are non-implementation; prototype carries `prototype_evidence`. Owner/authority is immutable across worker attempts, never inferred from report text.
- Build a DAG only for actual blocking dependencies. Ready Frontier is recomputed after genuine evidence change, not on repeated unmodified summaries.
- Shared schema, test fixture, migration, or root config should have one writer; otherwise serialize.

## Estimating only when useful
- Historical observed elapsed time is preferable; if unknown use explicit range or `not-estimated`.
- T-shirt / three-point estimates can support real staffing or critical-path decisions, but do **not** imply fixed 0.5–8h task-size validity.
- Record critical path only if dependencies/schedule matter; cost from extra agent orchestration and integration may exceed parallel gains.
