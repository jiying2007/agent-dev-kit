# Compatibility Matrix Runbook

## Purpose

Define which ADK assets can move across currently supported agent runtimes and
where unsupported semantics must degrade explicitly.

## Runtime Targets

This table follows the canonical target declarations in `manifest.json`; it is
not an independent target registry.

| Target | Status | Notes |
|---|---|---|
| Codex | external handoff target | Supported only through the owner-reviewed `~/codex -> ~/.codex` source-to-live chain; it is not an ADK direct export target. |
| Claude Code | experimental direct tool target | Agent and Skill export is governed by `manifests/target-contracts/claude-code.json`; no stable runtime claim is implied. |
| OpenCode | experimental direct tool target | Agent and Skill export is governed by `manifests/target-contracts/opencode.json`; no stable runtime claim is implied. |

A runtime absent from both `manifest.json:tool_targets` and
`manifest.json:external_handoff_targets` is unsupported and must not be
advertised as an active target.

## Compatibility Rules

- AGENTS-style policy, Skills and runbooks are portable only as far as their
  declared target contract preserves the required semantics.
- Direct export compatibility is claimed only for entries in
  `manifest.json:tool_targets`.
- Codex support is external handoff compatibility through
  `manifest.json:external_handoff_targets.codex`, never
  `export --target codex`.
- Official OpenAI/Codex and Anthropic/Claude references are provenance and
  method sources unless a canonical target declaration explicitly enables a
  runtime surface.
- Workflow scripts remain ADK-local unless the target contract declares an
  equivalent runtime entrypoint.
- MCP, plugin, hook and subagent behavior must declare support, explicit
  degradation or rejection before promotion.
- Silent downgrade is not allowed; unsupported behavior must fail closed or
  carry an explicit handoff/degradation boundary.

## Verification

```bash
bash scripts/devkit.sh validate --strict
bash tests/test_target_contracts.sh
bash tests/test_target_adapter_spi.sh
```

Runtime compatibility must not be claimed unless the canonical manifest target,
its target contract or external-handoff contract, and the corresponding tests
all agree.
