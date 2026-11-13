# 2026-11-13 Independent primary source freshness review

This is a **metadata-only** refresh required by the unrelated existing source freshness gate encountered in PR #254. No adapter, network execution, provider permission or interop conformance claim changed.

- `agent-skills-open-format`: https://agentskills.io/specification — read on 2026-11-13; SKILL.md with name/description frontmatter and optional supporting directories remain documented. Decision `adopt-method-only` unchanged.
- `agent-client-protocol`: https://github.com/agentclientprotocol/agent-client-protocol/blob/main/CHANGELOG.md — checked on 2026-11-13; latest visible stable version 1.17.0 dated 2026-11-10; unstable/v2 features exist. CHANGELOG blob `aa50ae1c7a4dd15be1e1f121218dd73e80679d49`. Decision `observe-method-only` unchanged.
- `a2a-protocol-1-0`: https://a2a-protocol.org/latest/specification/ — checked on 2026-11-13; official page reports Latest Released Version 1.0.0. Decision `observe-method-only` unchanged.

All three old records expired on 2026-11-12. New `retrieved_at=2026-11-13`, `expires_at=2027-01-12` preserves the previous 60-day review interval. This document records source content observations, **not runtime qualification**. Any future drift in A2A/ACP or security impact requires separate review.
