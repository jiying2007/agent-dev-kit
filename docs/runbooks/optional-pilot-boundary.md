# Optional Pilot Boundary Runbook

## 适用场景

- 来源仓在 intake 中被判定为 `reject`，但仍有局部方法值得低风险验证。
- 需要保证试点不污染 core 路由与默认 profile。

## 目标

- 允许在 `optional` 层验证候选做法。
- 明确“可进可退”，避免 reject 项绕道进入核心资产。

## 执行边界

1. 试点资产只能落在 optional 路径，禁止直接放入 core skills。
2. 必须声明 `must_not_touch`：核心路由、默认 profile、全局入口脚本。
3. 每个试点都要有回退路径：删除可选资产即可恢复原行为。
4. 试点结论只允许三种：
   - `promote-to-optional`：保留在 optional，继续观察；
   - `sunset`：关闭试点并移除；
   - `re-intake`：满足条件后重新进入正式来源评估。

## 验收门禁

- `check-runtime-routing.sh` 必须 PASS。
- `rtk bash tests/test_skill_trigger_matrix.sh` 必须 PASS。
- `check-all.sh --quick` 必须 PASS。
- 必须有一条可复现 evidence 路径记录试点结果。
