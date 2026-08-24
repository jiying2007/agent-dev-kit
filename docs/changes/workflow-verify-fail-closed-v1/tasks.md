# 执行任务：workflow-verify-fail-closed-v1

- [x] T1 根因、边界与 fail-closed 验收冻结
- [x] T2 先增加 deterministic 假绿复现测试
- [x] T3 显式传播 verify 子门禁失败
- [x] T4 定向/full、复审与受影响 change 重验；owner review 仍 pending

## Ownership 与并行冲突检查
- 写入范围：`scripts/workflow.sh`、新测试、本 change；受影响 Token change state/evidence。
- 读取范围：workflow/change governance/validate scripts 与测试。
- 冲突：共享 lifecycle 串行修改；不触碰 manifest/freshness 数据。

## 轻量工件与收敛结论
- 需求梳理工件：proposal/design。
- task checklist 工件：本文件/state。
- 执行反馈/验收记录工件：negative-results/verification-evidence。
- 收敛结论：完成前固定 needs-fix。
