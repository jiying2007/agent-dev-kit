# 负结果：official-source-toolchain-refresh-20260830

| 时间 | 假设/操作 | 结果 | 决策 |
|---|---|---|---|
| 2026-08-30 | Codex manual helper 默认 `/tmp` 缓存可用 | `rtk node` 对 `/tmp` access 返回 EACCES | 改用仓库 ignored `.cache/openai-docs`，不写长期资产 |
| 2026-08-30 | 当前会话可立即使用新添加的 OpenAI Docs MCP | CLI 配置成功，但工具不会在当前会话热加载 | 回退到 OpenAI 官方域名逐页 open；不使用第三方页面 |
| 2026-08-30 | 28 条来源均无事实漂移 | Codex Agents SDK 页面明确标记 `codex mcp-server` deprecated | 更新该条 decision，保留 watch，不机械续期旧结论 |
| 2026-08-30 | UTC 日期可直接作为本地治理日 | 香港本地 8/30、UTC 8/29 时把本轮来源误判 future | manifest 显式声明固定 +08:00 基准；补跨 TZ 一致性和 future 负例 |
| 2026-08-30 | T3 完成后 strict/parity 应全绿 | Python 3.8 strict 及 3.11/3.12 isolated quick 均在共享 target schema 检查失败 | 保留失败；归因 `claude-code adapter` 缺失，等待主线修复后复跑 |
