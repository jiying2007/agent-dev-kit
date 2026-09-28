# 本地任务

- [x] 核实 `run_deterministic` 只比较 Skill，`expected_safe` 未参与评分。
- [x] 增加总览和逐用例检查范围字段，保留路由评分语义。
- [x] 增加安全标签反转负例，更新命令和使用文档。
- [x] Python 3.8 `test_software_m5_ready.sh`、`devkit validate --strict`、release check 与 `git diff --check` 通过；CLI 实际输出 30/30 路由通过且 `safety_accuracy=null`。
- [x] 增加 canonical manifest 与已解析有序任务集摘要、非原子声明；Python 3.8 定向与 profile 棘轮通过。整批回归结果见 `../20260928-python38-test-runner/tasks.md`。
- [ ] Codex Runtime `execution-policy gate --event final` 返回 `runtime_control.policy/v2 requires an attested goal intake`；当前无 active goal，不能伪造 intake。这是本地 Runtime 门禁状态，不覆盖上述 ADK 源码测试结果。
- [ ] 本批集中做当前快照完整回归、独立复审和跨仓分发；当前不提交、推送、合并或 live apply。
