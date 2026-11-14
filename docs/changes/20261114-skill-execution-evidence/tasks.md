# 任务与验证

- [x] T1 独立核验 #264 最新 SHA 的 CI、差异与 Spec/Quality 结论；verify：`2d5306b8ce342b88d04420d55843ce752c0e5240` 的8个必需检查通过，独立 Spec/Quality pass，typed review 校验通过。PR已受保护合并至 `ebef1106aeecbe14e9ac676b2950b81895c1ea5b`。
- [x] T2 实现真实任务证据导入并接入现有 eval CLI；verify：现有 run-evidence runner 4+22+15=41项通过，真实 grade/import/配对CLI联通，strict mypy与ruff通过。独立复审和完整回归在T4/T5单独追踪。
- [x] T3 补齐既有 Skills 的执行缺口和 8 类开发基准；verify：12项基准测试、71项content、14项trigger以及token/profile/module门禁通过。只读独立Spec/Quality pass；未执行模型任务。
- [ ] T4 冻结来源、完成版本投影与完整回归；verify：strict validation、全套tests、lint/type和现有安全门禁。
- [ ] T5 独立只读 Spec/Quality 审查，修复发现，受保护 PR/合并/主线发布；verify：最终SHA、CI、Review及release证据分别核查。
- [ ] T6 使用允许宿主的真实任务观测执行预注册比较；verify：实际Skill加载、产物、usage和新任务证据；无法访问时保持evidence-blocked，提供导入/续行入口。

每项只有对应 verify 已执行并通过才能勾选。测试 fixture 的成功不计入 T6。

## 当前状态

协调/设计/发布由 `ai/root` 负责；实现分别由 `ai/root/implement_task_evidence` 与
`ai/root/implement_skill_workflows` 完成；只读独立审查由 `ai/root/review_existing_candidate` 负责。
11.3.0 的兼容CLI与版本投影已冻结，独立Spec/Quality复核通过。
首轮集成诊断为101/102，唯一profile体积失败已精简引用并定向6/6复验，未提高预算。
下一步：将冻结源码与真实审查记录提交受保护PR；核验最终提交的完整CI；验证主线CI与不可变release。
T6当前为 evidence-blocked：没有允许宿主的真实任务观测，续行见 `docs/runbooks/task-evidence.md`。
