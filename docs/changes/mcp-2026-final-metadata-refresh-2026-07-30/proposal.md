# 变更提案：mcp-2026-final-metadata-refresh-2026-07-30

## 问题陈述（单问题）

既有 `mcp-2026-compat-staging` 仍把 `2026-07-28-rc` 记录为未发布候选。MCP
`2026-07-28` final 已发布，若继续保留 RC/未来事实，来源 freshness 与 staging metadata
将失真；但 final 发布不等于 ADK 已完成兼容验证，更不授权 runtime 激活。

## Owner Decision

- candidate：`epc-c6f947d482aa8aa0c78f`
- decision：`ENHANCE`
- owner：`leiwenjun`
- reviewed_at：`2026-07-30`
- decision ledger：`reports/external-practice-targeted-decisions-2026-07-30.jsonl`
- target：`manifests/skill_mcp_dependencies.json`

## 上下文充分性检查

- [x] final tag、tag commit、release 状态与检索日期已有本地 evidence。
- [x] active/candidate/activation/rollback 的既有 contract 已定位。
- [x] owner 明确了目标、非目标和四项 activation prerequisites。
- [x] 验证命令、回退和许可证边界可审查。

## 目标

- 把 MCP candidate provenance 从 RC 刷新到不可变 final tag `2026-07-28` 和 tag
  commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`。
- 保持 active protocol 为 `2025-11-25`。
- 将 candidate 标记为 `released`，同时保持 `runtime_enabled=false`、
  `final_compatibility_claim=false`。
- 显式记录 Tasks、Apps、extensions 均为 disabled。
- 保留 schema fixture、version-pinned client/server smoke、auth boundary review 和 rollback
  smoke 四项 activation blockers。

## 非目标

- 不切换 active protocol，不迁移 MCP server 或 target runtime 配置。
- 不启用 Tasks、Apps、extensions、remote server、network discovery 或 OAuth flow。
- 不复制上游 specification、SDK code 或其他混合许可证内容。
- 不把来源已取回表述成 schema/client/server/auth/rollback 已验证。
- 不安装、发布、source-to-live apply、commit 或 push。

## Core/Optional 边界检查

- compatibility provenance 与 fail-closed activation gate 属于 core 治理 metadata。
- Tasks、Apps、extensions 和任何 runtime adapter 均不进入 core 或 optional install surface。
- 本 change 不创建新资产类型，只增强既有 manifest/checker/test。

## 变更重复性检查

- 已检索既有 `mcp-2026-compat-staging` archive、两个 MCP manifest、ecosystem checker 和
  fixtures。
- 结论：只能 `ENHANCE` 现有 contract；不新增第二套 validator、Skill 或 Workflow。

## Source、许可证与权限边界

- source：`https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28`
- tag commit：`5f5440bb26a62e2cf3440b92da5a667efa03b267`
- transport：公开 GitHub release/repository metadata，只读。
- license boundary：新 code/spec contributions 为 Apache-2.0，未完成 relicensing 的旧贡献为
  MIT，非 specification 文档为 CC-BY-4.0；本 change 只记录 metadata，不复制内容。
- deny-path：外部代码执行、clone/install、凭证、网络写入、runtime enablement。

## 完成标准

1. owner decision 通过 `external-practice-decision/v1` 校验。
2. final source、candidate 和 activation state 在现有两个 manifest 中一致。
3. checker 和正负 fixture 阻止 active protocol 漂移、runtime/Tasks/Apps/extensions 启用、
   compatibility claim 以及未完成 activation evidence 时的 promotion。
4. 定向 ecosystem、strict validation 和完整回归通过。
5. adoption matrix 只记录 metadata ENHANCE，不写成 runtime adoption 或兼容认证。

## Breaking Change 检查

- [x] 否。active protocol、runtime、auth baseline 和安装范围均不变。
- [ ] 是。涉及 runtime/API/安装迁移。
- 回退：恢复 RC source/candidate metadata；active `2025-11-25` 不受影响。若 final metadata
  有误，checker 应 fail closed，而不是启用兼容层。

## Spec 链路检查

- requirements：owner decision ledger 与本 proposal。
- design：本 change `design.md`。
- tasks：本 change `tasks.md`。
- verify/review：完成实现后写入 `verify-report.md` 与 `review-report.md`。

## 安装范围与依赖边界

- install scope：`none-method-only`。
- 依赖：现有 JSON manifest、checker、fixture 和 shell test；不增加 package、runtime、MCP
  server、网络或凭证。

## Prompt 回归证据计划

- 不修改 Agent/Skill prompt。
- before/after 只比较 manifest/checker 行为：RC future fact → final released fact，同时
  runtime/feature/compatibility/activation 仍 fail closed。

## 收敛模式与退出条件

- 当前模式：build。
- 退出条件：decision、change governance、定向测试、strict、双 Python full parity、adoption
  consistency 和最终 review 全部有证据；activation blockers 保持未完成。
