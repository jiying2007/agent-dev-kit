# Runtime Routing

ADK routes capabilities through profiles, skills, agents and workflows first. Runtime adapters are explicit tool targets and must not change ADK core semantics.

## Rules

1. Resolve profile membership before conversion or installation.
2. Keep runtime-specific paths out of core skills and manifests.
3. Run `bash scripts/devkit.sh runtime-boundary` after changing tool targets, install scripts or conversion scripts.
4. Record adapter-specific behavior in the adapter layer, not in ADK core.
