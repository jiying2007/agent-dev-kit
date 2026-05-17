# 验收标准格式

> 来源: agent-dev-kit 验收标准基线

## 标准格式

```
WHEN <触发条件>
THEN THE System SHALL <预期行为>
```

## 示例

```
WHEN 用户输入包含"调试"关键词
THEN THE System SHALL 加载 adk-systematic-debugging 技能

WHEN SKILL.md 缺少 what-to-do 标签
THEN THE System SHALL 发出 WARNING 并降级处理

WHEN 编译错误超过 5 个
THEN THE System SHALL 暂停执行并请求人工确认
```

## 与 adk 的集成
- `verify-report` 中使用此格式描述验证条件
- `task-breakdown` 中使用此格式定义验收标准
