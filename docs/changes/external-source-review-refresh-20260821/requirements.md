# Requirements

## Goal

恢复三个快速演进外部来源的复核新鲜度，使 ADK 治理门禁基于当前官方证据运行，而不是通过放宽到期检查绕过失败。

## Scope

- 复核 GitHub Agentic Workflows Safe Outputs、MCP Registry 和 OpenTelemetry GenAI Semantic Conventions 官方来源。
- 更新 `retrieved_at`、`expires_at` 与必要的边界说明。
- 保持既有 `adopt-method-only` 决策与默认 deny/write-disabled 策略。

## Non-goals

- 不导入上游实现、workflow、registry 条目或 telemetry payload。
- 不把 namespace ownership、registry listing 或 semantic convention 解释为安全认证。
- 不启用 GitHub 写权限、MCP 安装或 GenAI 敏感内容采集。

## Acceptance

- 三项来源均来自官方一手页面并记录 30 天复核窗口。
- strict、ecosystem、official-docs、workflow、SOP、memory 与 performance 相关门禁不再因这三项到期失败。
- 完整回归不存在由本 refresh 引入的 blocker/major。

## Rollback

回退本 change 的来源日期和说明；若官方页面不可访问或语义发生 breaking change，将对应来源改为 watch-only，而不是延长失真证据。
