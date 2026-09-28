# 设计与来源

2026-09-28 直接读取 [Langfuse Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)：发布决策应使用同一数据集版本与 evaluator 定义，记录应用、提示词/模型和 evaluator 版本；平均分不能掩盖关键用例退化。参考 [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/) 的测试归属边界，真实 provider 行为仍需真实适配器证据。

ADK 适配为本地合同：任务集摘要采用已解析有序任务序列；逐例只保存 prompt SHA256 与现有期望标签；grader 用显式版本常量，评分逻辑变更时必须前移。比较器先核报告内部指标与身份，再核两侧任务、标签、prompt、grader、请求模型和 CLI 版本，最后算总体/逐例差异。manifest 摘要分别保留，因为 ADK 处理侧可故意变更；它不能替代整个源码树身份。

任务序列在模型或 matcher 调用前经 JSON 规范化冻结，所有评分与摘要都读取同一份内存快照；测试主动修改原可变对象以证明结果不漂移。`task_snapshot_frozen=true` 仅指这份任务序列，manifest、源码树和外部 provider 状态仍非原子快照。
直接库调用的任务快照也受同一 1 MiB 字节预算约束，超预算在模型调用前失败。

旧历史 runtime 报告缺新身份时继续可作为归档阅读，但 `eval compare` fail closed，不生成新通过结论。报告身份来自调用方生成的 JSON，`input_identity_authenticated=false`；未做签名、原子快照或实际 provider 结果认证。任何真正 release 决策仍需独立证据和 owner 门禁。
比较输出始终给出 `release_authorized=false`，避免把评测比较 `pass` 误作发布放行。
顶层请求模型必须与每个用例一致，顶层观测模型列表必须等于逐例观测列表的并集；请求模型缺失时不允许比较。任一 `pass → fail` 用例会阻止比较通过，即使平均值改善；真实模型波动需另行重复实验和审查，不由单次结果自动放行。

平台中立方法进入既有 `adk-test-strategy`，未新增 Skill。入口增加 262 UTF-8 字节，七个包含该 Skill 的 profile 的入口与潜在完整源码各增加 262 字节；`incident-response` 不变。体积棘轮按实测更新，这不是 provider token 或 live 初始上下文测量。
