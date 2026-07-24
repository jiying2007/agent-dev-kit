# 执行任务：repository-runtime-evidence-v1

- [x] 需求确认与边界冻结
- [x] 设计 contract、report matrix、isolation 和 fail-closed 规则
- [x] 先编写 repository runtime 正负测试
- [x] 实现 contract/task/report validator 与 CLI
- [x] 增加生产 contract、冻结 metadata 和 optional adapter 边界
- [x] 接入 root Software M5 独立 blocker
- [x] 更新 eval suite、README/commands 和变更证据
- [x] 本地验证（定向/quick/full）
- [x] 代码评审与分级闭环（blocker/major/minor）
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- 写入范围：repository eval module/CLI/manifest/fixture/test/docs；根仓 M5 policy/certifier/test/docs。
- 读取范围：现有 campaign/evaluation、trace/effect、M5 policy 和外部研究报告。
- 冲突：与 field-evidence-v2 同时修改 root M5 policy/certifier/test，必须串行整合和共同回归。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist：本文件。
- 执行反馈/验收记录：`negative-results.md`、`verify-report.md`、`review-report.md`。
- 收敛结论：contract/fixture 可完成；真实 runtime campaign 必须保持 not-run/blocked。
