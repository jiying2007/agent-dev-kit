# Runbooks：按需阅读

本索引只提供高频入口，不复制所有 Runbook、正式 Workflow 或当前版本的第二份目录。通常先读 [Usage](../usage.md)；只有任务需要相应深度时再读下列专题。

| 场景 | Runbook | 主要边界 |
| --- | --- | --- |
| 规格驱动与跨 SoC/MCU 变更 | [SDD 最小路径](spec-driven-delivery.md) | 唯一规格、双向验收，不为小修过度设计 |
| Goal / 长任务恢复 | [计划执行](planning-execution-loop.md) | 保留完成证据、恢复点和用户授权 |
| 问题修复与回归 | [Bugfix](bugfix-delivery.md) | 复现、根因、定向修复 |
| 目标运行时验证 | [Native Campaign](native-campaign.md) | static / smoke / native / certified 不混淆 |
| 发布与日常仓库维护 | [维护指南](workspace-maintenance-guide.md) | 精确 HEAD、CI、回滚和不可变 Release |
| 外部 Skill / 方法引入 | [Skill 策展](skill-curation-delivery.md) | 真实方法、来源风险、触发效果与归属 |
| 安装、密钥与依赖安全 | [供应链审查](security-supply-chain.md) | 不自动扩大权限 |
| 外部 MCP 工具 | [MCP 治理](mcp-governance.md) | 来源、最小权限和启用证据 |
| 真实交付证据 | [Task Evidence](task-evidence.md) | 原始结果指针与不完整/失败语义 |

全部已有资产身份看根目录 `manifest.json`、[Skill 目录](../agent-skill-catalog.md)和[命令参考](../commands.md)。旧 `docs/changes/` 的实验、报告和原始日志只供追溯，不能自动提升当前运行时和产品资格。
