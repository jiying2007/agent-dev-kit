# 设计：effect-comparator-v1

```text
complete expected task population
  + baseline Run Evidence[]
  + candidate Run Evidence[]
  -> child validation
  -> population/runtime/model/bundle/window gates
  -> per-condition coverage-aware metrics
  -> candidate-minus-baseline deltas or not-comparable
```

Comparator 只保存聚合值、task population digest、condition bundle/runtime/model/prompt versions，不保存 prompt、
message、tool payload 或 task 内容。缺失 metric 的 observed/applicable sample size 与 coverage 显式输出。

回滚时删除独立 module/schema/test/runbook/change，不影响 Trace、Agent Value 或 Run Evidence API。
