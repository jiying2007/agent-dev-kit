# 四层分离架构模式

> 参考归档：本文记录外部架构模式，正式采纳前必须改写为 adk 本地目录、命令和门禁。

**来源**: superpowers-openspec-team-skills
**提取日期**: 2026-05-13
**适用场景**: 需要支持多 AI 工具的技能库架构

---

## 问题

当技能库需要支持多种 AI 工具（如 Codex、Claude Code、Cursor）时，如何组织代码以避免：
- 重复维护相同的逻辑
- 工具特定的代码污染通用逻辑
- 用户难以找到正确的入口

## 解决方案

采用四层分离架构：

```
project/
├── team-skills/     # 第1层：源码级 workflow 定义（维护者面向）
├── dist/            # 第2层：工具级 bundle（用户面向）
├── templates/       # 第3层：可复用模板
└── scripts/         # 第4层：自动化脚本
```

## 各层职责

### 第1层: team-skills/（源码层）

**面向**: 维护者
**职责**: 定义 workflow 的核心逻辑
**特点**:
- 工具无关的通用定义
- 包含完整的 SKILL.md 和 README.md
- 可能包含额外的依赖和说明

```markdown
# team-skills/superpowers-feature-workflow/SKILL.md
---
name: superpowers-feature-workflow
description: Use when feature work needs...
---

# Superpowers Feature Workflow

## Workflow
1. Explore project context...
2. Clarify requirements...
```

### 第2层: dist/（分发层）

**面向**: 用户
**职责**: 提供可直接安装的工具特定 bundle
**特点**:
- 已适配特定工具的格式（如 Codex SKILL.md、Claude Code CLAUDE.md）
- 包含 manifest.json 描述安装信息
- 可能精简了源码层的某些内容

```json
// dist/codex/bundles/superpowers-feature/manifest.json
{
  "name": "superpowers-feature",
  "tool": "codex",
  "type": "bundle",
  "installTarget": ".codex/skills",
  "contents": ["skills/superpowers-feature-workflow"]
}
```

### 第3层: templates/（模板层）

**面向**: 用户和维护者
**职责**: 提供可复用的配置和结构模板
**特点**:
- 标准化的目录结构
- 可直接复制使用的配置文件
- 支持自定义和扩展

```markdown
# templates/superpowers-memory/PROJECT_CONTEXT.md
# Project Context

Use this file for stable project knowledge...

## Project Summary
- What this project does:
- Who uses it:
```

### 第4层: scripts/（脚本层）

**面向**: 用户和 CI/CD
**职责**: 提供自动化操作
**特点**:
- 安装脚本（install-*.sh）
- 验证脚本（validate-*.sh）
- 记忆管理脚本（*-superpowers-memory*.sh）

```bash
# scripts/install-codex.sh
#!/bin/bash
# Install Codex bundle
...
```

## 优势

1. **关注点分离**：维护者和用户有不同的入口
2. **多工具适配**：dist/ 为每种工具生成特定格式
3. **模板复用**：templates/ 提供标准化配置
4. **自动化支持**：scripts/ 简化安装和验证
5. **易于扩展**：添加新工具只需在 dist/ 中添加新的 bundle

## 适用场景

- ✅ 需要支持多 AI 工具的技能库
- ✅ 需要标准化配置的项目
- ✅ 需要自动化安装验证的场景
- ❌ 只支持单一工具的简单项目
- ❌ 不需要模板复用的场景

## 与 llm_agent 的集成

在 llm_agent 中，可以采用类似的结构：

```
llm_agent/
├── skills/                    # 源码层（Hermes Agent skills）
│   ├── superpowers-feature/
│   └── superpowers-learning/
├── dist/                      # 分发层（多工具 bundle）
│   ├── codex/
│   ├── claude-code/
│   └── cursor/
├── templates/                 # 模板层
│   └── superpowers-memory/
└── scripts/                   # 脚本层
    ├── install-*.sh
    └── validate-*.sh
```

## 实现建议

1. **源码层保持通用**：不包含工具特定的代码
2. **分发层自动生成**：从源码层构建，避免手动同步
3. **模板层版本化**：跟踪模板的变更历史
4. **脚本层幂等性**：支持重复执行，不产生副作用

## 参考

- 来源: superpowers-openspec-team-skills 仓库结构
- 相关模式: 显式启用型工作流
