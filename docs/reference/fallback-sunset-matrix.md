# Fallback 下线矩阵退役说明

本控制面已于 2026-08-31 退役。ADK 运行路由只允许受信 ADK inventory、项目已声明 workflow 或 no-skill/needs-input，不再提供 Superpowers runtime fallback。

- 根工作区参考仓可继续用于只读 intake、差异分析和 provenance。
- 可执行 tombstone 已删除；本文件只保留退役事实与 provenance，不再维护能力行、评分、candidate 或 sunset 状态。
- 当前运行 footprint 由根工作区 `manifests/runtime_targets.json` 的 required/forbidden 声明检查。
- 当前 ADK 能力证据由 `scripts/pilot-readiness.sh`、路由回归和完整测试维护。
