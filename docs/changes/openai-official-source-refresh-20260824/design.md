# 设计说明：openai-official-source-refresh-20260824

## 架构影响
- 无 runtime/architecture change；只更新 official freshness manifest。

## 数据与配置影响
- 27 条：`retrieved_at=2026-08-24`、`expires_at=2026-11-22`；90 天窗口。
- ID/title/url/review_status/adoption_scope/owner/decision/required_checks 不变。

## 兼容性与迁移方案
- JSON schema 不变；旧 consumer 无迁移。

## 验证策略
- official gate、strict、workflow fail-closed/workflow lifecycle、quick/full parity。
- 机械断言 refreshed=27、expired=0，review decisions 无变更。

## Evidence Groups

- Codex customization/security/config/rules/MCP/app-server/hooks/slash/plugin/skills/best-practices。
- Agents SDK/tracing/evals/session memory；Responses migration/reasoning/tools/MCP/developer mode。
- Plugin submission review hints；agentic macro eval regression promotion。
- Manual helper 两次因 cache unavailable 失败；Docs MCP 未安装；official web fallback 仅访问
  `developers.openai.com` 原 URL，redirect 作为页面现状记录。
