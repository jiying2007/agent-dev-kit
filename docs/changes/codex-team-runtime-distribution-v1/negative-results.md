# Negative Results

| Attempt | Result | Decision |
| --- | --- | --- |
| 团队仓安全解包首次 smoke | `mkdtemp` 已创建目录，而解包器要求目录不存在，导入在校验前失败 | 调整为只接受“已存在但为空”的内部临时目录，并增加端到端测试 |
| bundle rollback 后复用 `build/bundle-import-plan.json` | `build` 完整重建并删除旧 plan | Bundle import plan 改放 `.cache/`，明确 30 分钟、一次性语义 |
| ADK strict / quick shared gate | 三个既有 source_ref review 到期：`github-gh-aw-safe-outputs`、`mcp-registry`、`otel-genai-semconv` | 记录为既有 freshness 阻断；不篡改日期、不把失败记为通过，本 change 继续使用定向与其他共享门禁取证 |
| ADK full suite | 51/59；7 项由上述 freshness 共同阻断，`test_asset_content_quality` 另被既有 `adk-code-review-loop` 缺 Commands/Evidence Template 阻断 | 与本次 Runtime Bundle diff 分开归因；不扩大范围修复无关 Skill |
| Python 3.11/3.12 Docker parity | wheel build、安装、doctor 均通过，最终 matrix 被上述 freshness 阻断 | 只声明支持版本加载证据，不声明 release gate pass |
