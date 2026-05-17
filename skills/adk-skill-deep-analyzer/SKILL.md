---
name: adk-skill-deep-analyzer
description: 从产品视角深度拆解 AI Skill 的设计意图、独特解法和可借鉴模式
version: 1.0.0
last_updated: 2026-05-16
triggers:
  - 深度拆解 skill
  - 分析 skill 设计
  - 提取设计模式
  - skill 产品视角分析
non_triggers:
  - 编写新 skill
  - 修改现有 skill
inputs:
  - repo_path: 目标仓库路径
  - skill_name: 可选，指定分析某个 skill
outputs:
  - deep_analysis: Skill 深度分析报告 (Markdown)
constraints:
  - 禁止直接引用 description 字段，必须从实现细节反推
  - 每个解法必须提供"通用做法 vs Skill 做法"对比
  - 5 维评分必须给出具体证据
---

# 分析仓库的 prompt 结构

## Goal

## Prerequisites

- 理解相关领域的基本概念
- 熟悉项目结构和工作流程
- 具备基本的文档编写能力

从产品视角深度拆解目标仓库中的 Skill 设计，提炼可复用的设计模式和最佳实践。


## Workflow

<what-to-do>


## Quality Gate
- 分析报告必须包含具体文件/行号证据
- 禁止直接引用 description 字段，必须从实现反推
- 5 维评分每项必须给出≥1个具体证据
- 输出报告必须包含"可借鉴点清单"章节


## Evidence Template

```md
status: pass | needs-fix | BLOCKED
commands:
- <command + exit code>
evidence:
- <path or output summary>
risks:
- <remaining risk or none>
```

## References
- 详细背景、命令、模板、示例和扩展检查项保存在 `references/details.md`。
- 入口文件只保留触发和执行所需的最小上下文，避免默认加载过多 token。
