# Skill 格式指南

## SKILL.md 规范

SKILL.md 是 skill 的入口文件，应保持精简（默认门禁 ≤140 行）。

### 必需章节
1. YAML frontmatter (name, description, triggers, non_triggers)
2. 核心流程（步骤化）
3. 输出契约

### 可选章节
- 合理化借口拦截
- 健壮性规范
- 示例

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
