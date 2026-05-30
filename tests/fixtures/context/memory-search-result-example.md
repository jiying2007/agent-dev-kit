# Memory Search Result Fixture

## Search Index Layer

- query: latest ADK capability runtime pilot decision
- result_ids: runtime-pilot-2026-05-30
- time_window: 2026-05-30
- project_scope: llm_agent / agent-dev-kit
- observation_type: runtime-pilot-report
- redaction_status: none
- detail_fetch_reason:
- raw_fallback: reports/adk-capability-runtime-pilot-2026-05-30.md

## Layer

- search_layer: search_index
- timeline_context:
- selected_observation_ids: runtime-pilot-2026-05-30
- owner_approval_for_persistent_memory: not-requested

## Timeline Context Layer

- query: latest ADK capability runtime pilot decision
- result_ids: runtime-pilot-2026-05-30
- time_window: 2026-05-30
- project_scope: llm_agent / agent-dev-kit
- observation_type: runtime-pilot-report
- redaction_status: none
- detail_fetch_reason:
- raw_fallback: reports/adk-capability-runtime-pilot-2026-05-30.md

## Layer

- search_layer: timeline_context
- timeline_context: Runtime pilot found that gates pass but instance validation is still needed.
- selected_observation_ids: runtime-pilot-2026-05-30
- owner_approval_for_persistent_memory: not-requested

## Observation Details Layer

- query: latest ADK capability runtime pilot decision
- result_ids: runtime-pilot-2026-05-30
- time_window: 2026-05-30
- project_scope: llm_agent / agent-dev-kit
- observation_type: runtime-pilot-report
- redaction_status: none
- detail_fetch_reason: implementation handoff requires exact prior decision
- raw_fallback: reports/adk-capability-runtime-pilot-2026-05-30.md

## Layer

- search_layer: observation_details
- timeline_context: Runtime pilot report decision section requires fixtures before full runtime promotion.
- selected_observation_ids: runtime-pilot-2026-05-30
- owner_approval_for_persistent_memory: not-requested
