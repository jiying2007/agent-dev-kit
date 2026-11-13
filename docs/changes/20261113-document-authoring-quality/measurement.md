# Entry source footprint (2026-11-13)

Exact UTF-8 Git blob byte counts for the seven rewritten Skill entry files, baseline ADK 11.2.7 vs candidate 11.2.8.

| Skill | Before bytes | After bytes | Saved bytes |
|---|---:|---:|---:|
| adk-adr-writer | 5201 | 2614 | 2587 |
| adk-after-action-review | 6948 | 3200 | 3748 |
| adk-cross-team-handoff | 4407 | 2335 | 2072 |
| adk-requirements-triage | 6386 | 3400 | 2986 |
| adk-lightweight-planning | 3469 | 2158 | 1311 |
| adk-knowledge-archive | 2733 | 2236 | 497 |
| adk-incident-rca-report | 3992 | 2301 | 1691 |
| **Total** | **33136** | **18244** | **14892** |

Reduced source entry-file size by 44.9%. Other source tests and maintained docs are excluded; **this does not measure runtime prompt size or billed Token usage**. Document quality, hallucination rate, human editing cost, latency and actual Token cost remain **not-measured**. Offline cases are design-level regression contracts, not executions of an LLM.
