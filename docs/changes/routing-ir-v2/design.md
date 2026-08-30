# 设计：routing-ir-v2

## 单一合同

`manifest.json:routing` 是运行时路由 IR 的 SSOT，`manifest.yaml` 仅为兼容镜像。IR 包含：

- `defaults`：无法从请求确认时采用 `task_mode=needs-triage`、`mutation_permission=deny`。
- `task_modes`：确定性的 mode signal、优先级和权限上限；readonly 优先于实现、调试、评审和发布。
- `artifact_mode_mapping`：将 routing mode 收敛为 Runtime Control v2 的 canonical artifact mode；
  debugging/review 映射 readonly，needs-triage 映射 null 并禁止进入 gate。
- `intents`：正向短语、primary/supporting Skill，以及可选的 task mode、风险、证据和 `negated_intents`。
- `abstain`：无候选或候选全部被否定时返回 `abstain / needs_triage`，不授予修改权限。

## 决策顺序

1. 从 task mode signals 判定显式 task mode；局部被否定的 signal 不参与分类。
2. 计算 routing intent 正向候选。
3. 若候选满足任一 `negated_intents[].all_of`，或其全部触发短语都被局部否定，则记录为 negated candidate。
   Skill non-trigger 同样先做局部否定判断，`不是纯文档修改` 不得被解释为 `纯文档修改`。
4. 从剩余候选按既有 specificity/order 规则选 primary Skill。
5. Skill trigger fallback 必须先检查 frontmatter `non_triggers`，并跳过已被 routing IR 否定的 Skill。
6. 没有可执行候选时返回 abstain；该结果保持 `match=false` 和非零 CLI 退出码。

## 权限边界

- matcher 只报告用户请求可推导出的权限上限，不执行任何动作。
- per-intent mutation permission 是 hard cap；全局 task mode signal 与 intent cap 取最严格权限。
- 显式 readonly 可收紧任何 intent；implementation signal 不得覆盖 debugging/review/readonly 的 deny。
- `workspace-write` 仍受调用方的实际沙箱、用户范围和 owner gate 约束。
- `explicit-authorization-required` 不等于已获发布、部署或外部写权限。
- `deny` 明确阻止从只读/否定请求推断修改权限。

## 兼容性

- 现有 `routing.intents` 顺序和 specificity 排序不变。
- `format_result` 保留原有 `match=true source=... skill=...` 前缀，仅附加 v2 policy 字段。
- 无匹配结果从 `no_match_found` 细化为 `abstain / needs-triage`；`match=false` 与 CLI 非零语义保持不变。
- `artifact_mode=not-applicable` 表示 needs-triage 尚未形成 Runtime Control v2 可接受的 gate 输入。
