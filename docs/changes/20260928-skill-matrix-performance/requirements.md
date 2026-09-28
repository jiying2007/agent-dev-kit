# Skill 触发矩阵测试耗时收敛

## 目标与边界

`test_skill_trigger_matrix` 当前对 68 个数据行逐个启动 `devkit.sh match`，在 Python 3.11 quick 收据中单项约 54 秒，quick 总耗时约 177 秒，超过现有 120 秒预算。保留完整触发矩阵与至少一次真实 CLI smoke，减少重复解释器启动。不修改 matcher 生产行为、不上调预算。

## 验收

- 每一 TSV 用例在同一 Manifest 快照下得到与旧测试相同的 match/不匹配结果；错误报告标明行号、Skill、scope。
- CLI 至少执行一次成功路径；测试不用固定 `/tmp/adk_skill-match.txt` 共享输出。
- Python 3.8 与 3.11 定向测试通过；quick 计时重新采样并记录总耗时，不把单次主机抖动解释成产品性能结论。
