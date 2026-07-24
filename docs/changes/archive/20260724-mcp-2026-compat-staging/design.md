# 设计说明：mcp-2026-compat-staging

## 架构影响
- 复用 `skill_mcp_dependencies.json` 作为 MCP 依赖与协议治理 SSOT。
- 复用 `check-agent-ecosystem-standards.sh` 和现有 fixture bundle，不新增 runtime 或 validator 入口。
- `external_agent_pattern_contracts.json` 增加官方 RC source/watch decision，确保 provenance 与 decision 可追溯。

## 数据与配置影响
- 新增 `protocol_compatibility_policy`：active protocol、candidate protocol、release status、capabilities、extension IDs、deprecated features、auth profile、compatibility tests、rollback 和 activation gate。
- active protocol 固定 `2025-11-25`；candidate 固定 `2026-07-28-rc`，`release_status=release-candidate`、`runtime_enabled=false`、`final_compatibility_claim=false`。
- positive fixture 证明 watch-only；negative fixture 覆盖 runtime enable、缺 rollback 和错误 final 声明。

## 兼容性与迁移方案
- 不改变现有 dependency provenance 或 OAuth/resource baseline。
- 2026-07-28 后必须重新检索最终规范，再单独更新 candidate version/status 和 compatibility evidence。
- 未完成 breaking-change diff、schema fixture、client/server smoke 和 rollback 前不能 promotion。

## 验证策略
- `rtk bash scripts/check-agent-ecosystem-standards.sh --summary-json`
- `rtk bash tests/test_agent_ecosystem_standards.sh`
- `rtk bash scripts/validate-assets.sh --strict`
- `rtk bash tests/run_all.sh --quick`
