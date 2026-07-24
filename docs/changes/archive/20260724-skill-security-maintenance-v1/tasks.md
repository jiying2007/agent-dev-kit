# 执行任务：skill-security-maintenance-v1

- [x] 需求确认与边界冻结
- [x] AST10/maintenance/watch 设计完成
- [x] 先增加三类负 fixture
- [x] 更新 external source/candidate 和 skill contracts
- [x] 扩展 ecosystem checker/test
- [x] 更新 reference adoption 文档
- [x] 定向/quick/full 验证
- [x] 代码评审与分级闭环
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围：external/skill manifests、ecosystem checker/test/fixture/reference docs、本 change。
- 读取范围：portable Skill、ASI、third-party intake、target contracts。
- 冲突：与 MCP change 共用 ecosystem files，串行修改和联合验证。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist：本文件。
- 执行反馈：`negative-results.md` 和后续 verify/review report。
- 收敛结论：crosswalk/evidence/watch 可实现；不新增 direct target。
