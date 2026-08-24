# Verification Evidence

- Source transport：official web read-only；manual helper cache unavailable，Docs MCP unavailable，按
  openai-docs skill 回退到 `developers.openai.com` 原 URL。
- Coverage：27/27 URL 可访问；Skills/Agents/tracing/evals/reasoning/plugin review/requirements/
  sandbox/rules/security/MCP/app-server/session/docs-MCP/Responses/hooks/slash/plugin/skills/tools/
  developer-mode/MCP safety/macro-evals 的关键语义均找到。
- Redirect：部分 Codex URL 到 ChatGPT Learn，Apps SDK submission 到 Plugins；稳定原 URL 仍有效。
- Data diff：仅 27 条 retrieved/expires 从 2026-05-25/2026-08-23 更新为
  2026-08-24/2026-11-22；decision/status/owner 不变。

| Command | Exit | Result |
|---|---:|---|
| refreshed/expired jq assertions | 0 | refreshed=27，expired=0 |
| `test_official_docs_governance.sh` | 0 | official governance pass |
| host strict | 0 | strict pass |

- Final：Python 3.11 source `268dc95b…`，63/63、strict/targets/routing/dependency audit pass。
