# 执行任务：mcp-2026-compat-staging

- [x] 需求确认与边界冻结
- [x] active/candidate/activation/rollback 设计完成
- [x] 先增加 MCP watch 负 fixture
- [x] 更新 source ref、candidate decision 和 protocol contract
- [x] 扩展 ecosystem checker 与测试
- [x] 本地验证（定向/quick/full）
- [x] 代码评审与分级闭环
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围：external pattern/MCP manifest、ecosystem checker/test/fixture、本 change。
- 读取范围：MCP 当前 auth/provenance contract 与 2026-07-28 RC source。
- 冲突：与 skill-security-maintenance-v1 共用 ecosystem checker/test/fixture，串行修改后联合验证。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist：本文件。
- 执行反馈：`negative-results.md` 和后续 verify/review report。
- 收敛结论：staging 可实现；final compatibility 在规范发布前固定阻塞。
