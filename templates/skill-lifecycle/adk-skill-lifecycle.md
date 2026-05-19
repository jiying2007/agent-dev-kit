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

## Metadata

- version:
- last_updated:
- quality_tier:
- owner:
- review_by:

## Validation

- `bash scripts/devkit.sh validate --strict`
- `bash scripts/check-fallback-sunset.sh`
- `bash tests/run_all.sh`
