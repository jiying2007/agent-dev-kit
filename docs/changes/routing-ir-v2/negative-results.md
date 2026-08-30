# 负结果与 Repair Note：routing-ir-v2

## Repro Baseline

环境：2026-08-30 当前工作树，入口 `rtk scripts/skill-match.sh --text <input>`。

| 输入 | 修改前结果 | 结论 |
|---|---|---|
| 长任务但只做只读分析且无需执行计划 | `match=true source=optional_skill_trigger skill=adk-planning-execution-loop trigger="执行计划"` | routing 表未命中后，fallback 未检查全局否定语义 |
| 根因不明但不要调试只做架构评估 | `match=true source=routing skill=adk-systematic-debugging` | routing intent 只看正向子串 |
| 准备发布但只需要解释现状不执行发布 | `match=true source=routing skill=adk-release-versioning` | 后置范围收窄无法覆盖先出现的正向子串 |

## 假设与负结果

| 假设 | 实验 | 结果 |
|---|---|---|
| 仅补 Skill `non_triggers` 即可修复全部问题 | 检查 matcher 调用路径 | 证伪；routing intent 路径从不读取 Skill frontmatter `non_triggers`，且第 3 条需要组合语义 |
| 只在触发词前检查一个“不”即可 | 比较三条触发位置 | 证伪；`准备发布` 先出现，真正否定条件 `不执行发布` 在后半句 |
| 统一 IR + 局部否定 + `all_of` 组合规则可覆盖且不过度否定 | 三组正负对照，并增加“只生成版本清单、不执行发布”只读正向检查 | 通过；三条反例 abstain，对应正例仍命中原 Skill，只读发布清单仍路由 release 但权限为 deny |
| 全局 implementation signal 可以覆盖 intent policy | `根因未明，需要调试并修复` | 证实为缺陷；首版返回 debugging Skill 但授予 workspace-write，已改为 intent hard cap 并回归 deny |
| 任意命中 non-trigger 都应 veto | `这不是纯文档或命名修改；根因未明，请调试并定位根因` | 证伪；non-trigger 自身被否定时必须忽略，修复后命中 systematic-debugging |
| routing mode 可直接传 Runtime Control | 对比 routing 与 Runtime Control v2 task mode enum | 证伪；debugging/review/needs-triage 不是 Runtime Control canonical mode，已增加 artifact mode 显式映射 |
| routing ablation 仍可解析 artifact mode | `test_effect_eval.sh` 禁用 routing intents | 首次修复失败；disabled routing 没有 mapping，已限定为 needs-triage/not-applicable，复跑 effect eval 通过 |

## Repair Note

- failed_scope：全局 routing intent 与 Skill fallback 的组合否定语义。
- passing_scope_to_preserve：现有正向 primary Skill、specificity 排序、显式 `--skill` 行为、CLI `match=false` 非零语义。
- minimal_rerun：`tests/test_match_effectiveness.sh`、`tests/test_boundary_conditions_match.sh`、manifest schema/quick validate。
- rollback_anchor：本 change 修改前的四个核心文件。
- root_cause_status：known。
- repair_action：引入 routing-ir/v2 并让所有全局候选统一通过否定与弃权裁决。
- semantic_verification：三组 contrastive 正负输入 + 无关输入 abstain。
- do_not_repeat：不通过无限追加 trigger/non-trigger 单句绕过统一决策合同。

## Fix Verification

| 输入 | 修复后结果 |
|---|---|
| 长任务但只做只读分析且无需执行计划 | `match=false decision=abstain reason=needs-triage task_mode=readonly mutation_permission=deny` |
| 根因不明但不要调试只做架构评估 | 同上，`negated_intents=systematic_debugging` |
| 准备发布但只需要解释现状不执行发布 | 同上，`negated_intents=release_versioning` |
| 长任务，需要执行计划并分阶段执行 | `adk-planning-execution-loop`，implementation/workspace-write |
| 根因未明，需要调试并定位根因 | `adk-systematic-debugging`，debugging/deny |
| 准备发布并执行发布前检查 | `adk-release-versioning`，release/explicit-authorization-required |
| 根因未明，需要调试并修复 | `adk-systematic-debugging`，debugging/deny，artifact mode readonly |
| 这不是纯文档或命名修改；根因未明，请调试并定位根因 | `adk-systematic-debugging`，被否定 non-trigger 不参与 veto |
| 完全无关的文本xyz | abstain/needs-triage，artifact mode not-applicable，不得进入 Runtime Control gate |

定向路由 34/34、历史边界 39/39、Runtime Control 14/14、schema 负例和 strict manifest validation 均通过。当前执行环境为 Python 3.8.10，证据层级为 development，不替代受支持 Python 3.11/3.12 的 release gate。
