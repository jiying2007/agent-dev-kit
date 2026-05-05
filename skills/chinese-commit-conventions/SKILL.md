---
name: chinese-commit-conventions
description: 中文 Git 提交规范——适配国内开发团队
version: 1.0.0
last_updated: 2026-05-05
triggers:
  - "提交代码"
  - "写 commit message"
  - "git commit"
non_triggers:
  - "需求不清楚"
  - "调试代码"
inputs:
  - 代码变更内容
outputs:
  - 格式化的 commit message
constraints:
  - 使用中文提交信息
  - 遵循 conventional commits 格式
---

# 中文 Git 提交规范

## Goal
- 提供适配国内开发团队的 Git 提交规范，确保 commit message 可读、可追溯。

## Prerequisites
- 确认代码变更已完成且可提交。
- 获取最小上下文：变更内容、影响范围。

## 格式

```
<type>(<scope>): <中文描述>

<body>

<footer>
```

## Type 类型

| Type | 中文 | 用途 |
|------|------|------|
| feat | 新功能 | 新增功能 |
| fix | 修复 | 修复 bug |
| docs | 文档 | 文档变更 |
| style | 格式 | 代码格式（不影响逻辑） |
| refactor | 重构 | 代码重构 |
| perf | 性能 | 性能优化 |
| test | 测试 | 测试相关 |
| chore | 杂项 | 构建/工具/配置 |
| ci | CI | CI/CD 相关 |

## Scope 范围

- 使用模块名: `feat(driver): 新增 I2C 驱动初始化`
- 使用功能名: `fix(auth): 修复 token 过期未刷新`

## 示例

```
feat(driver): 新增 I2C 驱动初始化流程

- 实现设备树解析
- 添加 DMA 传输支持
- 包含单元测试

Closes #123
```

## Workflow
1. 检查代码变更内容和影响范围
2. 选择合适的 type 和 scope
3. 编写中文描述（简洁准确）
4. 按格式组装 commit message
5. 提交并验证

## Quality Gate
- commit message 符合格式规范
- type 和 scope 准确反映变更内容
- 描述使用中文且简洁准确

## Evidence Template
```md
- commit message: <message>
- 格式检查: pass / needs-fix
- commit hash: <hash>
```

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "改动很小不用规范" | 小改动也需要可追溯 | 按格式写 commit message |
| "用英文更专业" | 中文团队用中文更高效 | 使用中文描述 |

## 健壮性规范

- **输入验证**: 检查 type 和 scope 合法
- **重试策略**: commit 被拒绝时修正 message 重试
- **超时控制**: 写 commit message 不超过 2 分钟
- **异常隔离**: message 格式错误不影响代码
- **日志记录**: 记录最终 commit hash 和 message
