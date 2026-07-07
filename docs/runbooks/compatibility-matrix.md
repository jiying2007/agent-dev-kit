# Compatibility Matrix Runbook

## Purpose

Define which adk assets can move across supported agent runtimes and where they
must degrade explicitly.

## Runtime Targets

| Target | Status | Notes |
|---|---|---|
| Codex | external handoff target | Supported through `~/codex -> ~/.codex` source-to-live; not an ADK direct export target. |
| Claude Code | direct tool target | Preserve agent and skill semantics; runtime hooks may degrade. |
| Hermes Agent | direct tool target | Preserve team handoff and collaboration assets where possible. |
| OpenCode | direct tool target | Preserve basic agent and skill directory structure. |

## Compatibility Rules

- AGENTS-style policy, skills and runbooks are portable as text assets.
- Direct export compatibility is claimed only for entries in `manifest.yaml:tool_targets`.
- Codex compatibility is claimed as external handoff compatibility through `manifest.yaml:external_handoff_targets.codex`, not `convert --target codex`.
- OpenAI/Codex references in governance docs are provenance and method sources, not runtime enablement.
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
