# Skill 格式指南

## SKILL.md 规范

SKILL.md 是 skill 的入口文件，应保持精简（严格门禁 ≤140 行）。它是写给 Agent 的岗位 SOP 入口，不是 prompt 仓库，也不是长篇百科。

### 必需章节
1. YAML frontmatter (name, description, triggers, non_triggers)
2. 核心流程（步骤化）
3. 输出契约

### 可选章节
- 合理化借口拦截
- 健壮性规范
- 示例

### Description 触发质量

`description` 会参与运行时 discovery，必须写成“何时使用 + 产出什么”的短句，而不是泛化能力名。

要求：
- 把最关键的使用场景放在前半句；skill 列表被截断或缩短时，仍能保留可路由信息。
- 具体说明任务场景，避免“优化流程”“提升质量”这类空泛描述。
- 能与相邻 skill 区分，避免多个 skill 同时争抢 primary。
- 与 `triggers`、`non_triggers` 和 `manifest.json` routing 语义一致。
- 不得包含 `TODO`、`TBD`、`待补充`、`示例技能` 等占位内容。
- 高风险 skill 应在 description 或 constraints 中体现运行边界。
- 如果 skill 需要 MCP、hook、CLI、外部服务或写操作，description 不直接承诺权限；权限边界进入 manifest、runbook 或 `agents/openai.yaml` 依赖声明。

示例：
- 好：`完成前验证门禁，确保交付声明与证据一致`
- 差：`验证优化`

## references/ 子目录

当 SKILL.md 接近 140 行时，将详细参考资料拆分到 references/ 子目录：

```
skills/<skill-name>/
├── SKILL.md           # 精简入口（触发条件 + 核心流程）
└── references/
    ├── patterns.md    # 详细模式库
    ├── checklist.md   # 检查清单
    └── examples.md    # 示例代码
```

### 原则
- SKILL.md = Agent 需要立即知道的信息
- references/ = Agent 按需查阅的详细信息
- 减少 token 消耗，提高上下文效率
- 官方 Codex skills 模型可作为渐进式披露参考：初始上下文只暴露名称、description 和路径；完整 `SKILL.md` 只在选中 skill 后读取。adk skill 设计必须保持入口可短读，避免把长案例、历史证据和平台教程塞进入口文件。
- 大 skill 生态按 `manifests/tool_search_contracts.json` 的 lazy-loading 契约治理：初始只暴露 namespace/skill 摘要，命中后再读取 `SKILL.md`、references、scripts 或 assets。
- 需要 MCP 或外部工具的 skill 必须区分“发现用摘要”和“执行用 schema”；延迟加载不能绕过 tool approval、auth boundary 或安全审查。
- 生产使用的 skill 必须按 `manifests/skill_reproducibility_contracts.json` 固定版本，并记录兼容的模型/运行态假设、验证命令和回滚路径；开发期使用 `latest` 也必须有 freshness review。
- 带脚本的 skill 按 tiny CLI 方式设计：可从命令行运行、stdout 稳定、失败时明确报错、输出路径可预期；需要网络时补 allowlist、数据外发规则和 approval boundary。
- 路由不稳定时优先迭代 `description`、`triggers/non_triggers` 和正反例，不把完整 skill 流程复制到全局系统提示词里。

## Skill / Plugin 分发边界

- Skill 是可复用 workflow 的作者格式，优先承载方法、输入输出、失败收口和验证要求。
- Plugin 是安装和分发边界，只有在需要打包多个 skill、MCP、hook、app、native 依赖、凭证或 marketplace 元数据时才晋级。
- 本地试验期优先保持 repo/user skill；完成触发准确率、重复能力检查、pilot 证据和回滚方案后再考虑 plugin。
- `agents/openai.yaml` 只放 UI 元数据、隐式触发策略和工具依赖声明；不替代 `SKILL.md` 的执行契约，也不直接授予运行权限。

## 运行时分层

Skill 只定义“应该怎么做”；Agent 负责运行时执行和调度；Sub-agent 是被拆分出去的短生命周期执行实例；MCP/tool 只提供外部能力接口。完整分层见 `docs/skill-agent-runtime-model.md`。

---

## 增强格式：XML 语义标签（可选）

> 来源: mattpocock-skills 的 `<what-to-do>` / `<supporting-info>` 创新

在传统 Markdown 标题结构之上，增加 **XML 语义标签**，让 AI Agent 能精确区分"必须做什么"和"参考信息"。

### `<what-to-do>` — 核心行为指令

包裹 Agent 必须执行的动作。这是 SKILL.md 的"执行层"。

```xml
<what-to-do>
## 目标
[一句话描述目标]

## 步骤
1. [必须执行的动作]
2. [必须执行的动作]

## 约束
- [不可违反的规则]
</what-to-do>
```

### `<supporting-info>` — 支撑参考信息

包裹前置条件、背景知识、参考链接等。这是 SKILL.md 的"上下文层"。

```xml
<supporting-info>
## 前置条件
- [需要的环境/工具]

## 参考资料
- [相关文档链接]

## 历史决策
- [为什么这样做]
</supporting-info>
```

### 格式层次对照

| 层次 | 格式 | 用途 |
|------|------|------|
| 人类阅读 | `## 标题` | 章节结构，快速浏览 |
| Agent 解析 | `<what-to-do>` | 核心指令，必须执行 |
| Agent 解析 | `<supporting-info>` | 参考信息，按需加载 |

### 迁移指南

现有 SKILL.md 不强制改造，但新增或大改的 SKILL.md 应采用增强格式。

### 增强格式最小示例

```markdown
---
name: adk-example-skill
description: 示例技能
---

<what-to-do>
## Goal
验证增强格式是否正常工作

## Steps
1. 检查 frontmatter
2. 检查 what-to-do 标签
3. 检查 supporting-info 标签
</what-to-do>

<supporting-info>
## Background
此格式来源于 mattpocock-skills 的实践。
</supporting-info>
```
