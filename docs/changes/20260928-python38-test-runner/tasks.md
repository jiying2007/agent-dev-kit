# 本地任务

- [x] 复现包导入失败与系统 `python` 为 Python 2 的测试失败。
- [x] runner 绑定工作树 `src`；相关 shell 测试显式调用 `python3`。
- [x] Python 3.8 完整回归：94 项中 93 项通过，`test_runtime_bundle` 因 clean commit 身份门禁失败；内部 3 个功能测试通过。
- [ ] 统一提交后复跑 clean commit 身份项；本阶段不提交、推送、合并或 live apply。
