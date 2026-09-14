# Low Token Profile

> Runtime budget overlay only. It is **not** a manifest asset profile and never weakens safety or evidence gates.

- trigger:
- active_scope:
- base_policy: balanced
- overlay_mode: fast
- technical_terms_preserved:
- safety_exception: none / security warning / irreversible action confirmation / multi-step ambiguity / review finding precision
- restore_condition: high-risk / low-confidence / missing-raw-evidence / safety-exception / user-disable
- usage: input_tokens / output_tokens / cached_tokens / total_tokens / unavailable
- user_override:

## Rules
- Preserve commands, paths, source references, risks, verification evidence and blockers.
- Load agent/skill/tool/reference detail only after intent match; keep stable reusable context before dynamic context.
- Summaries keep a raw pointer; full evidence stays retrievable outside the active context.
- Restore `audit/L3` for high risk or whenever compression increases ambiguity.
- The user can disable the overlay explicitly.
