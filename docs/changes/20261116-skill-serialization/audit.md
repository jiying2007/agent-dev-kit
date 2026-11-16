# 全体 Skill 增量复查与外部对照

本轮承接已合并的 v11.3.10（PR276）。此前五项修复的全量证据见 `../20261116-skill-failure-paths/`：19 个固定仓库与 6 个官方网页、54 个去重文件/页面。当前重新审查 65 个入口；没有声称穷尽互联网上所有 Skill。

## 实际覆盖

独立只读审计 `portfolio_optimization` 全文重读 65 个 SKILL.md：34 个通用核心、22 个嵌入式核心、9 个可选；定向全文重读 14 份 bundled reference。153 个资产、422513 bytes 的清单与摘要机械对账，49 条入口内直接 reference 路径缺失 0。153 个文件的哈希不等于本轮全文阅读，准确范围与逐 Skill 判断见 `evidence/portfolio-audit.json`。

该审计以 v11.3.10 的 `fa012817` 树为对象（与合并后的 `b20df018` 同树），结论 62 KEEP / 3 OBSERVE，没有证明新的通用或嵌入式缺陷；不构成对本轮 serializer 修改的批准。单独的外部方法研究发现隐式序列化缺口，作为本变更唯一 ENHANCE 候选。

Goal/Loop 已有状态变化触发、当前身份的验证复用、1–4 个交付批次、最多 3 个下一动作、8 KiB 恢复输出和按收益决定并行。本轮保留这些控制，不把源码字节或静态规则写成真实 Token、成本和时延收益。

三项已知观察继续保留：E1 需要可信低风险来源及拒绝路径；旧 worktree 冲突模板的真实消费未证实；多人累计 human_active_minutes 口径缺少生产方证据。另排除了 goal_ref 必须等于计划路径的误判：原设计允许引用需求文件。

## 外部候选决定

固定提交、文件路径和本轮 GitHub 回读的 blob identity 见 `evidence/external-sources.json`。仅吸收方法，不导入上游完整正文、脚本或依赖。

| 来源 | 决定 | 本轮依据 |
|---|---|---|
| Sentry secret-serialization，`a582c51ee29d0f35e6ac321340796f77d43da733`，Apache-2.0 | ENHANCE | 标准库反例证明 repr 隐藏与 asdict 输出保护不同；已有供应链参考缺具体路径，补 holder/serializer/sink 与合法字段控制 |
| Addy Osmani evals，`39b723ceebf81474d0557c1fecd01eddab585563`，MIT | KEEP / OBSERVE | expected owner/collision 已覆盖；真实执行流 terminal 与 grader identity 待实际 adapter 场景，不新增第二评测引擎 |
| Anthropic Skill Creator analyzer，`1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064`，具体 Skill Apache-2.0 | KEEP | ADK 已有训练/留出、盲评、负控制、固定试验与成本归因；缺真实观测不能靠重写流程补齐 |
| Matt Pocock writing-for-agents，`5863806dd4e15c63174bee4e7515a4256792ecfa`，MIT | KEEP | 按分支读取参考、条件入口和减少重复已有覆盖；只对当前具体缺口补导航 |
| Superpowers review-package，`22f0b463e7a5e579904dd6211a520321035526f7`，MIT | OBSERVE | ADK 使用固定 HEAD/merge-base；直接强加 base 是祖先会错拒分叉 PR，未证明空 diff 导致实际放行缺陷 |

Python 官方 `dataclasses.field` 与 `dataclasses.asdict` 文档核验了 repr 与递归转换语义。上游许可由研究者实际读取；Anthropic 根 LICENSE 路径失败后读取具体 Skill 的许可，不能推断整仓许可一致。部分 immutable GitHub 页面在网页工具不可读，GitHub connector 的精确 ref 文件回读成功，失败不改写为成功。

## 验证边界

本轮有合成方法反例、发布示例执行和独立源码消费者任务；没有付费模型 A/B、真实 Token/成本/时延、设备/HIL、生产运行态 discovery/load/trigger 或 M5 新资格。普通用户使用 Skill 不需要运行 ADK 的源码发布检查。
