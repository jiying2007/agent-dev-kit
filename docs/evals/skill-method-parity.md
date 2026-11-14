# ADK Skill 方法质量评测 — 执行协议（非结果）

## 权威边界
`tests/fixtures/skill_method_cases.json` 的情景与 expected_behavior 是**待验证假设**；本轮只可声明源文件/引用/路由/格式等 E0/E1 通过。没有真实模型 transcript 时 E2/E3/E4 均为 **not-measured**，不能用 CI 通过宣称优于 Superpowers / Matt Pocock。

## 盲评设置
- 在相同模型/版本、温度、预算、工具权限、项目上下文和任务集下冻结 baseline/candidate 的 immutable commit；本轮候选以前一已发布的 v11.2.16（538e224ad91319a17a88f0e8c4d743dd89d7b02d）为来源基线，旧 v11.1.0 仅作历史对照，不能与新候选混用统计。上游只作方法对照，不复制到运行仓。
- 交互任务至少保留四轮真实问答与分支决策；实现任务使用固定公开的验收命令与有效失败样例。遇到不可用宿主，写 `not-measured` 而非无音频/无模型模拟绿灯。
- 每个方案输出脱敏原始 trace、源 SHA、命令/返回码、用户确认或拒绝、结果和工具成本。不能控制的网络/设备环境逐项标明。
- 双人盲评先复核是否符合真实目标，再分维度给 0–4 分：问题发现、候选取舍、反馈有效性、可测试性、任务完成、额外问答/工具成本。授权/安全越界硬失败；模型作者或同一次生成不能自称独立裁判。
- 同行参考只在其确有对应能力时比较：无完全对等目标（嵌入式真实设备、HIL）不造假排名。
- 先检查不回退原有成功用例、安全与用户快路径，再比较任务成功、质量和实际 Token；若未优于基线，保留反例并回退该项行为方法。

## 测试映射
- `bash scripts/devkit.sh validate --strict`：结构与机器授权元数据。
- `python -m unittest tests.test_skill_content_contract -v`：65 个登记 Skill 的 Markdown 围栏和方法契约源回归。
- `bash tests/test_skill_trigger_matrix.sh`：触发词/否定/冲突的确定性 source-test。
- `bash tests/run_all.sh`：现有完整工程回归。
- **E2/E3/E4 额外记录**：真实 native discovery/load/trigger + 多轮/实作轨迹 +独立审核/使用方确认，不可由以上测试替代。

本协议只定义可复跑的试验，当前不包含任何捏造的任务成功率或 Token 节省百分比。

## 真实 Skill 改进评测的最小预注册批次（尚未执行）
- 复用 `tests/fixtures/skill_method_cases.json` 中至少 5 个不同真实任务和不少于 3 次独立试验；方案候选覆盖需求澄清、debugging、TDD、review 和嵌入式目标适配。其 expected/reject 字段是**假设**，不可作为模型通过回执。
- 执行前冻结 baseline/candidate **exact SHA**、native host、同一模型快照、采样参数、任务文本、工具/权限、缓存条件、上下文与 grader；用不参与编辑的 holdout 检验过拟合。真实数据含敏感信息时先脱敏并记录保真边界。
- 复用 `agent_dev_kit.effect_trials.compare_effect_trial_file` 及已有 Run Evidence/Trace Summary；只从可信实测 run 提取 first-pass success、误路由、authorization failures、输入/输出/缓存 Token、tool calls、elapsed_ms 和人工干预。不可把脚本模拟、文件字节或源码触发测试计作模型行为。
- **先判安全和质量不退化，再比较 Token/时延**。关键缺失（无可用 native host、无真实对照、无独立审查、缺成本记录）统一 `not-measured`，无需每小时巡检，不消耗未经授权的付费 Codex/Work 额度。
- 允许先只读复用原有合格 traces；未找到对应 exact source/模型/工具身份时不得混合批次或补造实验。此处是评测协议与预注册任务，不是测试已执行的报告。

## 真实触发 / 行为评测的预注册 ID（source-only，不是效果结果）
- 预注册合同在 `tests/fixtures/skill_method_ab_prereg.json`；案例原文来自 `skill_method_cases.json@6dbb5678c1c71a560eca2dd13acdf79719afcfee`，`train_case_ids` 与 `holdout_case_ids` **不重叠且覆盖全部 9 个已有案例**。候选 release/source SHA 在真实执行前补固定值；不能提前猜 commit。
- 描述、路由或方法的修改仅能利用 train 案例。冻结候选后留出集做独立终验；若使用留出集迭代，则原留出结论失效，必须重新预注册完全未参与优化的案例。
- 真实宿主可用且用户授权时，相同 model snapshot、工具权限、上下文、缓存条件与预算下按预注册重复；必要时加入不加载该 Skill 的阴性基线。每项用固定 grader、原始 trace 与 source SHA 跟踪。
- 先核 `unauthorized_tool_use / fabricated_evidence / security_regression` 硬失败，再比较任务成功、误触发、人工干预、Token（输入/输出/缓存）、tool calls、elapsed_ms 和可核账单成本。优先修复高影响失败，而非按文件数量、Start 数或静态 bytes 排名。
- 复用已有 `agent_dev_kit.effect_trials.compare_effect_trial_file` 和 Run Evidence。当前 `status=not-measured`、`execution=no-model-runs`、`results=[]`，所有 E2–E4 与真实 Token/成本提升均未实测；不为本协议新建模型 runner、定时任务或消耗 Codex/Work 额度。
