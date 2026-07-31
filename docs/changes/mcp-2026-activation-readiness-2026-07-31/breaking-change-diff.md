# MCP 2026-07-28 breaking-change diff

## Evidence identity

- final specification tag：`2026-07-28`
- final specification commit：`5f5440bb26a62e2cf3440b92da5a667efa03b267`
- active baseline：`2025-11-25`
- verified SDK：`github.com/modelcontextprotocol/go-sdk v1.7.0-pre.3`
- SDK tag commit：`827f90ba0c13edb546028df42fadc9f1211a4ff2`
- reviewed_at：`2026-07-31`

## Diff 与本轮处置

| Area | 2025-11-25 baseline | 2026-07-28 candidate | 本轮验证/处置 |
|---|---|---|---|
| lifecycle | `initialize` session handshake | `server/discover` + per-request metadata | modern smoke 精确协商 `2026-07-28`；rollback 精确协商 legacy |
| HTTP state | sessionful 可用 | modern HTTP 要求 stateless/sessionless | modern fixture 固定 `Stateless=true`，断言无 `Mcp-Session-Id` |
| routing headers | limited headers | `Mcp-Method`、`Mcp-Name` 等标准 header | 捕获并验证 discover/list/call 的 protocol/method header |
| JSON Schema | 旧 schema contract | JSON Schema 2020-12 | input/output 正例及 required/type/output 负例 |
| authorization | PRM/resource indicator/no passthrough baseline | issuer/audience/scope boundary 加固 | missing/issuer/audience/scope/expiry/no-passthrough 全部 fail closed |
| deprecated core features | roots/sampling/logging 可用 | deprecated | 不在本轮启用；candidate 保留 deprecated list |
| extensions | 非统一独立扩展模型 | extensions framework | Tasks、Apps、extensions 与 extension IDs 全部保持 disabled/empty |
| rollback | active 为 legacy | candidate 可 modern | stateful legacy endpoint 仍 list/call 可用，modern application request 被拒绝 |

## Activation 结论边界

breaking-change diff 和四项技术证据已完成，但只覆盖固定 Go SDK、离线容器、本地
Streamable HTTP loopback、合成 auth verifier 和 legacy rollback。真实反向代理、IdP、
跨 SDK/跨实现、负载与长时运行不在本 evidence scope。

technical readiness 阶段只允许：

- `technical_readiness_completed=true`
- scoped `final_compatibility_claim=true`

owner decision 前不允许：

- 在 owner decision 前设置 `activation_allowed=true`
- 自动切换 active protocol 或 runtime
- 自动启用 Tasks、Apps 或 extensions

## Owner 决策后的状态

owner `leiwenjun` 于 2026-07-31 选择 `ACTIVATE`，decision ID 为
`mcp-act-2026-07-31-leiwenjun`。本次只切换治理状态：

- active protocol：`2026-07-28`
- active scope：`protocol-governance-contract-only`
- runtime：disabled
- Tasks / Apps / extensions：disabled
- rollback target：`2025-11-25`

这不是 runtime/API 部署 breaking change；但对读取 active protocol 的治理 consumer
属于显式状态变更。consumer 必须同时读取 active scope、runtime 和 feature flags，禁止只
按 protocol version 推导运行能力。
