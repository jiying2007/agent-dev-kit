# Design

## Evidence decisions

- GitHub Safe Outputs：官方文档继续采用只读 agent、结构化输出与独立权限 job；新增记录其保守 `create-issue` 自动注入行为，本地仍要求显式输出边界。
- MCP Registry：官方仓说明 namespace ownership 验证机制；继续仅吸收 provenance 字段，不把 listing 当成信任或安装批准。
- OpenTelemetry GenAI：官方仓仍在演进，覆盖 MCP 和 provider conventions，Schema URL 尚未定型；继续使用可选、版本锁定映射并默认关闭敏感内容。

## Freshness contract

- `retrieved_at`: `2026-08-21`
- `expires_at`: `2026-09-20`
- `decision`: 保持 `adopt-method-only`

## Safety boundary

本 change 只修改治理元数据与说明，不下载、执行或发布任何上游代码，不扩大网络、SCM、MCP 或 telemetry 权限。
