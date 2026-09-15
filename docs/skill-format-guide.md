# Skill 格式指南

## 目标

`SKILL.md` 是 Skill 被选中后的精简 capability instruction，不是 prompt 仓库、岗位百科或机器权限清单。稳定 discovery 信息放 frontmatter，复杂 routing/permission/eval policy 由 `manifest.json` 与 `manifests/skill_content_contracts_v2.json` 承担，长知识按需进入 references/scripts/assets。

## Portable frontmatter

必须至少有：

```yaml
---
name: adk-example
description: 说明做什么、何时使用，以及与近邻能力的关键边界
---
```

ADK authoring 可以继续使用：

- `triggers`
- `non_triggers`
- `inputs`
- `outputs`
- `constraints`
- version/freshness metadata

但 frontmatter 不承载 nested permission、approval、selection graph 或完整 workflow state。机器策略放 typed contract。

## Description 触发质量

`description` 是运行时 discovery 第一层，必须表达 **what + when + boundary**：

- 前半句优先放任务场景和结果，catalog 被截断时仍有路由价值。
- 避免“优化流程”“提升质量”等泛化描述。
- 写清与相邻 Skill 的近邻边界，例如分析 vs 实现、验证 vs review、context planning vs token governance。
- 与 `triggers/non_triggers`、manifest routing 和 v2 runtime role 一致。
- 高风险 Skill 描述执行边界，但不得把 description 写成授权声明。
- 新增或大改 Skill 必须有 positive、near-miss negative 与 collision/abstain evidence。

## Body 按 capability class 设计

不再强制所有 Skill 使用一套 headings。`manifests/skill_content_contracts_v2.json` 的 `capability_class` 决定推荐结构。

### task
适合有明确任务结果的能力：
- Goal / Use When
- Prerequisites
- Workflow
- Failure / Escalation
- Output / Evidence

### workflow
适合多阶段推进：
- Goal
- State Model / Entry Conditions
- Transitions / Checkpoints
- Stop / Replan / Resume
- Completion Evidence

### guardrail
适合约束与门禁：
- Protected Boundary
- Policy
- Trip Conditions
- Enforcement Level
- Exceptions / Approval
- Evidence

### tool
适合 deterministic wrapper：
- Tool Contract
- Input Validation
- Execution
- Exit/Failure Semantics
- Security / Side-effect Boundary

### support / knowledge
只保留 primary capability 需要的支持信息、转换规则和 reference pointers；默认不得与 task/workflow 争抢 primary。

### meta
用于 runtime/control-plane，例如 router；必须保持入口紧凑，把 catalog/tool details progressive-disclosure 到 references 或 machine contract。

## references / scripts / assets

推荐目录：

```text
skills/<skill-name>/
├── SKILL.md
├── references/      # 长知识、命令模式、案例、历史说明
├── scripts/         # 重复、确定性动作
└── assets/          # 输出模板/资源；需要时才加载
```

原则：
- `SKILL.md` = 被激活后立即需要的信息。
- `references/` = 按问题深度读取，默认不进 always-loaded context。
- `scripts/` = deterministic/repetitive action，稳定 stdout/exit semantics。
- `assets/` = 输出生成所需资源，不作为知识上下文默认读取。

不再以“140 行”作为唯一质量定义；入口仍应短小，但由 token/byte ratchet、progressive disclosure 和 behavior eval 联合判断。长背景、完整日志、平台教程和大样例不能为了凑模板塞回 SKILL.md。

## Machine contract 边界

`manifests/skill_content_contracts_v2.json` 从 manifest identity 派生：

- capability class
- runtime role (`primary|supporting|governance|fallback`)
- selection group
- effect ceiling
- eval obligations

`effect_ceiling` 是上限，不是授权。Skill 能描述“如何执行”，但真正 side effect 还必须满足 Agent permission、tool/runtime guardrail 与必要 approval。

不得为每个 Skill 复制第二份 path/description/category identity catalog；Manifest 始终是 SSOT。

## Progressive disclosure

推荐加载次序：

1. catalog：name + description + lightweight runtime metadata。
2. 选中后：`SKILL.md`。
3. 需要深入时：specific reference / script / asset。
4. 高风险或争议结论：evidence L3/raw pointer。

不把完整 Skill procedure 复制到全局系统提示或 Agent 文件来“提高命中率”；路由问题优先修 description、typed selection metadata 和 eval cases。

## Skill / Plugin / Tool 分发边界

- Skill：可复用 capability/method。
- Workflow：跨阶段 composition/state。
- Tool：执行能力。
- Plugin/connector：安装/外部系统分发边界。
- Agent：运行责任和 authority。

需要 MCP、hook、connector、credential 或 native runtime 时，Skill 只声明依赖与边界；安装和授权必须经过独立 supply-chain/runtime governance，不因 Skill 被选中自动启用。

## 外部 Skill

外部 Skill 先进入 method-only intake；审查 provenance、version、license、trigger quality、重复能力、side effects 与 rollback，再决定 ADOPT/MERGE/ENHANCE/OBSERVE/REJECT。第三方格式兼容不等于生产信任。

## Eval minimum

大改 Skill 至少证明：
- should-trigger / positive
- near-miss should-not-trigger
- sibling collision
- abstain/fallback（适用时）
- behavior/evidence contract
- authority/permission negative（有 side effect 时）

Token 下降可记录为 efficiency observation，但不能替代 task success 与安全/authority evidence。

## 运行时分层

Skill 只定义能力方法；Agent 持有运行责任与 authority；Sub-agent 使用 typed handoff 接收范围受限任务；Workflow 管理 state；MCP/tool 只提供外部能力接口。完整模型见 `docs/skill-agent-runtime-model.md`。
