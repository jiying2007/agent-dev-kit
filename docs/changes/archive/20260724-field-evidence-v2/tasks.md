# 执行任务：field-evidence-v2

- [x] 需求确认与边界冻结
- [x] v2 event/metric/PII/兼容设计完成
- [x] 先扩展 M5 pass/negative tests
- [x] 更新 policy、certifier 和状态输出
- [x] 更新认证计划与 field-readiness evidence template
- [x] 定向/quick/full 验证
- [x] 代码评审与分级闭环
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围：根仓 M5 policy/source/test/docs；ADK field-readiness Skill 与本 change。
- 读取范围：ledger/events/scorecard/runtime campaign。
- 冲突：与 repository-runtime-evidence-v1 共用 M5 policy/source/test，串行整合。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist：本文件。
- 执行反馈：`negative-results.md` 和后续 verify/review report。
- 收敛结论：contract 可完成；真实第二 operator/独立仓/30 天证据不在本次生成。
