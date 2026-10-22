# Renew four expired official-source reviews

## Observed problem

The actual UTC date is 2026-10-22. The frozen 8.0.38 candidate full regression returned 91/101 passing scripts; the ecosystem source gate rejected four records whose review expiry was 2026-10-21. The complete tracked-source snapshots before and after that execution are identical. The failed terminal receipt and raw streams are retained in the delivery audit, not replaced by a later result.

The affected source IDs are `github-gh-aw-safe-outputs`, `mcp-registry`, `otel-genai-semconv`, and `vscode-agent-skills-2026`.

## Acceptance

1. Actually retrieve and review the four current official sources. Record retrieval time, canonical URLs, applicable revision identities when verifiable, and a claim-by-claim comparison with the current source notes and local adoption contract.
2. Correct any unsupported source note. Renew a reviewed source only after that review succeeds, using the actual review date and the established 30-day review interval. Preserve other source records.
3. Retain each existing method-only adoption/observation boundary. Runtime enablement, direct targets, permission grants, telemetry capture/export, schema mappings and qualification claims are outside this change.
4. Keep the existing reviewed OpenTelemetry adapter revision distinct from a new upstream observation. Do not silently rebind the adapter or invent a schema URL/version.
5. Independently review the proposed manifest difference and its source evidence, then run the canonical ecosystem gate and the required regression on the actual date. Do not weaken gates, modify tests to ignore expiry, or substitute a historical clock.

This source-maintenance correction does not supply Native, G22, LTA, or Product M5 field evidence.
