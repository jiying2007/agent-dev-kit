---
name: adk-structured-requirements-questioning
description: "用于头脑风暴、brainstorming、Grill Me、方案拷问、苏格拉底式追问；以 Explore/Challenge 多轮探索意图、方案和决策依赖。不用于已有明确方案的直接实现、普通验收整理或文档润色。"
version: 1.2.2
last_updated: 2026-11-16
triggers:
  - "头脑风暴"
  - "脑暴"
  - "brainstorm"
  - "brainstorming"
  - "grill me"
  - "gill me"
  - "方案拷问"
  - "挑战方案"
  - "苏格拉底式追问"
  - "深度追问"
  - "先发散再提问"
non_triggers:
  - "已有完整方案按计划直接执行"
  - "只执行已有任务包"
  - "纯文档润色"
  - "只运行测试"
inputs:
  - "用户意图、既有决策和代码、约束、证据"
outputs:
  - "确认的设计取舍、未决依赖、反例与验收交接"
constraints:
  - "read-only；不授予实现、设备、发布或额外外部操作权限"
  - "不得冒充用户已确认，不重复已知问题或无限追问"
---

# 交互式设计探索

## Goal
发现真实需求、比较方案并证伪关键风险；使用本原生 Skill，不加载外部 Skill。

## Look before asking
先读原请求、既有批准、源码和测试；事实自己查，区分事实、用户决定、AI 建议与未知。仅问能改变设计的问题；“直接做”且范围明确时退出，不重开访谈。

## Explore protocol
“头脑风暴 / brainstorm”或 Why 未明时，**每轮一个关键问题**：先开放询问目标/受益者，再依据回答追问，不先给诱导选项。意图明确后比较 2–3 个可行方向的收益、成本、失败条件与推荐；仅一路可行则说明。阶段性核对设计与未决项，接受纠正。

## Challenge protocol — decision tree
“Grill Me / 拷问 / 挑战方案”时，为重要决策记录 id、依赖、备选、证据与状态 confirmed / proposed / unresolved / invalidated。**Frontier** 仅含依赖已解决的未决节点；每轮问独立 frontier（通常 2–4 题），列建议、依据和反例，回答后重算。关注性能、成本、安全、兼容、资源和恢复风险，不凑题、不先问下游。“都按建议”仅确认本轮明示选择。

**部分回答与修订**：沿用问题 ID/原义，不回收或重编号；保留 `depends_on / status / answer_source`。未答保持 unresolved，不默认为同意；查证未返回只挂起依赖分支，独立项可继续。答案对应含糊只澄清该项。上游修订保留旧答案/来源，受影响下游置 invalidated 后重判。用户委托判断的结果标 AI 建议，不能冒充用户确认或新增写权限。

## 可抛弃原型（条件性）
状态机或交互可用性难以口头判断时，提出可证伪问题和最小原型，按需读 `references/prototype-as-experiment.md`。本 Skill 只读；写文件/外部工具仍走已有授权实施流程。

## Cross-mode convergence
用户可切换或停止；连续两轮无新证据/决策则给推荐或最小实验。结束时交付设计、User-confirmed decisions、AI 建议、开放问题、反例与验证路径；仅确认内容交 `adk-requirements-triage`，实现仍遵守原授权和工程门禁。

## 结果导向的设计探索（不增加固定轮次）
- **证据先行**：从现有调用方、代码/日志、历史方案和验收反例提取约束；可从来源证明的事实不再询问用户。对“直接落地”与已决定的设计不重启 Explore。
- **候选可区分**：当决策尚未收敛，提供至少两种真正不同的可行边界；每项注明适用条件、成本、会失败的场景、可逆性和最小验证信号。不为凑数制造方案；仅一路可行应解释排除理由。
- **有用的问题才问**：每个开放问题都标明“哪个决策将因答案改变”；无需答案亦可安全推进时，给可逆假设和建议而不是阻塞。
- **反证优先**：至少检验一项可能推翻推荐的负例（预算、跨端协议、断网恢复、制造/验证限制等）；若缺实测证据标 UNKNOWN。
- **交接**：用一页以内的 `problem / alternatives / falsifier / evidence / decision-source / next-test` 输出；确认的行为需求可进入现有 Canonical Change Contract。提出方案不授予写入、设备或发布权限。
- **退出**：问题答案不改变方案、两轮无新证据、已有批准路径或用户要求停止时，立即收敛为建议/最小实验。不把提问数量当成果。

## Quality Gate
Explore 先 Why 后选项；Challenge 遵守依赖，不重复历史。真实多轮效果按源码评测协议 `docs/evals/interactive-discovery-evaluation.md` 独立盲测，静态路由通过不等于效果认证。
