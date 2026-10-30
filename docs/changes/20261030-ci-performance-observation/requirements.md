# 对照本次 CI 全量耗时

## 目标

把同一次 regression job 的真实 timing 接入既有性能预算报告，确保结果、解释器、运行环境与 artifact 可追溯。

Owner 已在 2026-10-30 审查后授权按建议全部优化落地。

## 边界

继续 report-only；不新增耗时硬阻断，不改变 Root quick strict 策略，不运行网络或模型 benchmark。

## 验收

1. 报告模式在超预算时输出 warn 且不改变成功退出策略。
2. 缺失 timing 或无效输入必须明确报错，工作流留下可见诊断。
3. 真实 full timing 与报告使用同一路径，三个 Python job 各自保存结果。

