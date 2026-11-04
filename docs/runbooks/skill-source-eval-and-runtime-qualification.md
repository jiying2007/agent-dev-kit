# Skill 评测：源码级基线与真实运行效果分离

## 适用边界

- 离线基线：`tests/fixtures/skill_trigger_cases.tsv` 和 `skill_catalog_competition.tsv`；覆盖孤立正/反例、全目录竞争、否定与 abstain。由 `tests/test_skill_trigger_matrix.py` 执行；最低总数 100。**这只证明 ADK 自身确定性 matcher。**
- 真实运行时：在明确允许的目标平台下采集真实 discovery、load、trigger、权限拒绝和回退路径。当前 `claude-code` / `opencode` 仍为 experimental，缺少受信任 authority 时不得提升 conformance。
- 效果对照：候选 Skill vs 基线，预先冻结任务、模型、预算和版本，分别记录成功率、错路由、漏路由、abstain、工具调用、耗时、token 消耗、失败类型及复现路径。**未执行模型实验时为 not_evaluated，不是 pass。**
- Product / field：组件发布与真实产品资格、长期现场证据分别判定；不得继承。

## 如何运行离线基线

```bash
PYTHONPATH=src python3 -m unittest tests.test_skill_trigger_matrix tests.test_skill_content_contract
```

若测试使用 `unittest` 模块搜索方式，在源码根目录执行；不要依赖外部模型、凭证或用户的 Codex/Work 配额。CI 的 Python 3.11/3.12 全量合同门禁仍为最终源码级验收依据。

## 后续真实实验（按需、显式预算）

1. 从实际用户意图中登记不少于 60 个任务，涵盖中文、英文、否定、权限阻止、错误工具、成功交付及恢复；去重并审查敏感数据。
2. 固定 exact ADK source、target/runtime binary、模型版本、资产集合、输入快照、温度、次数、超时及美元/token/运行时预算；至少 3 次重复对照，样本不足明确记 not_evaluated。
3. 收集真实 trace 与产物；区分 `invoked`、`routed_correctly`、`task_succeeded` 和 `resource_cost`，不能让自述代替观测。
4. 生成每个 Skill/Agent/Profile 的带来源判定及反例；由独立审查复核，不能按缺失证据退休资产，也不能把静态 100 例声称为真实效能结果。
5. 只有具备经授权的无额外付费运行环境时才执行真实模型实验；缺条件保持 pending，不自动调用计费提供商。

参考：https://developers.openai.com/blog/eval-skills
