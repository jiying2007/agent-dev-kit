# 设计：official-source-toolchain-refresh-20260830

## 来源刷新

- freshness manifest 显式声明治理日期基准为 `Asia/Hong_Kong` 固定
  `+08:00`；以该基准下的 `2026-08-30` 为本轮 retrieved/review 日期，
  expires 固定为 `2026-11-28`，不超过既有 90 天策略。
- checker 不读取宿主本地时区；Kiritimati、Adak 和 UTC 宿主得到相同治理日期。
  相对该治理日期的 future `retrieved_at` 仍 fail closed。
- source URL 保留 `developers.openai.com` canonical inventory 形式；若官方页面
  重定向到 `learn.chatgpt.com`，记录 redirect 漂移，但不扩展 gate 的 allowed
  domains，也不把运行时产品行为绑定进 ADK core。
- 每条来源在 `source-review.md` 记录 `unchanged`、`decision-updated` 或
  `watch-retained`。只有页面可达且核心结论仍成立才刷新日期。
- `codex mcp-server` 已由当日手册标为 deprecated；对应 multi-agent 来源继续
  `watch`，decision 改为新集成优先 App Server，旧 MCP 示例只作 legacy 参考。

## Python 入口

- 未设置 `ADK_PYTHON_BIN` 时按 `python3.12 -> python3.11 -> python3` 顺序选择；
  显式设置始终优先。
- 该顺序改善常见宿主上 `/usr/bin/python3` 较旧、但 3.11/3.12 已安装的情况，
  不修改 package 的 Python 3.11+ 支持声明。
- 若最终选择的解释器低于 3.11，保留 development-only warning；
  `ADK_REQUIRE_SUPPORTED_PYTHON=1` 继续在 CLI 执行前失败；`doctor` 继续可用。
- 不把宿主测试输出写成 Python 3.11/3.12 release evidence；正式证据仍来自受控
  local-CI parity。

## 回滚

- freshness 回滚：恢复本 change 前的日期与 decision，门禁会重新 fail closed。
- launcher 回滚：恢复默认 `python3`；`ADK_PYTHON_BIN` 显式选择合同不变。
