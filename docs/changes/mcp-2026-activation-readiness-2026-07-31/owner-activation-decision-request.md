# 独立 Owner Activation Decision Request

## Status

`completed`。owner `leiwenjun` 已于 2026-07-31 选择 `ACTIVATE`；正式记录：
`owner-activation-decision.json`。

## Decision target

- candidate：`epc-c6f947d482aa8aa0c78f`
- protocol：`2026-07-28`
- independent owner：`leiwenjun`
- current active protocol：`2026-07-28`
- technical readiness：completed
- activation scope：`protocol-governance-contract-only`

## Evidence presented to owner

1. `verify-report.md`：四项技术前置条件、不可变版本身份和命令级证据。
2. `review-report.md`：独立性、权限边界、真实性核验和剩余风险。
3. `breaking-change-diff.md`：final 与 active contract 的差异和回退边界。
4. `negative-results.md`：红灯、错误假设和修复证据。
5. `tests/mcp_2026_activation/mcp_activation_test.go`：schema/client-server/auth/rollback 行为 fixture。
6. `schemas/mcp-protocol-activation-decision.schema.json`：owner decision 的机器可读合同。

## Decision semantics

| Decision | State transition | Runtime / features |
|---|---|---|
| `ACTIVATE` | 把 active protocol governance contract 切换到 `2026-07-28` | runtime、Tasks、Apps、extensions 继续 false |
| `HOLD` | active 保持 `2025-11-25`，保留技术证据供后续复审 | 全部继续 false |
| `REJECT` | active 保持 `2025-11-25`，记录拒绝理由 | 全部继续 false |

`ACTIVATE` 不表示启动真实 MCP server、配置 credential、发布资产或启用
Tasks/Apps/extensions。上述操作均不在本次授权范围内。

## Known residual risk

- 固定 Go SDK 是 `v1.7.0-pre.3`，尚非稳定 release。
- 证据来自离线本地 loopback，不覆盖真实 IdP、反向代理、跨 SDK、负载与长时稳定性。
- 根 `llm_agent` quick aggregate 当前 49/54；五项失败已归因到过期 reference baseline、
  stale artifact hash、gitlink/lock 状态和本次合法 dirty 变更，不能宣称全工作区全绿。

## Owner response received

- decision：`ACTIVATE`
- rationale：接受当前固定版本技术证据及已披露的预发布和单SDK验证风险，同意仅激活协议治理
  契约，runtime 与 Tasks、Apps、extensions 继续保持关闭。
- decision ID：`mcp-act-2026-07-31-leiwenjun`
