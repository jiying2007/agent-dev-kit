# Memory Search Result

- query:
- result_ids:
- time_window:
- project_scope:
- observation_type:
- redaction_status: none / redacted / sensitive / unknown
- detail_fetch_reason:
- raw_fallback:

## Layer

- search_layer: search_index / timeline_context / observation_details
- timeline_context:
- selected_observation_ids:
- owner_approval_for_persistent_memory: yes / no / not-requested

## Notes

- Search starts from compact `search_index` results.
- Fetch `timeline_context` only for selected IDs or scoped queries.
- Fetch `observation_details` only when `detail_fetch_reason` is filled.
- Memory hits are candidate context until checked against `raw_fallback`.
