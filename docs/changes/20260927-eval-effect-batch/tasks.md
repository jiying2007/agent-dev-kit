# 本地批次状态

- [x] 核对 `llm_agent` 台账、ADK 当前实现和外部一手资料。
- [x] 对齐 guardrail suite 与数据集；中英文四类样本共 8 条，ID、预期结果和输入正文一致，并补目录审计。
- [x] 增加确定性负例与有限字节预算；目录审计的最新 6 项 Python 3.8 测试、`devkit validate --strict` 已通过。
- [x] 更新现有测试/恢复 Skill，核对入口体积棘轮。
- [x] 复核已登记参考仓远端 HEAD、上游 release 与新候选，记录 exact SHA 和本地吸收取舍；未动 dirty 参考目录或 pin。
- [x] `devkit validate --strict`、release check、目录审计负例、profile 棘轮、Skill SOP、测试注册与格式检查通过。
- [x] Python 3.8 工作树全量回归 92/93；唯一失败是 `test_runtime_bundle` 的干净提交身份门禁，内部 3 个功能测试通过。按用户要求保持未提交，待统一提交后复跑身份项。
- [x] 吸收近期参考实践：规划 Skill 采用里程碑批量验证；工具副作用 reference 补 proposal、可信校验、受限 executor 与目标生效边界。最新 Python 3.8 quick 回归 49/50，唯一失败仍为干净提交身份门禁；严格校验、release check、SOP 与体积棘轮通过。
- [x] 任务拆解 Skill 增加就绪任务集合、前置验收与共享写冲突边界；等待本地批次集中验证。
- [x] 目录审计逐 suite 披露真实检查范围：当前 10 个声明中 1 个 TSV 对齐已核，9 个 contract-only，grader 与 runtime eval 均未执行；release check 与严格校验通过。
- [x] 2026-09-28 补中英文四类样本共 8 条，manifest 与 TSV 按 ID、预期和输入正文对齐；逐 suite 输出数据 SHA256、catalog SHA256 和 `snapshot_atomic=false`。最新 Python 3.8 定向 6/6、严格校验与 release check 通过。
- [x] 目录与数据摘要绑定已读取字节，显式标记非原子快照；正文漂移和超预算负例已补，待批次定向验证。
- [x] 工作树自审发现重复 manifest fixture 可能误报逐 suite 对齐 `pass`；已收紧判定并补负例，Python 3.8 定向 7/7 通过。当前只有 guardrail TSV 逐项对齐，仍不代表 runtime eval。
- [x] 此前本地批次快照经 Python 3.8 完整回归 94 项中 93 项通过；唯一失败是 `test_runtime_bundle` 需要 clean commit，内部 3 个功能测试通过。首次回归暴露的测试 runner `PYTHONPATH` 与系统 Python 2 入口已修复，详见 `../20260928-python38-test-runner/`。此后任务加载器又有行为改动，完整回归须在统一收口复跑。
- [x] 2026-09-28 后续快照完整回归 95 项中 94 项通过，唯一失败仍为 clean commit 身份；逐例模型身份与测试策略补丁在该全量之后，当前快照只完成定向与体积棘轮，详见 `../20260928-runtime-eval-comparability/`。
- [ ] 本批与后续优化一起做最终语义审查、版本前移和跨仓分发。

本批只保留本地未提交改动；提交、推送、合并和 live 应用等待用户后续统一收口要求。
