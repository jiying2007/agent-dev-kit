# Interoperability Boundaries

ADK core owns a stable asset/evidence/workflow model. External runtimes and protocols are integrations, not core domain identities.

## 1. Boundary rule

Every external integration must cross a versioned adapter boundary:

```text
ADK canonical IR
      |
      +-- target adapter ----------> runtime/CLI asset surface
      +-- protocol adapter --------> MCP / A2A / other protocols
      +-- telemetry adapter -------> OpenTelemetry GenAI or other observability schema
```

The adapter is responsible for translation, version pinning, capability negotiation, negative cases and rollback. Core code must not silently inherit the lifecycle or semantic version of an external protocol.

## 2. Required adapter identity

A runtime/protocol adapter contract must identify at least:

- ADK adapter API version;
- external protocol/runtime name and exact version or version range;
- direction (`export`, `import`, `bidirectional`, `telemetry`);
- supported ADK asset/evidence kinds;
- unsupported or lossy fields;
- detection/discovery contract;
- validation/smoke/native evidence level;
- rollback or downgrade behavior;
- owner and freshness source.

Unknown fields or an unreviewed external version must fail closed at the compatibility boundary.

## 3. MCP

MCP remains an external tool/resource/context interoperability protocol. Protocol-governance metadata may live in ADK manifests, but MCP tasks/apps/extensions or transport behavior must not become implicit ADK core behavior. Enabling new MCP protocol features requires a reviewed adapter/activation decision and compatibility evidence.

## 4. A2A

A2A is an Agent-to-Agent interoperability surface. ADK may describe portable Agent assets and capability metadata, but scheduling, remote-agent lifecycle and production message transport remain outside ADK core. A2A support must be implemented as a versioned adapter over canonical ADK identity/capability data.

## 5. OpenTelemetry GenAI

ADK evidence and trace schemas remain canonical for ADK. OpenTelemetry GenAI semantic conventions are an export/projection target, not the internal permanent schema. The adapter must pin the semantic-convention version and default to metadata-only/sanitized output; raw prompt, message and tool payload capture remains forbidden unless an independent privacy policy explicitly permits it.

## 6. Evidence semantics

Adapter conformance and product qualification are independent:

```text
static adapter pass
    != runtime-native pass
    != runtime-certified
    != product-qualified
```

A caller-supplied fixture or protocol smoke can prove only the scope it actually measured. Missing native runtime evidence remains `blocked`, `not_measured`, or `not_required` as appropriate; it is never promoted to `pass` by documentation.

## 7. Consumer-driven compatibility

ADK releases should be consumed through immutable release/source identity plus a consumer contract. Consumers such as Codex or digital-worker own their local runtime assembly and must bind every vendored ADK asset to an exact release/source identity. Consumer CI should reject stale compatibility projections rather than requiring ADK core to embed consumer-specific assembly logic.
