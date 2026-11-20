# 第三方编程工具速查：历史快照说明

此文档原是一份 **2026-04** 的 9 款编程工具对照表，含当时的模型、价格、上下文窗口、快捷键与安装命令。多数属于**随版本/地区/套餐变化的外部事实**，不应继续作为 ADK 当前官方指南或能力选择依据。

原始完整快照仍可通过 [2026-11-20 之前的固定源码版本](https://github.com/jiying2007/agent-dev-kit/blob/2aa49df24eeb7db20278f49c6d8056738bf18313/docs/reference/tool-cheatsheet.md) 审阅；保留历史证据，不在当前维护入口重复复制可能过时的市场数据。

## 当前唯一有效的判断方式

- **ADK 支持什么**：查仓库根目录 `manifest.json` 的 `tool_targets`、`external_handoff_targets` 与 `profiles`；外部工具名不等于 ADK 运行时认证。
- **如何选择和运行 Skill**：按 [使用指南](../usage.md) 及 [Workflow/Skill 边界](../workflows.md) 选已有能力。
- **能否导出或安装**：按 [命令参考](../commands.md) 执行当前源码的 plan / check；实机或第三方 CLI 必须另做 native 验证。
- **外部工具标准、变化与权限**：按 [互操作边界](../architecture/interoperability-boundaries.md) 和 [官方资料治理](../runbooks/official-docs-governance.md) 获取有日期、来源和有效期的依据。

避免从历史表格直接推导当下的价格、最大上下文、地域可用性、免费额度、配置路径或产品排名。任何新的外部工具吸收，必须先有可信来源、明确适用边界和真实使用效果证据；不靠一份速查表扩充 ADK Runtime。
