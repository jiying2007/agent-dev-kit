# ADK Skill Lifecycle

## Scope

- Skill name:
- Intended profile: core | optional | reject
- Embedded full-stack layer: silicon/board | boot chain | BSP/rootfs | OS/runtime | driver | middleware/protocol | device application | host/production tool | diagnostics | OTA/field | safety/reliability
- Primary scenario:
- Non-goals:

## Creation Gate

| Gate | Decision | Evidence |
|---|---|---|
| Duplicate skill checked | pass |  |
| Trigger overlap checked | pass |  |
| Profile ownership decided | pass |  |
| Pilot requirement declared | pass |  |
| Fallback / replaced_by declared | pass |  |
| Output contract declared | pass |  |
| Deterministic guard declared | pass |  |
| Plugin boundary checked | pass |  |

## Pattern Classification

| Pattern | Fit | Required hard gate |
|---|---|---|
| Tool Wrapper | wraps CLI/API/MCP | command allowlist, input validation, exposure inventory, rollback |
| Generator | creates code/docs/assets | schema or template, overwrite policy, verification |
| Reviewer | evaluates existing work | severity rubric, evidence paths, false-positive handling |
| Inversion | user gives goal, agent controls workflow | explicit stop/ask conditions, state file, owner |
| Pipeline | multi-stage orchestration | code-level state check, checkpoints, resume and abort path |

Pipeline and Inversion skills must not rely only on prose such as "do not proceed". They need executable state checks, structured output validation, or an external workflow gate.

## Plugin Boundary

- Keep as skill when the workflow is prompt/process only and has no external runtime.
- Promote to plugin when it bundles MCP servers, hooks, apps, native binaries, background services, credentials, or third-party installers.
- Plugin promotion requires manifest, owner, version, license, source anchor, profile binding, readiness evidence and rollback.
- MCP-backed plugins must include exposure inventory, auth scope, schema/smoke evidence and deny-path guard tests.

## Output Contract

- Expected artifact:
- Schema/template:
- Pass condition:
- Needs-fix condition:
- Deny-path example:

## Metadata

- version:
- last_updated:
- quality_tier:
- owner:
- review_by:

## Validation

- `bash scripts/devkit.sh validate --strict`
- `bash tests/test_skill_trigger_matrix.sh`
- `bash scripts/pilot-readiness.sh --summary-json`
- `bash tests/run_all.sh`
