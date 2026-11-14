# 第三轮外部 Skill 方法吸收：面向真实执行而非扩大清单（2026-11-14）

本轮公开源仅作为**不可信只读参考**；单文件 Git blob 用于回查内容身份，不能代表整个仓库 commit、可再分发许可、安全认证或模型实测。不执行任何来源中的安装命令、脚本、MCP、远程依赖或付费评测。

| 来源及核验文件 | Git file blob（短） | 真正可迁移的方法 | ADK 的最小决策 |
|---|---|---|---|
| [Microsoft Waza Runner](https://github.com/microsoft/waza/blob/main/waza-runner/SKILL.md) | `453cb55a3bbe` | 每个场景定义输入、grader、运行结果；mock/offline harness 与真实任务质量分开 | **RETAIN** 已有 `effect_trials`/CI；不引入第二套 CLI |
| [NVIDIA SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator/blob/main/README.md) | `eadf78a0a19e` | changed-skill 质量门禁与有/无 Skill 实际执行效果分层 | **RETAIN** ADK E0/E1 与 E2–E4 资格分离；不默认安装扫描器 |
| [Alibaba skill-upper](https://github.com/alibaba/skill-up/blob/main/skills/skill-upper/SKILL.md) | `85898ca3c9df` | 从归属明确的观察反馈生成可复现回归，再按隔离环境评测差异 | **ENHANCE** 已有 Skill lifecycle 和 behavior-eval reference；来源可为外部用户提供的可信 trace，不能未授权自动录屏/捕获 |
| [Superpowers executing-plans](https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md) | `ea23196d7450` | 已批准计划的 inline 实现、逐项验证、偏差裁决 ledger、末尾整体 review，减少每任务多 Agent/重读 | **ENHANCE** `adk-planning-execution-loop`；权限扩大与不可逆动作仍按原规范暂停 |
| [Superpowers systematic-debugging](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md) | `62fc752aaef5` | 根因先于修复，最小验证、跨层边界定位、三次失败后质疑假设 | **RETAIN** `adk-systematic-debugging` 已有最短反馈、单变量、两次无增益 replan，避免再加平行流程 |

## 经实际 ADK 源码确认的缺口

1. **真实指令路由**：`全网搜索优质 Skills` 有现成的 read-only 入口，但“继续吸收外部成熟方法，提升已有 Skills 的实际执行效果”未被已有实用路由用例覆盖。
2. **Optional negation 回归盲区**：既有 catalog competition 测试在核竞争 Skill 时固定使用 Core `scope=skill`；对 Optional Skill 会因查无文件而 trivially false，无法证明原生 matcher 的 Optional 否定匹配正确。本轮按目标注册身份选择 `optional-skill`/ `skill`，并加入实际语言输入。
3. **研究→实施 handoff**：来源已冻结、目标已有清晰批准范围时，重复广域研究和一源一立项会占用上下文，难以推进交付。本轮 `scoped-adoption` 优先复用 ledger、合并同一受保护变更的相关工作； `source-only` 仍只读。已批准 implementation 不再重启外部 intake。
4. **Goal 费用与完成率**：采用 inline fast path 和批末独立 review；计划与源码冲突时记带证据的局部 ruling，不隐式扩大权限或修改 acceptance。不得把空 heartbeat、模板或权限推断视为交付。
5. **效果证据隔离**：已有 `effect_trials` 的真实 run 仍需同起点 workspace 与可观察的 tool trace；只校验最终文件状态不能证明过程无越权。没有合格真实宿主数据，保持 `E2–E4=not-measured`。

## 本轮测试

- `tests/fixtures/skill_catalog_competition.tsv`: 新增 R039–R041，覆盖吸收继续执行、纯研究、明确否定。
- `tests/fixtures/skill_trigger_cases.tsv`: 真实语言的 Optional Skill 正反例 + Core Skill 研究例。
- `tests/test_skill_trigger_matrix.py`: 将竞争测试覆盖到正确的 Optional `scope`，跑**生产 Matcher 本身**，而不是只核包含特定词。
- `tests/test_external_method_intake.py`: 合同边界检查，不代替生产路由测试或模型行为证据。

## 结果边界

**当前为 PR 候选**，能由 CI 证明的是源约束、生产 Matcher 路由/否定和完整回归（E0/E1）。真实模型能否正确触发、一次交付率、令牌/调用与延迟变化，需按相同真实宿主和 frozen baseline/candidate 重复对照；不得以这些路由测试声称完成 E2–E4，也不得把未执行称为通过。保留单一 Manifest/Router/effect_trials、65 Skill 身份、原权限、受保护 PR 流程。
