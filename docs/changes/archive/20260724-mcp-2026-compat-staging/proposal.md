# 变更提案：mcp-2026-compat-staging

## 背景
- MCP 官方公告预告 2026-07-28 版本将涉及 stateless core、extensions、Tasks、Apps、授权加固、弃用、JSON Schema 2020-12、`Mcp-Method` 和 `ttlMs`。
- 当前日期为 2026-07-23，最终规范尚未到公告发布时间；现有 ADK 只记录 MCP dependency provenance 和 OAuth/resource 边界，缺少 protocol-version/capability/弃用/rollback contract。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：在不把 RC 当正式标准、不启用新 runtime 的前提下，建立可审计的 MCP 版本兼容预备门禁。
- 触发证据：`skill_mcp_dependencies.json` 没有 `protocol_version`、`extension_ids`、`deprecated_features`、`compatibility_test` 和 `rollback` 字段。

## 目标
- 固定当前 active protocol 为 2025-11-25。
- 把 2026-07-28 RC 记录为 watch candidate，`runtime_enabled=false`。
- 新增 capability、extension、deprecated feature、auth profile、compatibility test 和 rollback 必填字段。
- 增加正负 fixture，确保 watch candidate 不能误启用 runtime 或声称 final compatibility。

## 非目标
- 不声明 2026-07-28 final 已发布。
- 不启用 Tasks、Apps、extension、网络发现或 remote MCP server。
- 不迁移现有 MCP server，不修改 target runtime 配置，不放宽 OAuth/least-privilege 门禁。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别规范未发布、breaking change、auth 和 rollback 风险
- [x] 已明确验证命令与通过标准
- [x] 最终规范差异保留为 2026-07-28 后的独立复核

## Core/Optional 边界检查
- [x] 兼容与安全门禁属于 core
- [x] 新协议能力属于 optional/disabled
- 归属结论：只扩展平台中立治理 contract；不加入 runtime transport。

## 变更重复性检查
- 已检索 `skill_mcp_dependencies.json`、Agent ecosystem standards gate 和现有 MCP provenance fixture。
- 本次复用现有 standards checker，不创建第二套 MCP validator。

## Breaking Change 检查
- [x] 否：active protocol 保持 2025-11-25，新字段只约束未来 activation
- [ ] 是：涉及兼容性破坏

## Spec 链路检查
- requirements 基线：本提案和外部实践候选报告 3.8 节。
- design 决策：本 change `design.md`。
- tasks 追溯关系：本 change `tasks.md`。

## 安装范围与依赖边界
- 安装范围：global-ready method-only contract。
- 依赖边界：JSON manifest、现有 checker/fixture；不新增包、网络或凭证。

## Prompt 回归证据计划
- 不修改 prompt。
- 负例保留：watch candidate `runtime_enabled=true`、缺 rollback、把 RC 标为 final、缺 auth profile。

## 收敛模式与退出条件
- 当前模式：planning。
- 退出条件：manifest、source provenance、正负 fixture 和 ecosystem gate 通过；状态仍为 watch。

## 备选方案与取舍
- 方案 A：等待 final 后再做任何准备。
- 方案 B：现在建立 disabled staging contract，final 后只更新版本/差异和 compatibility evidence。
- 选择 B：提前补 fail-closed 数据结构，同时避免预判最终规范。

## 风险与回退
- 风险：RC 字段变化、误把 watch 当兼容、auth 语义漂移。
- 回退：移除 watch entry 和新增 fixture；active protocol/现有 dependency provenance 不变。
