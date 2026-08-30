# Effect Comparator

`agent_dev_kit.effect_comparator` 对两组已经过 `validate_run_evidence` 的 baseline/candidate test runs 做
确定性对比。它是本地 effect-eval 工具，不是 native runtime campaign certifier。

## 强制可比条件

- 调用方提供非空、唯一的 expected task population；工具重算 count 与 digest。
- baseline 和 candidate 必须完整覆盖同一任务集，每个 condition 每个 task 恰好一个 run。
- 两组 run identity 必须互不复用，baseline/candidate asset bundle 必须不同。
- 对应 task 的 runtime target、runtime version 和 model version 必须一致。
- 每组内部只能有一个 runtime/model identity 和一个 asset bundle。
- 所有 run 的 observed time 必须落入固定 campaign window，且 `through <= as_of <= now`。

## 指标和缺失语义

输出 task success、first pass、human interventions、latency、cost、token、wrong skill 和 abstain。
任何 condition 的 cost/token/outcome 覆盖不完整时，该指标为 `not-measured/incomplete-coverage`，delta 为
`not-comparable`；不得只对有值的子集求平均，也不得补零。Cost 可比较时两组 currency 必须相同。

输出固定：

- `evidence_scope=test-only`
- `quality_evidence_eligible=false`
- `owner_review_required=true`
- `lifecycle_authority=none-evidence-only`

调用方声明的 task population 仍需 owner 审查；该工具不能证明任务集代表真实生产分布。

## 验证

```bash
rtk bash tests/test_effect_comparator.sh
rtk bash tests/test_run_evidence.sh
```

真实双 runtime、独立仓、双操作者和 field campaign 必须由 R10/Software M5 证据链完成。
