# 需求与验收

- REQ-001 / ACC-001：读取 OpenCode agents 与 skills 官方文档，核对路径、frontmatter、mode、permission 和现有 implicit 调用。保持 experimental/static/not-certified。
- REQ-002 / ACC-002：核对 OWASP 官方 ASI01-ASI10 分类与已有本地 crosswalk；指南不可读时明确记录实际替代依据和限制。保持 method-only。
- REQ-003 / ACC-003：逐项复核五项 Anthropic 既有采纳，不将推荐字段误说成官方必填，也不激活新功能。
- REQ-004 / ACC-004：strict validate、source governance、完整回归和 fresh independent whole-diff review 有真实结果；失败不提交发布。
- REQ-005 / ACC-005：遵循既有 main 合并规则，将 source 与 campaign 的七项投影推进到 8.0.6；版本同步不重标旧资格证据。

task-package v2：kind implementation；question 既有来源是否仍支持静态契约；permission 隔离源码与已授权 SCM；exit 真实验证及独立审查；handoff root exact import；retention 保留负结果与未完成项。
retry budget 2；staleness 300 秒；新 blocker replan，资格缺失 blocked，不重复同基线失败 CI。总计真实模型取证仍最多一次，本阶段 0 次。
