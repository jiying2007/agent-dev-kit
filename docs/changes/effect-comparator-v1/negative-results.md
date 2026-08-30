# Negative Results：effect-comparator-v1

- 缺少一个 task：拒绝，不允许选择性缩小 denominator。
- 同 condition 重复 task/run：拒绝。
- baseline/candidate 复用 run：拒绝。
- 对应 task runtime/model 不一致：拒绝，不跨环境直接算 delta。
- candidate cost 仅部分可用：condition metric 为 not-measured，delta 为 not-comparable，不补零。
- outcome 不可用：success metric 与 delta 不可比较。
- secret-like campaign identifier：共享 privacy gate 拒绝。

这些结果不证明任务集具有生产代表性，也不授予 quality/promotion authority。
