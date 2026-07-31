# 变更提案：official-model-catalog-freshness-2026-07-30

## 问题

`openai-latest-model-gpt-5-5` 的 freshness 窗口已于 2026-07-27 过期，导致 official docs governance 和 strict validation 失败。该 source ID 已被 adoption 记录引用，不能为了追随易变模型名称静默重命名；同时也不能在未复核官方来源时单纯延长日期。

## 目标

- 只使用 OpenAI 官方 Models 与 Model guidance 页面复核当前事实。
- 保留稳定 source ID，更新易变标题、复核日期、expiry 和明确的 `update` 决策。
- 记录 GPT-5.5 已不是当前首选模型家族，但不把 GPT-5.6 写成 ADK 的持久默认值。
- 恢复 official docs governance、strict validation 和 Python 3.11/3.12 parity 验证。

## 非目标

- 不迁移任何 API 调用、模型默认值、prompt、价格表或历史基线。
- 不启用 OpenAI API、外部 runtime、MCP 写操作或凭证。
- 不把当前模型目录的易变事实提升为长期平台中立合同。

## Source 与权限边界

- primary：`https://developers.openai.com/api/docs/models`
- supporting：`https://developers.openai.com/api/docs/guides/latest-model`
- transport：OpenAI Docs MCP 优先；当前线程缺少该工具时使用仅限 `developers.openai.com` 的 Web fallback。
- 权限：公开文档只读；不提交表单、不登录、不执行远端代码。

## 完成标准

1. freshness 记录明确 `update`，窗口不超过 90 天。
2. official docs governance 和定向测试通过。
3. strict validation 在受支持 Python 3.11/3.12 parity 环境通过。
4. 任何模型选择仍要求 workload eval，不把目录快照当作默认模型授权。
