# 2026-10-29 upstream source freshness review

Source-only evidence for ADK dependency-maintenance PR #227. This document is **not** a delegated Spec/Quality verdict, owner sign-off, runtime activation, or evidence of an executed model/provider.

## API model catalog — volatile, watch-only

- Registry ID (retained for backwards-stable references): `openai-latest-model-gpt-5-5`.
- Authoritative pages checked 2026-10-29:
  - https://developers.openai.com/api/docs/models
  - https://developers.openai.com/api/docs/models/all
  - https://developers.openai.com/api/docs/guides/latest-model
- Actual observation: the official API model catalog now presents **GPT-6 Astra**, **GPT-6.1 Sol**, **GPT-6.1 Terra** and **GPT-6 Luna** in distinct capability/cost roles; GPT-5.6 appears as a previous model family. In particular, the old 2026-07-30 `GPT-5.6 current recommendation` sentence is obsolete.
- Technical decision: update the textual official-source observation and review date only. The registry ID is intentionally stable, and its `legacy_id_note` prevents the name from acting as current model truth. Retain `review_status=watch`, `adoption_scope=P2`, and no source-to-live change.
- Freshness: reviewed `2026-10-29`, expires `2026-11-28` (30-day volatile watch interval). There is **no** inferred model deployment, paid API call, routing switch, or head-to-head evaluation. Representative task evaluation, cost assessment, security review and a new source-pinned decision remain required before adoption.

## MCP 2026-07-28 final — immutable source identity, not enabled runtime

- Registry ID: `mcp-2026-07-28-final`.
- Sources checked 2026-10-29:
  - https://github.com/modelcontextprotocol/modelcontextprotocol/releases
  - https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28
  - https://modelcontextprotocol.io/specification/2026-07-28
  - https://blog.modelcontextprotocol.io/posts/2026-07-28/
- GitHub upstream `releases/latest` still selects the **2026-07-28** stable (not RC) release, published `2026-07-28T16:47:49Z`; full release Git commit stays `5f5440bb26a62e2cf3440b92da5a667efa03b267`. A commit-SHA-pinned source is not a new cryptographic user/Owner signature.
- Changes in that original specification include a stateless request-oriented protocol core and official extensions. This re-review does **not** authorize adopting them in any ADK target runtime. The existing metadata-only and 2026-07-31 owner-governed protocol contract remain the only accepted scopes; Tasks, Apps, extensions and external network/runtime integrations remain disabled without new safety/conformance review.
- Freshness: reviewed `2026-10-29`, expires `2026-12-28` (60-day stable-version check). The original revision, release timestamp, license caveat, candidate identity, owner decision and `enhance-metadata-only` state are unchanged.

## Review boundary and replay

The exact changes are confined to `manifests/official_docs_freshness_gates.json` and `manifests/external_agent_pattern_contracts.json`. Existing source expiry/fail-closed tests remain enabled. A future expiry must trigger **fresh external verification again**; do not simply extend dates or introduce defaults.

This is a source-freshness observation associated with ADK v8.1.3 maintenance. A separate independent Spec and Quality review still evaluates the exact PR HEAD under protected CI. Product M5, G21, G22 and LTA-04 are not certified by either source-list freshness or component-version maintenance.
