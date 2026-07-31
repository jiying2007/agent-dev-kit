# 验证报告：mcp-2026-activation-readiness-2026-07-31

## 结论

MCP `2026-07-28` 的四项技术前置条件已在固定 Go SDK、固定容器镜像和离线
loopback 边界内通过。独立 owner 已选择 `ACTIVATE`，当前只激活协议治理契约：

- active protocol：`2026-07-28`
- active scope：`protocol-governance-contract-only`
- runtime：disabled
- Tasks / Apps / extensions：disabled
- owner activation decision：`mcp-act-2026-07-31-leiwenjun`
- rollback target：`2025-11-25`

兼容性结论只适用于
`go-sdk v1.7.0-pre.3 + JSON Schema 2020-12 + stateless Streamable HTTP +
本地 auth boundary + legacy rollback`，不能外推为跨 SDK、真实 IdP、反向代理或生产负载认证。

## 不可变验证身份

| 项目 | 固定值 |
|---|---|
| Protocol final tag | `2026-07-28` |
| Protocol tag commit | `5f5440bb26a62e2cf3440b92da5a667efa03b267` |
| Go SDK module | `github.com/modelcontextprotocol/go-sdk v1.7.0-pre.3` |
| Go SDK tag commit | `827f90ba0c13edb546028df42fadc9f1211a4ff2` |
| Go SDK module sum | `h1:SEAY9IduDif4iApnZgpFkjFIdo3askSGZVbZIYyTy6I=` |
| Go SDK go.mod sum | `h1:dL7u98E/zjJTGzEq+j30jQ8K2k1mb6LeAH4inEcSGts=` |
| Go image | `docker.io/library/golang:1.25.1-bookworm@sha256:c423747fbd96fd8f0b1102d947f51f9b266060217478e5f9bf86f145969562ee` |
| Smoke network | Docker `--network=none`，容器内 loopback |

## 四项前置条件

| Requirement | Test | Positive evidence | Negative evidence | Verdict |
|---|---|---|---|---|
| Schema compatibility fixture | `TestSchemaCompatibilityFixture` | 合法 input/output 和 structured output 通过 | missing required、wrong input type、wrong output type 均 fail closed | PASS |
| Version-pinned client/server smoke | `TestVersionPinnedClientServerSmoke` | discover/list/call 通过并精确协商 `2026-07-28` | header/session 断言防止协议形态漂移 | PASS |
| Auth boundary verification | `TestAuthBoundaryVerification` | 合法 synthetic bearer 可完成 call | missing、issuer、audience、scope、expiry 均拒绝；token 不下传、不回显 | PASS |
| Rollback smoke | `TestRollbackSmoke` | stateful legacy list/call 通过并协商 `2025-11-25` | discover 不声明 modern；modern `tools/list` 返回 HTTP 400 | PASS |

## 命令级证据

| Command | Exit | Result | Evidence |
|---|---:|---|---|
| `rtk scripts/check-mcp-2026-activation.sh --prepare` | 0 | 固定 module/checksum cache 准备成功 | `/tmp/adk-mcp-2026-activation-cache/` |
| `rtk scripts/check-mcp-2026-activation.sh --offline` | 0 | 四个 Go 行为测试、owner record 和治理激活状态一并通过 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` |
| `rtk scripts/check-agent-ecosystem-standards.sh --summary-json` | 0 | 545 checks；13 negative fixtures；runtime disabled | command output |
| `rtk tests/test_agent_ecosystem_standards.sh` | 0 | ecosystem 正负 fixture 回归通过 | command output |
| `rtk python3 -c '<decision schema validation>'` | 0 | owner ACTIVATE record 通过 JSON Schema 2020-12 与 date format 检查 | `owner-activation-decision.json` |
| `rtk scripts/check-change-governance.sh docs/changes/mcp-2026-activation-readiness-2026-07-31` | 0 | change governance 通过 | command output |
| `rtk scripts/devkit.sh validate --strict` | 0 | strict validation 通过；host Python 3.8 warning 不作为 release 证据 | command output |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full` | 0 | Python 3.11/3.12 各 57/57，routing 各 30/30，dependency audit 无已知漏洞 | parity output |
| `rtk scripts/check-format.sh` | 0 | format gate 通过 | command output |
| `rtk tests/test_file_modes.sh` | 0 | file mode gate 通过 | command output |
| `rtk tests/test_product_maturity_v3.sh` | 0 | product maturity gate 通过 | command output |
| `rtk git diff --check` | 0 | 无 whitespace error | command output |

首次 full parity 对 synthetic bearer 命名产生 `quality.SECRET_CONTENT` 真阳性，随后缩短
opaque fixture 值并保留全部 auth 负例语义。完整试错链见 `negative-results.md`。

## 根工作区聚合门禁

根工作区 `scripts/check-all.sh --quick` 当前为 49/54。五项失败均已归因到本 change
范围外的既有治理状态：

1. current-status 已过期，并存在 ADK gitlink/lock/worktree commit 不一致；
2. practice intake 的 removal-plan artifact hash 过期；
3. 3 个外部参考仓的 dirty triage baseline 于 2026-07-30 过期；
4. reference removal check 读取同一过期 hash；
5. subrepo state 同时报告上述过期 baseline 与本次 ADK 合法 dirty 变更。

这些失败不否定四项固定范围内的 MCP 行为证据，但意味着不能声称整个 `llm_agent`
工作区全绿或可合并。

## Claimant、verifier 与剩余风险

- claimant / implementer：Codex 当前会话。
- deterministic verifier：Go 行为测试、ecosystem negative fixture、ADK strict/full gates。
- independent activation owner：`leiwenjun`，已签署 `ACTIVATE`。
- blocker/major implementation finding：0。
- activation blocker：0。
- residual risk：Go SDK 仍为 pre-release；未覆盖真实 IdP、反向代理、跨 SDK 组合、并发、
  长时运行或生产 rollout。

## 已执行的 Owner 决策

- decision：`ACTIVATE`
- decision ID：`mcp-act-2026-07-31-leiwenjun`
- record：`owner-activation-decision.json`
- scope：只激活 `2026-07-28` protocol governance contract。
- retained deny boundary：runtime、Tasks、Apps、extensions 全部 false。
- rollback：恢复 `2025-11-25` governance contract，保持 runtime/features disabled。
