# 显式启用型工作流模式

> 参考归档：本文记录外部工作流模式，正式采纳前必须改写为 adk 本地触发词、profile 和门禁。

**来源**: superpowers-openspec-team-skills
**提取日期**: 2026-05-13
**适用场景**: AI 编程助手的复杂工作流管理

---

## 问题

AI 工具的 workflow 不应成为默认后台行为，否则会：
- 干扰用户的正常工作
- 增加不必要的认知负担
- 可能产生意外的副作用

## 解决方案

所有 workflow 都是"显式启用型"，遵循以下原则：

1. **安装 ≠ 启用**：安装只是让能力可用
2. **显式调用才启用**：只有当用户明确要求、明确点名，或仓库策略明确要求时才启用
3. **明确声明**：SKILL.md 中声明 "This is an explicit opt-in workflow"

## 实现方式

### 方式 1: 通过 workflow 名称显式激活

```text
Use $superpowers-feature-workflow for this feature.
```

### 方式 2: 通过 AGENTS.md 意图路由表

```yaml
# AGENTS.md 意图路由表
- 触发词: "brainstorm", "plan before coding", "TDD"
  动作: 加载 superpowers-feature-workflow
  技能: $superpowers-feature-workflow
```

### 方式 3: 通过仓库策略

```yaml
# .repo-policy.yaml
workflows:
  superpowers-feature:
    auto_activate: false
    required_for: ["feature-requests", "bug-fixes"]
```

## 代码示例

### SKILL.md 声明

```markdown
---
name: superpowers-feature-workflow
description: Use when feature work needs the Superpowers stages...
---

# Superpowers Feature Workflow

## Overview

This is an explicit opt-in workflow. Do not use it by default.
Only use it when the user explicitly asks for this workflow,
names this skill, or a repository policy explicitly requires it.
```

### 激活检查

```python
def should_activate_workflow(workflow_name: str, context: dict) -> bool:
    """检查是否应该激活工作流"""
    # 1. 用户显式请求
    if workflow_name in context.get('explicit_requests', []):
        return True

    # 2. 仓库策略要求
    if context.get('repo_policy', {}).get(workflow_name, {}).get('required'):
        return True

    # 3. 默认不激活
    return False
```

## 适用场景

- ✅ 复杂的多阶段工作流（如设计→计划→实现→验证）
- ✅ 需要人工确认的关键操作（如架构变更、数据库迁移）
- ✅ 可能影响项目结构的变更（如添加新模块、重构）
- ❌ 简单的单步操作（如格式化代码、运行测试）
- ❌ 日常的开发任务（如写函数、修 bug）

## 与 llm_agent 的集成

在 llm_agent 中，可以通过 AGENTS.md 意图路由表实现：

```markdown
## 意图路由表

| 用户意图 | 触发词 | 执行动作 | 涉及技能 |
|----------|--------|----------|----------|
| 特性开发 | brainstorm, plan, TDD | 加载 superpowers-feature-workflow | $superpowers-feature-workflow |
| 学习捕获 | learn, capture, reflect | 加载 superpowers-learning-workflow | $superpowers-learning-workflow |
```

## 参考

- 来源: superpowers-openspec-team-skills/README.cn.md
- 相关模式: 四层分离架构
