# 官方来源复核：2026-10-13

现有 OpenCode、OWASP 和五项 Anthropic 来源声明已过期，阻断 ADK 与 root 集成验证。本 change 仅复核既有采纳范围及来源有效期；不扩大运行时、原生认证或产品发布资格。

## Canonical Change Contract

| Requirement | Delta | Affected Surface | Acceptance | Task | Verification | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | MODIFIED | target-contracts/opencode.json | ACC-001 官方依据仍支持现有静态契约 | TASK-001 | VERIFY-001 | source-review.md |
| REQ-002 | MODIFIED | external_agent_pattern_contracts.json | ACC-002 ASI 分类仍支持 method-only 采纳 | TASK-001 | VERIFY-001 | source-review.md |
| REQ-003 | MODIFIED | official_docs_freshness_gates.json | ACC-003 五项官方采纳依据实际复核且差异明确 | TASK-001 | VERIFY-001 | source-review.md |
| REQ-004 | ADDED | docs/changes/official-source-refresh-20261013 | ACC-004 回归及独立审查闭环 | TASK-002 | VERIFY-002 | verify-report.md |
| REQ-005 | MODIFIED | 七项 source version 投影与 CHANGELOG.md | ACC-005 8.0.6 同步且严格高于 exact base | TASK-003 | VERIFY-003 | verify-report.md |

默认只改 ADK 单仓；root 的失败测试候选保留。基线 ef5384305421700ca01e89b3df3b3f7878a70265，隔离分支 codex/official-source-refresh-20261013。用户此前全部授权包含源码及 SCM；没有模型调用、live apply 或 human owner 代签。
