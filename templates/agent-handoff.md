# Agent 交接协议

> 标准化 Agent 间交接模板

- **from_agent**: {{from_agent_name}}
- **to_agent**: {{to_agent_name}}
- **date**: {{YYYY-MM-DD}}
- **change_id**: {{change_id}}

## 交接产物

| # | 产物标签 | 路径 | 状态 |
|---|---------|------|------|
| 1 | {{artifact_tag}} | {{path}} | READY/BLOCKED |

## 交接状态

- [ ] 所有必要产物已就绪
- [ ] 阻塞项已清零
- [ ] 下游入口条件满足

## 阻塞项（如有）

| # | 阻塞项 | 应由谁解除 | 预计时间 |
|---|--------|-----------|---------|
| 1 | {{blocking_item}} | {{responsible_agent}} | {{eta}} |

## 交接说明

{{详细说明当前状态、已完成的工作、需要下游继续的部分}}
