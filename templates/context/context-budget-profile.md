# Context Budget Profile

- task_type: exploration / bugfix / review / audit / handoff
- risk_level: low / medium / high
- budget_profile: fast / balanced / precision / audit
- read_tier: L0 / L1 / L2 / L3
- compress_allowed: yes / limited / no
- raw_required: yes / no
- raw_evidence:
- fallback_condition:
- do_not_read:
- last_verified:

## Budget Mix

| source | percent | rule |
|---|---:|---|
| project_map | 0 | use only when current enough |
| search_results | 0 | merge duplicate hits |
| source_windows | 0 | prefer related functions and callers |
| logs | 0 | keep failing cases, top stack, repeat count |
| diff | 0 | keep changed files, hunks, public contract changes |
| docs | 0 | keep stable rules, not chat history |

## Mode Rules

- fast: L0/L1 first, aggressive summaries, raw evidence must remain reachable.
- balanced: L1/L2, type-aware summaries, read local source windows before editing.
- precision: L2 first, limited compression, read callers, tests, configs, and key logs.
- audit: L3 for conclusion evidence; only dedupe, sort, or redact sensitive data.
