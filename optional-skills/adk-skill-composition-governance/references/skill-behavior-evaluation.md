# Skill 行为回归：基线—候选—压力测试

此方法不规定某个模型供应商，也不自动调用 Codex/Work/付费 API。

1. **问题与基线**：给出一个真实任务失败，附脱敏原始 trace（缺哪条事实、错误推断、反复提问、误触发、越权或交付错误）；冻结模型/运行时、权限、工具、检索上下文、预算和任务集。
2. **RED**：不加载目标 Skill 跑场景，观察原始失败；若已发生过且证据可信可复用。没有模型调用渠道或记录时只标 `not-measured`。
3. **GREEN**：加载候选 Skill、其余不变，重跑相同场景；记录结果是否修正和原已成功场景是否退化。交互式场景保留每轮用户回复/依赖决策 frontier。
4. **冻结训练/留出集（执行前）**：任务案例预注册 `train_case_ids` 和 `holdout_case_ids`，两组不可交叉；冻结样本身份、选取理由、版本与 grader。描述优化只利用训练集失败，留出集在候选冻结后才评一次；不可根据 holdout 的错误反复重写候选。重复试验次数与预算由目标任务预注册，不为小改无条件跑大批次。
5. **压力边界**：至少包括 positive、near-miss、相邻 Skill 冲突、用户否定/退出、诱导跳过验证、失败后恢复；不同能力选择相关项而非强加模板。
6. **盲评**：对关键用户可见效果，两位不共用生成上下文的审查者按预注册 rubric 打分；包含安全/授权硬失败，不允许被平均分抵消。
7. **成本**：先判不低于现行质量，再比较实际输入/输出 Token、工具次数与耗时；不可用静态字节/估算 token 替代实测。
8. **资格边界**：E0/E1 的 source-test 可自动通过；E2 对话/行为、E3 native host、E4 任务轨迹未执行则始终 `not-measured`。附确切 trace 与来源 SHA，不伪造已通过认证。

汇报最小字段：`candidate_sha / baseline_sha / model_runtime / scenario_id / raw_trace_ref / judge / behavior_verdict / permission_verdict / tokens / tool_calls / unresolved`。

## Case isolation / observation boundary（需要真实评测时）

- 复用已有 `effect_trials`，按固定案例在 baseline/candidate 间恢复**相同初始 workspace、输入、工具权限和缓存条件**；工作树输出只能证明最终状态，不足以证明中途未越权读写或未外传。
- 记录 `initial_workspace_ref / observed_tool_calls / final_artifact_ref / forbidden_side_effects / missing_observability`，真实 trace 可验证时才判实际行为；模拟 CLI/静态回放/离线 matcher 只给 E0/E1，不能伪造 native load、独立评价或任务完成率。
- 真实宿主不可用时保留预注册和用例，明确 `not-measured`，**不因未测而运行收费模型、触发新定时任务或削弱安全 guardrail**。

## Skill Value / Harm Gate（真实任务才判）

- 只对确有真实运行证据的任务比较 `no-skill vs selected-skill`，固定 `target_repo@commit`、需求与可执行 verifier、model/runtime、工具授权、时间窗和初始 workspace。区分正确性、实际 Skill 调用、耗时/Token、越权或负面副作用；不能用通用问答或纯模板得分代表真实工程成功。
- 特别检验三类负收益：`wrong-version`（Skill 的 API/框架版本落后于目标仓）、`explicit-instruction-conflict`（模板覆盖用户的明确非目标/验收）、`irrelevant-trigger`（无关任务仍加载）。记录原有成功任务的退化而不仅是新任务绿灯。
- 分类 `beneficial / neutral / harmful / inconclusive` 必须有任务级成对结果与原始 verifier/trace；样本不足、未成对、审查不独立或环境漂移时统一 `inconclusive / not-measured`，不得用偶发一次成功批准长期 Skill 默认启用。
- 这项检查沿用 ADK `effect_trials`，不导入 SWE-Skills-Bench 任务/模型执行器，不用 Skill 自己评价自己。没有明确性能增益也不能因此跳过安全/权限门禁。

## Evidence Contract
- 固定 `baseline_sha / candidate_sha / model_runtime / tool_permissions / budget / grader_id / dataset_sha`，无真实 source 或宿主权限则中止并记 `not-measured`。
- 先以安全/任务质量 **non-regression** 决定是否可比较 Token、wall time、tool calls；授权越界为硬失败，未报告的缓存 Token 记 unavailable。
- 若同一 ID 被用于优化和 holdout 或当前运行环境发生漂移，标 `invalid-eval` 并冻结原始 trace，不以静态 router pass 代替行为结论。
- 复用既有 `agent_dev_kit.effect_trials.compare_effect_trial_file`、Run Evidence、Trace Summary；不自动运行付费模型，不创建平行评测引擎。
