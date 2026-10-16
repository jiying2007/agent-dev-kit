# Skill Description Discovery Preflight

Status: **deterministic source-only**; no native or model execution.

OpenAI Skills documentation confirms discovery first shows `name` and `description`, not ADK-specific `triggers` or `non_triggers`. Eight high-confusion near-neighbor Skill descriptions now state when to use and when not to use them. Each modified `SKILL.md` is byte-neutral or smaller; existing profile-source and token budgets are unchanged.

The established `tests/test_skill_trigger_matrix.py` reuses ADK's production frontmatter reader to test eight description-only metadata pairs. It asserts distinct positive vocabulary and explicit exclusions, **not** model rank accuracy. Production automatic routing is still tested through the existing canonical `match_text()` catalog tests, unchanged.

This proves only static metadata stability, not Codex/Claude/OpenCode behavior, native Skill loading, routing precision, Agent task success, Token/cost reduction, real device performance, G21 or G22. The independent real authenticated native campaign and preregistered real A/B/C effect trial remain open and require genuine receipts/owner evidence. No third-party Skill pack, new router, persistent eval service or runtime dependency was introduced.

Sources: OpenAI Skills official documentation and skill evaluation guide (2026-10-16); method-only adoption. Rollback: revert this candidate.
