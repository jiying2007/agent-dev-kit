# Repeated effect comparison

```bash
adk eval compare-trials --input campaign.json --output comparison.json --summary-json
```

输入格式为 schemas/effect-trials-v1.schema.json。计划与全部 trial 同文件，每个 trial 的 baseline/candidate 项由已有 Run Evidence 加 plan_ref/controls_ref 组成。使用 UTF-8 canonical JSON（sort_keys、separators=(",",":")）计算 sha256，引用形式为 ref:<digest>；计划引用以完整 plan 对象为输入，控制引用以完整 plan.controls 为输入。

先在版本控制中冻结计划，再采集全部预期任务和重复运行，不能仅提交成功样本。每条件每 trial 包含相同完整 task_id 集合；run_id 必须全局唯一。唯一允许干预是 plan.bundles 指定的两个资产 bundle，其余摘要身份与控制引用保持固定。模型别名无法证明 revision 时使用 alias-unverified，结果保留统计但结论 inconclusive。

primary_metric 和 guardrails 只能使用原 effect comparator 的方向性指标。至少包含 task-success-rate 与 wrong-skill-rate 护栏。建议先冻结30个任务、每任务3次，再按研究需求和预算设 minimum_tasks/minimum_trials；这不是统计显著性的保证。

退出码0仅代表此 test campaign improved/non-inferior；1为regressed；2为inconclusive/invalid。它们均不产生 release authority。报告中的模型、环境、grader和计划登记时间是调用方声明，未被本工具独立认证；opaque hash提供绑定，不提供真实性背书。

输出 any_trial_succeeded_rate 与 all_trials_succeeded_rate，不能混用。缺成本/结果保留 not-comparable/not-measured；基础设施失败使整体invalid，不删除失败trial再算。可靠性结论应结合代表性、置信区间、硬护栏和真实运行验证，不能只看绿色exit。

测试入口：tests/test_effect_trials.sh。tests/test_effect_trials.py 的 document() 可生成不依赖模型凭证的完整合成示例，仅作为数据格式与比较器回归测试，不是产品效果证据。