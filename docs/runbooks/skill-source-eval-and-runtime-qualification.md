# Skill 评测：源码级基线与真实运行效果分离

## 适用边界

- 离线基线：`tests/fixtures/skill_trigger_cases.tsv` 和 `skill_catalog_competition.tsv`；覆盖孤立正/反例、全目录竞争、否定与 abstain。由 `tests/test_skill_trigger_matrix.py` 执行；最低总数 100。**这只证明 ADK 自身确定性 matcher。**
- 真实运行时：在明确允许的目标平台下采集真实 discovery、load、trigger、权限拒绝和回退路径。当前 `claude-code` / `opencode` 仍为 experimental，缺少受信任 authority 时不得提升 conformance。
- 效果对照：常规改版采用现行 Skill（champion/baseline）vs candidate；首次证明价值或调查负收益时另设 no-skill 组。冻结任务、模型、预算和版本，记录成功率、错/漏路由、abstain、实际成本和失败证据。**未执行模型实验时为 not_evaluated，不是 pass。**
- Product / field：组件发布与真实产品资格、长期现场证据分别判定；不得继承。

本页的评测证据 E0/E1（静态）、E2（模型行为）、E3（原生宿主）、E4（端到端）与路由的执行投入 `execution_effort=E0/E1/E2/E3` 是两个维度。前者回答已观察到什么，后者限定执行深度；同号不能互换，也都不授予写权限。不改已有协议编号或新增映射状态。

## 开发、选型与冻结验收

| 用途 | 案例与结论边界 |
|---|---|
| 开发定位 | 使用已有失败与成功案例，按影响补最小正/反例；2–3 个探索例可定位问题，不能证明正式资格、普遍收益或统计显著性。 |
| 候选选型 | 固定开发/验证分组、预算、grader 和重复规则，比较现行与候选；保留失败、否决及环境差异，不从未完成结果中挑赢家。 |
| 冻结验收 | 候选冻结后使用独立未曝光 holdout，执行适用 campaign 的原有门槛与独立审核；已向作者曝光的案例回归开发用途，不再称为独立最终留出集。 |

样本和重复次数按变更影响、失败变异与既有 campaign 预注册，不把小改一律扩成全资产实验。全资产资格仍执行下节不少于 60 任务、至少 3 次重复；交互式发现沿用其专门协议；`skill_method_ab_prereg.json` 等既有预注册门槛不得由本页缩减。登记与描述用例不等于已执行模型试验。

## 如何运行离线基线

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_trigger_matrix tests.test_skill_content_contract
```

若测试使用 `unittest` 模块搜索方式，在源码根目录执行；不要依赖外部模型、凭证或用户的 Codex/Work 配额。CI 的 Python 3.12 全量合同门禁仍为最终源码级验收依据。

## 全资产真实资格 campaign（按需、显式预算）

1. 从实际用户意图中登记不少于 60 个任务，涵盖中文、英文、否定、权限阻止、错误工具、成功交付及恢复；去重并审查敏感数据。
2. 固定 exact ADK source、target/runtime binary、模型版本、资产集合、输入快照、温度、次数、超时及美元/token/运行时预算；至少 3 次重复对照，样本不足明确记 not_evaluated。
3. 收集真实 trace 与产物；区分 `invoked`、`routed_correctly`、`task_succeeded` 和 `resource_cost`，不能让自述代替观测。任务预算耗尽计入失败分母；采集故障单列无效评测并按预注册规则成对重跑，不能选择性丢弃失败。
4. 先判质量和权限不退化，再比较实际 Token、工具调用、耗时与返工；缺失用量记 unavailable。生成各资产的来源判定及反例，由独立审查复核；不能按缺失证据退休资产，也不能把静态 100 例声称为真实效能结果。
5. 只有具备经授权的无额外付费运行环境时才执行真实模型实验；缺条件保持 pending，不自动调用计费提供商。

证据存入现有 change/effect 记录；七字段见 [方法记录](practice-source-governance.md)，执行细则见 [行为评测](../../optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md)。外部参考 URL 仅供查阅，采纳依据需记录确切版本或内容摘要：https://developers.openai.com/blog/eval-skills
