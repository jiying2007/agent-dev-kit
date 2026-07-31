# 审查报告：mcp-2026-activation-readiness-2026-07-31

## Review verdict

独立 owner 已签署 `ACTIVATE`，schema-valid record、manifest 状态迁移和定向复验已完成。
允许标记为 `protocol-governance-contract-only` activated；不得标记为 runtime 或 feature
activated。

## Findings

### Blocker

无。

### Major

无。

### Minor / residual

1. 官方 Go SDK 固定版本为 `v1.7.0-pre.3`。其行为证据有效，但稳定性承诺仅限该版本。
2. auth 测试使用本地 synthetic claims/verifier，不等价于真实 OAuth/IdP 集成验证。
3. loopback smoke 不覆盖 proxy、跨实现互操作、性能、长稳和生产回滚编排。
4. 根工作区 quick aggregate 尚有五项既有治理失败，不能据此宣称全仓可合并。

## 真实性核验

- schema 断言由 SDK 注册、请求解析和 output validation 实际执行，不是静态 JSON 比较。
- client 与 server 均来自固定 SDK module，协议版本/header/list/call 有行为级断言。
- auth 负例覆盖 401/403、issuer/audience/scope/expiry 和 token no-passthrough。
- rollback 启动独立 legacy handler，验证协商版本、legacy 正向调用和 modern fail-closed。
- offline wrapper 同时核对 owner record、manifest active scope 和 runtime/features deny
  boundary，防止协议激活意外扩大运行权限。
- `final_compatibility_claim` 附带明确 scope，不授权 runtime 或 feature enablement。

## 权限与副作用审查

- prepare 只读取公开 module proxy/checksum 数据并写显式 `/tmp` cache。
- offline smoke 使用 `--network=none`，不读取环境 credential，不连接真实服务。
- 未修改 `~/codex`、`~/.codex`、真实 MCP runtime 或安装状态。
- 未执行 commit、push、merge、rebase。

## Owner independence

实现者未代签 decision。owner `leiwenjun` 明确选择 `ACTIVATE` 并提供不少于 20 个字符
的理由；正式 record 为 `owner-activation-decision.json`，decision ID
`mcp-act-2026-07-31-leiwenjun`。
