# 变更提案：adk-v3-1-rc2-target-conformance

## 背景

- `3.1.0-rc.1` 已建立 manifest、Agent、Skill、Profile、Workflow、安装、回滚、评测和发布控制面。
- 终态成熟度审计确认 source/test 证据强于 runtime/field 证据，当前总体仍应保持 M3 release candidate。
- direct target 导出存在阻断性契约偏差：Claude Code Skill、OpenCode Agent/Skill 的原生路径不正确，三个 target 的 Skill 丢失必需 `description`，Hermes Agent 缺少可验证的原生发现契约，且 export/install 使用两套转换逻辑。

## 问题陈述（单问题）

建立一套 versioned、可验证、export/install 共用的 direct target adapter，使每个支持的资产在目标运行时约定路径中具有完整 frontmatter、稳定权限映射、可回滚安装语义和可机械检查的发现/加载/触发证据入口。

## goal_statement

将 ADK 从“能够生成 direct target 文件”提升为“能够证明静态 target contract 正确，并为真实 runtime smoke 提供不可伪造的控制面”，形成 `3.1.0-rc.2` 候选证据；不提前宣称 M4/M5。

## 范围

- versioned `TargetContract` 与统一 `TargetAdapter` registry。
- Claude Code、OpenCode 的 Agent/Skill 原生树；Hermes 的 Skill-only 原生树。
- export/install 共用同一 renderer，支持 Skill support directories，禁止越界和符号链接输入。
- install plan v2、receipt v3、export manifest v2；保留旧 receipt rollback 读取，拒绝旧 plan apply。
- `target check/smoke`、`--asset-kind`、稳定 exit/error contract。
- Draft 2020-12 manifest schema 的真实执行与 `3.1.0-rc.2` 版本、迁移、回滚证据。
- static/golden/negative smoke、clean-clone/static-analysis/security/provenance/performance/eval 控制面能够在无外部凭证时执行的部分。

## 非目标

- 不代替 Claude/OpenCode/Hermes 官方运行时完成认证，也不伪造 discovery/load/trigger 结果。
- 不自动登录、执行付费 720-run campaign、邀请第二操作者、制造 30 天现场记录。
- 不 commit、push、tag、发布或 apply 到 `~/.codex`。
- 不把 Claude Agent SDK、OpenAI Agents SDK 或任一 runtime SDK引入 platform-neutral core。
- 不修改 dirty reference subrepos。

## 成功标准

1. 三个 target 的静态 contract/golden tree/frontmatter 检查通过；Hermes Agent 在写入前稳定失败且不产生部分输出。
2. export/install 对同一请求产生相同相对路径与内容 hash；Skill support files 可复现复制。
3. install 只接受 `copy`；`symlink` 以 usage/contract exit 2 拒绝；v2 plan 可 apply，v1 plan 被拒绝；v1/v2 receipt 仍可 rollback。
4. manifest schema 由 `jsonschema==4.23.0` 实际执行，覆盖全部顶层键并拒绝未知顶层属性。
5. 新增行为具有 normal/boundary/error 测试；至少保存一个预期负结果。
6. ADK strict/full、根仓 quick/full 和完成前门禁通过，或将真实失败记录为 blocker。

## completion_claim

- claimant：Codex（实现与证据整理）。
- verifier：`adk-verification-before-completion` 门禁及仓库自动测试；外部 runtime/field 证据必须由真实 operator/runtime 产生。
- required_evidence：target contract check、golden tree、installer migration/rollback、schema negative、ADK full、root full、release check/rehearsal、证据索引。
- open_items：任何未认证 runtime、第二操作者、独立 repo、720-run 或 30 天观察均保持显式 blocker，不得折算为完成。

## Breaking Change 检查

- direct target 输出树和 frontmatter 为有意修正；旧 export tree 不继续兼容。
- install plan 从 v1 升到 v2，旧 plan 必须重新生成；receipt v1/v2 仅用于 rollback 兼容。
- Hermes Agent 从“生成未证实目录”改为明确 unsupported。
- 迁移与回滚详见 `design.md`；版本固定在 prerelease `3.1.0-rc.2`。

## 风险与边界

- 目标官方契约可能变化：contract 固定 source URL、retrieved/expires 时间和 `experimental` 状态；过期后阻断提升 stable。
- 共享 renderer 影响面大：先补 contract tests，再逐层替换 compiler/installer；单一假设最多重试两轮。
- 安装目标含用户数据：只在测试临时目录 apply；真实 target root 需要用户显式命令。
- 外部认证不可本地重现：提供 `runtime-command` smoke 入口和 append-only 结果，但不将 `not-run` 当 pass。

## 上下文充分性检查

- [x] 输入、输出、错误、版本、迁移和验证命令已定义。
- [x] 已检查 `compiler.py`、`installer.py`、`manifest.schema.json`、legacy install/convert tests 与 rc.1 change artifact。
- [x] ADK 预期 lessons 文件不存在，已记录为负结果；没有重复执行旧方案。
- [x] capability 属于 platform-neutral core，target-specific 数据放入 versioned contract。

## Core/Optional 边界检查

- TargetContract registry、renderer、transaction 和 schema validation 属于平台中立 core。
- Claude Code、OpenCode、Hermes 的路径/frontmatter/permission 映射仅存在于 versioned target contract，不把 vendor SDK 引入 core。
- Claude Agent SDK、OpenAI Agents SDK、付费 campaign 和真实 runtime harness 均不作为 core 依赖或默认能力。

## 变更重复性检查

- 已对照 rc.1 compiler/installer 双实现、legacy wrapper 和现有 change artifact；本次合并重复 renderer，而非增加第三套转换器。
- `official_docs_freshness_gates.json` 继续作为统一资料治理入口，Anthropic 不另建旁路 manifest。
- performance/effect eval 复用现有 `devkit.sh` CLI 分组和 release evidence exclusion 机制。

## Spec 链路检查

- manifest schema 使用 Draft 2020-12；target contract 使用独立 `adk-target-contract/v1` schema。
- Claude Code、OpenCode、Hermes contract 固定官方 source URL、retrieved/expires 和 review status。
- static contract 只证明 rendered tree；runtime stage 必须由 caller-supplied harness 产生，`not-run` 不可提升为 pass。

## 安装范围与依赖边界

- 本次只在临时 target roots 执行 install/apply/rollback 测试，不写用户 live roots。
- core 新增固定依赖 `jsonschema==4.23.0`；Ruff、pip-audit、Scorecard 和 attestation 仅属于 CI/release 外部门禁。
- install 仅支持 `copy`；plan/apply 绑定 manifest/contract/content digest，并在锁内完成 staging/replace/rollback。

## Prompt 回归证据计划

- 本变更不修改 Agent/Skill prompt 主体；回归重点是 frontmatter、路径、permission metadata 和 routing contracts。
- 24 个输入/标签分离的 OOD/adversarial fixtures 验证 route/safety/trace/outcome，并以禁用 `routing.intents` 作为消融对照。
- target golden tree 与 fake runtime smoke 覆盖发现契约；真实 runtime prompt 试验留给外部认证 campaign。

## 收敛模式与退出条件

- 本地退出条件：ADK strict/full、target static、schema negatives、effect/performance、static/security/release checks 通过。
- 外部退出条件：真实 runtime 认证、remote CI/attestation、commit 后 root lock sync、双 runtime/第二操作者/30 天 field evidence。
- 本地条件通过而外部条件未完成时，状态只能是 `local-pass-external-blocked`，不得宣称 M4/M5 或 stable target。
