# 任务与验收

- [x] 核对当前 ADK 能力、官方资料和评测数据集引用。
- [x] 扩展接口 Skill，补独立副作用契约。
- [x] 补 guardrail fixture，新增路径与样本覆盖测试。
- [x] `scripts/devkit.sh validate --strict`、`tests/test_skill_sop_quality.sh`、`scripts/devkit.sh release check`。
- [x] `tests/run_all.sh` 工作树阶段回归 91/92；唯一失败为要求干净提交的 `test_runtime_bundle` 身份门禁。
- [x] 最终 diff 审查：改动限于一个 Skill、一个按需参考文件、一个已声明的 fixture、治理测试、源码体积棘轮和本 change 文档；无 runtime/profile 变更。
- [x] 干净提交后，`test_runtime_bundle` 的 3 个功能测试与身份门禁均通过。

测试启动环境需令 `python` 指向 Python 3.8，主机默认 `/usr/bin/python` 为 Python 2.7。最终提交若因记录本验收结果而变化，身份门禁须对最终干净提交再次复跑。

结论只覆盖源仓契约与测试；Codex 分发和 live 应用另按 source-to-live 绑定版本执行。
