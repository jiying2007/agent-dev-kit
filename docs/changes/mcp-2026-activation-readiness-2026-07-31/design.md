# 设计：mcp-2026-activation-readiness-2026-07-31

## 架构决策

保持 `skill_mcp_dependencies.json` 为 MCP compatibility SSOT。新增一个 opt-in 的
version-pinned Go fixture 和一个稳定 wrapper；静态 ecosystem checker 负责状态一致性，
真实 fixture 负责行为证据。二者均通过后才允许把四项 technical prerequisite 标为完成。

## 状态模型

```text
final source retrieved
        |
fixed SDK + fixed image + offline loopback smoke
        |
schema + client/server + auth + rollback = completed
        |
final_compatibility_claim = true (scoped evidence only)
        |
owner_decision_required = true
owner_decision_completed = false
activation_allowed = false
runtime_enabled = false
        |
independent owner ACTIVATE / HOLD / REJECT
        |
ACTIVATE => active_protocol_version = 2026-07-28
            active_scope = protocol-governance-contract-only
            runtime/features remain false
```

`final_compatibility_claim` 不再表示“没有测试”，但必须与 `compatibility_scope` 和不可变
evidence identity 一起读取。它不授权 active/runtime 切换。

## Fixture 设计

### 固定依赖

- Go toolchain image：
  `docker.io/library/golang:1.25.1-bookworm@sha256:c423747fbd96fd8f0b1102d947f51f9b266060217478e5f9bf86f145969562ee`
- SDK：`github.com/modelcontextprotocol/go-sdk v1.7.0-pre.3`
- SDK tag commit：`827f90ba0c13edb546028df42fadc9f1211a4ff2`
- `go.sum` 作为 module artifact checksum 证据。

### 执行分层

1. `--prepare`：在固定 image 中下载 `go.sum` 已约束的 modules 到显式 `/tmp` cache。
2. `--offline`：同一 image digest，`--network=none`，fixture 只读挂载，cache 只读挂载，
   build cache 写入 `/tmp`；执行 `go test -count=1 -json`。
3. wrapper 再验证 manifest readiness state，防止行为测试与治理状态脱节。

### Schema compatibility

- input/output schema 显式声明
  `https://json-schema.org/draft/2020-12/schema`。
- 正例：合法 input 产生与 output schema 一致的 structured content。
- 负例：缺少 required input、错误 input type、错误 output type 均 fail closed。
- schema 由 SDK 注册、解析与 handler 前后验证，不能只做 JSON 文本比较。

### Version-pinned client/server

- server：`StreamableHTTPOptions{Stateless:true, JSONResponse:true}`。
- client：固定 SDK 的默认 modern discovery；结果必须精确为 `2026-07-28`。
- 证明 `server/discover -> tools/list -> tools/call` 可用。
- 捕获并验证 `Mcp-Protocol-Version`、`Mcp-Method`，现代 stateless 请求不得携带
  `Mcp-Session-Id`。

### Auth boundary

- 使用 SDK `auth.RequireBearerToken` 包装同一个 MCP HTTP handler。
- verifier 对合成 claims 强制 issuer、audience、expiry；middleware 强制 scopes。
- 负例：
  - missing token → 401；
  - wrong issuer → 401；
  - wrong audience/resource → 401；
  - insufficient scope → 403。
- 正例：valid token 可完成 modern client/server call。
- 下游由本地 `httptest` 表示；收到任何 `Authorization` 即测试失败，响应/日志也不得包含
  token。

### Rollback

- candidate server smoke 完成后启动 legacy stateful handler。
- 同一固定 SDK client 必须从 discover 回退并协商 `2025-11-25`，list/call 可用。
- `server/discover` 可以响应，但 `supportedVersions` 必须排除 `2026-07-28` 并包含
  `2025-11-25`；随后精确 modern `tools/list` 必须被拒绝。
- manifest 仍以 `2025-11-25` 为 active，fixture 全程只读，不修改 repo/runtime。

## Evidence contract

candidate 增加：

- `compatibility_scope`
- `compatibility_evidence.sdk_module/sdk_version/sdk_revision/sdk_sum`
- `compatibility_evidence.runtime_image/runtime_image_digest`
- `compatibility_evidence.transport/network_mode/verified_at/evidence_path`

activation gate 增加：

- `owner_decision_required=true`
- `owner_decision_completed=false`
- `owner_decision_id=null`

四项 completed 可以为 true，但只要 owner decision 未完成，`activation_allowed` 必须 false。
owner 选择 `ACTIVATE` 后，manifest 必须记录 decision ID/path、active scope、完成日期和
rollback target，同时继续断言 runtime 与三个 feature flags 为 false。

## 权限、日志与回退

- prepare 阶段不接触 credential；offline 阶段禁止外网。
- 工件只记录固定版本、digest、测试名称、退出码和状态；不记录 bearer token。
- 任何测试失败均保持 active/runtime/activation 不变。
- ACTIVATE 也不自动启用 Tasks/Apps/extensions；它们需要独立 feature decision。

## 已知限制

- SDK 为 pre-release，证据仅绑定 `v1.7.0-pre.3`，不是稳定版承诺。
- loopback smoke 不覆盖反向代理、真实 IdP、跨实现矩阵、负载和长时稳定性。
- 新 SDK/tag 或生产部署前必须重跑并形成新的 evidence identity。

## 已执行决策

- decision：`ACTIVATE`
- owner：`leiwenjun`
- decision ID：`mcp-act-2026-07-31-leiwenjun`
- active：`2026-07-28` governance contract only
- disabled：runtime、Tasks、Apps、extensions
- rollback target：`2025-11-25`
