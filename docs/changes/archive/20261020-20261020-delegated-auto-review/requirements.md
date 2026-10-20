# Delegated automatic review requirements

The owner explicitly instructed on 2026-10-20 at 06:43:29 UTC: “授权自动推进，自动审核，提高推进和审核质量，不用人工干预”. This authorizes automatic review and normal protected delivery; it does not claim that the owner personally performed a review or that missing runtime/field observations exist.

| Requirement | Acceptance |
|---|---|
| REQ-001 | ACC-001: The existing review/archive lifecycle consumes a single typed, bounded review-evidence validator. An explicitly opted-in repository must not accept CLI pass/count strings without valid delegated review evidence. |
| REQ-002 | ACC-002: Evidence identifies an actual AI reviewer independent from the implementer, records separate Spec and Quality verdicts, unresolved findings, real authorization/review/evidence times, and exact source/evidence/policy/validator byte digests. Missing, ambiguous, stale, unsafe or contradictory inputs fail closed. |
| REQ-003 | ACC-003: Harness retains its seven dimensions, structural checks, 90-day limit and field-evidence boundary. Repository opt-in requires a current source-bound review covering every dimension, including justified N/A; changing only dates is insufficient. |
| REQ-004 | ACC-004: The three frozen historical changes receive actual independent delegated review and follow the existing review/archive lifecycle. Historical facts and original verification records remain intact; records use relocation-safe evidence references. |
| REQ-005 | ACC-005: Existing protected PR checks, supported Python 3.8/3.11/3.12, immutable component release and downstream exact-source promotion remain required. Automatic review does not invoke a provider, spend money, generate observations or itself authorize product release. |

This is one review-authority integration change. It does not introduce a second workflow engine, external review service, new mandatory human approver, or an automated generator of semantic pass verdicts.
