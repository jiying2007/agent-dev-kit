# 变更提案：mcp-2026-activation-readiness-2026-07-31

## 问题陈述（单问题）

MCP `2026-07-28` final metadata 已进入 compatibility staging，但 schema fixture、
version-pinned client/server smoke、auth boundary verification 与 rollback smoke 仍无
可执行证据。缺少这些证据时不能形成新的独立 owner activation decision。

## 上下文充分性检查

- [x] final tag、tag commit、现有 active/candidate/activation contract 已定位。
- [x] owner 指定了四项技术 prerequisite 和新的独立 activation decision。
- [x] 官方 Go SDK 的固定版本、tag commit、最低 Go 版本和 HTTP stateless 约束已核验。
- [x] Knowledge Hub exact-source 审计要求 source/version/environment 三者绑定。
- [x] 当前 dirty 变更已盘点，本 change 只触碰 MCP readiness 范围。

## 目标

1. 新增 JSON Schema 2020-12 input/output 正负 fixture，并通过真实 SDK handler 验证。
2. 使用固定 `github.com/modelcontextprotocol/go-sdk v1.7.0-pre.3` 完成
   `2026-07-28` stateless HTTP client/server discovery、list、call 和 header smoke。
3. 验证 missing/invalid issuer/invalid audience/insufficient scope 均 fail closed，并证明
   bearer token 不传给下游。
4. 验证 server 回退到 stateful legacy 配置后协商 `2025-11-25`，list/call 可用且
   discover 只声明 legacy versions、`2026-07-28` application request 被拒绝。
5. 把四项技术证据写入 manifest；在 owner decision 前保持 activation、runtime 和扩展
   关闭，在 schema-valid `ACTIVATE` 后只切换 protocol governance contract。
6. 生成一个新的独立 owner activation decision request，由 `leiwenjun` 选择
   `ACTIVATE`、`HOLD` 或 `REJECT`。

## 非目标

- 不代替 owner 签署决策，不把用户的“开始执行”解释为 `ACTIVATE`。
- 不在独立 owner decision 前切换 `active_protocol_version` 或启用 runtime。
- 不启用 Tasks、Apps、extensions，不增加 extension ID。
- 不连接真实 MCP server、OAuth issuer 或下游服务，不读取真实 token/credential。
- 不把单一 SDK 的本地 loopback smoke 表述成全生态或生产稳定性认证。
- 不安装到 `~/codex`/`~/.codex`，不发布、commit、push、merge 或 rebase。

## Core/Optional 边界检查

- compatibility fixture、证据 contract 和 fail-closed owner gate 属于 core 治理。
- Go SDK 只作为测试期固定依赖，不成为 ADK 安装资产或 runtime dependency。
- Tasks、Apps、extensions 继续不进入 core 或 optional install surface。

## 变更重复性检查

- 复用 `skill_mcp_dependencies.json`、`check-agent-ecosystem-standards.sh` 和既有 MCP
  staging contract。
- 不新增第二套 compatibility manifest、Skill 或 Workflow。
- 新增专用 smoke 入口是因为既有 checker 只能验证静态 metadata，不能提供真实
  schema/client-server/auth/rollback 证据。

## Source、许可证与权限边界

- specification source：tag `2026-07-28`，commit
  `5f5440bb26a62e2cf3440b92da5a667efa03b267`。
- SDK module：`github.com/modelcontextprotocol/go-sdk v1.7.0-pre.3`，tag commit
  `827f90ba0c13edb546028df42fadc9f1211a4ff2`。
- build image：`docker.io/library/golang:1.25.1-bookworm`，按 digest 固定。
- prepare transport：仅 Go module proxy/checksum 服务的公开只读依赖下载。
- smoke transport：Docker `--network=none`；容器内 `httptest` loopback。
- credential boundary：只允许源码内明确的合成 opaque token，不读取环境 credential。
- deny-path：真实服务、用户目录、runtime config、外部写操作、token 日志、宿主网络。
- license boundary：SDK 作为 module 测试依赖使用；不复制 specification/SDK 实现代码。

## 完成标准

1. 四个命名测试分别覆盖 schema、client/server、auth、rollback，至少一个预实现红灯与
   全部绿灯证据可审查。
2. `go.mod` 精确固定 SDK version，`go.sum` 固定 module checksum，Docker image 固定
   digest；offline smoke 不访问外网。
3. manifest 写明 compatibility scope、SDK/image identity、证据路径和四项 completed。
4. `final_compatibility_claim=true` 仅表示声明范围内证据通过；owner `ACTIVATE` 后
   `active_protocol_version=2026-07-28`，但 `active_runtime_enabled=false` 且三个 feature
   flags 继续 false。
5. 定向 ecosystem、strict 和完整回归通过，或对非本 change 失败给出原始证据和影响。
6. 生成独立 owner decision request；没有 owner 响应前不得把本 change 标为最终激活。

## Breaking Change 检查

- [x] 否。active protocol、runtime、安装与扩展表面均不变。
- [ ] 是。涉及 runtime/API/安装迁移。
- 回退：恢复 readiness evidence 字段为 pending；active `2025-11-25` 始终保留。

## Spec 链路检查

- requirements：用户本轮五项要求与本 proposal。
- design：本 change `design.md`。
- tasks：本 change `tasks.md`。
- verify/review：实现后写 `verify-report.md` 与 `review-report.md`。
- activation：独立 owner decision ledger，不能由技术验证隐式推导。

## 安装范围与依赖边界

- install scope：`none-test-only`。
- 固定 SDK/module/image 只用于验证；不修改 ADK 运行依赖、target 或 lockfile。
- module cache 和 build cache 只写入显式 `/tmp` 路径。

## Prompt 回归证据计划

- 不修改 Agent/Skill prompt。
- before/after 比较：四项 pending → scoped evidence complete → owner `ACTIVATE` 仅提升
  governance contract；runtime/features 始终 blocked。

## 收敛模式与退出条件

- 当前模式：build/test。
- 每阶段 retry budget：2；超出后停止并重审固定版本/API 假设。
- source/package staleness threshold：1 天；owner decision 前若越界需重取 metadata。
- 退出条件：技术 prerequisites 绿灯、形成 decision request、执行独立 owner 分支并复验。

## 执行结果

owner `leiwenjun` 已选择 `ACTIVATE`，decision ID
`mcp-act-2026-07-31-leiwenjun`。active protocol governance contract 已切换为
`2026-07-28`；runtime、Tasks、Apps、extensions 继续关闭。
