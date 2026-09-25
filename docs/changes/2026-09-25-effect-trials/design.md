# 重复试验设计

effect_trials 对每个 trial 调用 effect_comparator.compare_effects；成功率、token、成本和缺失值语义继续由原 comparator 的条件汇总实现负责。只在合法原子试验之上增加跨 trial 的来源一致性和任务级聚合。

计划包含 expected tasks/trials、时间窗口、两个 bundle digest、固定控制变量、主指标、效应阈值、非劣界值和重采样参数。每条测试 run sidecar 绑定 plan_ref/controls_ref；真实摘要中的模型、运行时、prompt、编排模式和 bundle 还要与计划逐项相符。环境/参数/grader/权限/数据集/provider 仅保存 opaque ref，报告明确其 caller-declared/not-attested 属性。无法独立确认 model revision 时必须使用 alias-unverified。

统计：每任务先对全部 trial 聚合；对 task 均值差配对 bootstrap，绝不把多次运行当成更多独立任务。主指标与护栏使用 Bonferroni 校正的 percentile 区间。small-sample/degenerate-bootstrap、代表性和跨候选选择偏差限制在结果中明确。p95 是任务均值分布的分位数，不是原始运行延迟尾部。

退出码：improved/non-inferior=0，regressed=1，inconclusive/invalid=2。所有结果仅 test-only，无产品资格、发布或生命周期权限。未知指标、错证据、缺 trial 等校验失败不输出测得收益。

预算：文件16MiB；每条件最多2000个 task×trial 单元；每指标最多2,000,000次抽样累加；默认不包含网络或模型执行。

回滚：回退此新增能力及其 CLI/schema/test/registry；单次接口语义不变。旧历史证据不重写。任何模型客户端或生产执行循环不属于此模块。