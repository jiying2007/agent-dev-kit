# 设计

## 执行顺序

1. 对齐 `eval_suites.json` 与 guardrail TSV，增加伪造审批对抗例，并为四类样本各提供中英文输入。按 ID、expected 和输入正文核对，避免编辑其中一份时静默漂移。
2. 在 `src/agent_dev_kit/eval_catalog.py` 实现只读、无网络、Python 3.8 可运行的目录审计。通用 suite 只验证静态目录与声明结构；仅 guardrail TSV 做严格字段、分类和 manifest 对应校验。输出保留 `catalog_valid`、`dataset_fixture_alignment_scope` 与 `runtime_eval_executed`，防止把其它文档型 suite 误称为已执行数据集。
   - 逐 suite 输出 `dataset_present`、`fixture_dataset_alignment`、`dataset_sha256` 和 `grader_executed`，并报告 contract-only 数量；目录与 TSV 均有有限字节预算。catalog 与数据摘要只绑定各次读取的字节，明确 `snapshot_atomic=false`，不声称跨文件原子快照或模型成绩。
3. 在现有 `validation_contract.validate_repository` 和 `release.check_release` 调用目录审计，不建立新的发布流程；用最小正负 fixture 测试失败路径。
4. 更新 `adk-test-strategy` 和 `adk-planning-execution-loop` 的入口指引，详细副作用规则继续链接现有 `adk-interface-contract-design` reference。
5. 将官方开源的待审写入分层适配到现有工具副作用 reference：proposal、可信校验、收窄权限的 executor、实际生效回执分离；不增加新 Skill、运行时或托管服务。
6. 在 `adk-task-breakdown` 的依赖图之后显式计算就绪集合：依赖证据完成、共享写冲突消除、权限符合 task-package v2；保持 existing schema，不引入新的任务调度器。

七个包含上述 Skill 的 profile 入口和潜在完整源码各增加 502 UTF-8 字节；`incident-response` 无新增资产，棘轮保持原值。这是源码大小审查，不宣称初始提示 token 用量。
工具副作用参考契约扩展后，这七个 profile 的按需支持材料各再增加 787 字节；入口大小不变，`incident-response` 仍不受影响。棘轮按当前源码实测更新。
任务拆解入口补就绪集合后，这七个 profile 的入口和潜在完整源码各再增加 454 字节；未引入新的支持文件或默认运行上下文声明。

## 回滚

删除目录审计模块及调用、恢复 guardrail manifest/TSV 和两处 Skill 文字即可回到上一合同。没有数据库、外部写入或运行态迁移。
