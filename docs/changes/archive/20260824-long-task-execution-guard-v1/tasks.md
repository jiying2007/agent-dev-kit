# 执行任务：long-task-execution-guard-v1

- [x] T1 state/action/安全边界冻结
- [x] T2 先增加 execution guard 失败测试
- [x] T3 typed evaluator 与 CLI 实现
- [x] T4 docs/runbook/help/quick suite 接入
- [x] T5 targeted/quick/full、review/verify 收口；owner review 仍 pending

## Ownership 与并行冲突检查
- 写入范围：新 module/test/change、CLI、commands/runbook、runner。
- 读取范围：long-task/harness/goal/token contracts。
- 冲突：共享 CLI/runner 串行；不改 manifest/schema。

## 轻量工件与收敛结论
- 需求：requirements/proposal/design。
- task：本文件/state。
- evidence：negative/review/verification。
- 收敛：验证前 needs-fix。
