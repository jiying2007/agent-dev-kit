# 执行任务：official-freshness-utc-date-v1

- [x] T1 复现与 UTC 语义冻结
- [x] T2 增加 cross-TZ 失败测试
- [x] T3 UTC default 与 summary disclosure 实现
- [x] T4 official/workflow/strict/full 与复审；owner review 仍 pending

## Ownership 与并行冲突检查
- 写入范围：official docs gate、新测试、本 change。
- 读取范围：freshness manifest、validate/workflow 入口。
- 冲突：与 workflow fail-closed 串行；不改 expiry manifest。

## 轻量工件与收敛结论
- 需求梳理：proposal/design。
- task：本文件/state。
- 验收：negative/verification evidence。
- 收敛：完成前 needs-fix。
