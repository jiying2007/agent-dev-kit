# Runtime Routing

ADK routes capabilities through profiles, skills, agents and workflows first. Direct runtime adapters are explicit `tool_targets`; runtime systems that require an external declarative chain are `external_handoff_targets`. Neither category may change ADK core semantics.

## Target Model

| Layer | Meaning | Boundary |
|---|---|---|
| `reference_sources` | External docs, official guidance, reference repos and provenance | Citation/governance only; no runtime enablement |
| `tool_targets` | ADK direct install/convert export targets | Must define format, directories, detection and rollback behavior |
| `external_handoff_targets` | Runtime systems handled by an external source-to-live chain | Must declare `direct_tool_target: false`, handoff mode and owner review |

Current support model:

- Claude Code and OpenCode are the current direct `tool_targets`; the canonical set is defined only by `manifest.json`.
- Codex is an external source-to-live handoff target through `~/codex -> ~/.codex`, not a direct export target.
- OpenAI/Codex source names in governance files are provenance labels, not ADK runtime bindings.

## Rules

1. Resolve profile membership before conversion or installation.
2. Keep runtime-specific paths out of core skills, scripts and direct tool defaults.
3. Run `bash scripts/devkit.sh runtime-boundary` after changing tool targets, external handoff targets, install scripts or conversion scripts.
4. Record adapter-specific behavior in the adapter layer or external handoff target, not in ADK core.
5. Do not promote reference source metadata into runtime enablement without a separate owner-approved runtime review.
