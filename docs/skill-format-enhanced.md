# SKILL.md 格式增强规范

> 来源: mattpocock-skills 的 `<what-to-do>` / `<supporting-info>` 创新

## 核心改进

在传统 Markdown 标题结构之上，增加 **XML 语义标签**，让 AI Agent 能精确区分"必须做什么"和"参考信息"。

## 标签规范

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

## 与传统格式的关系

| 层次 | 格式 | 用途 |
|------|------|------|
| 人类阅读 | `## 标题` | 章节结构，快速浏览 |
| Agent 解析 | `<what-to-do>` | 核心指令，必须执行 |
| Agent 解析 | `<supporting-info>` | 参考信息，按需加载 |

## 迁移指南

现有 SKILL.md 不强制改造，但新增或大改的 SKILL.md 应采用增强格式。

### 最小示例

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

## Related
- docs/skill-format-enhanced.md
</supporting-info>
```
