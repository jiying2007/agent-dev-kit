# Compatibility Matrix Runbook

## Purpose

Define which adk assets can move across supported agent runtimes and where they
must degrade explicitly.

## Runtime Targets

| Target | Status | Notes |
|---|---|---|
| Codex | primary | Production target through `~/codex -> ~/.codex`. |
| Claude Code | compatible text target | Preserve agent and skill semantics; runtime hooks may degrade. |
| Hermes Agent | compatible text target | Preserve team handoff and collaboration assets where possible. |
| OpenCode | compatible text target | Preserve basic agent and skill directory structure. |

## Compatibility Rules

- AGENTS-style policy, skills and runbooks are portable as text assets.
- Workflow scripts remain adk-local unless the target runtime has an equivalent
  script entrypoint.
- MCP, plugin, hook and subagent behavior must declare support, fallback or
  rejection before promotion.
- Silent downgrade is not allowed; unsupported behavior needs an explicit
  fallback note.

## Verification

```bash
rtk bash agent-dev-kit/scripts/devkit.sh validate --strict
rtk bash scripts/check-runtime-routing.sh .
```

Multi-runtime compatibility must not be claimed unless the target assets and
fallback behavior are both documented.
