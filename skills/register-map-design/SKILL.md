---
name: register-map-design
description: 定义寄存器映射与位域文档
triggers:
  - 驱动开发前期或芯片适配时
non_triggers:
  - 应用层纯逻辑开发
inputs:
  - datasheet 摘要、硬件约束
outputs:
  - 寄存器表与访问规则
constraints:
  - 不得臆造寄存器语义
---

# register-map-design

## Goal
- 产出可直接用于驱动实现的寄存器映射规范。

## Prerequisites
- 已确认芯片手册版本、页码与勘误信息。
- 明确访问宽度、端序、读写副作用。

## Workflow
1. 建立寄存器清单：地址、复位值、访问权限、描述。
2. 细化位域定义：位宽、枚举值、保留位处理规则。
3. 标注时序约束：写入顺序、延时、互斥条件。
4. 关联异常处理：错误状态位与清除机制。
5. 生成驱动映射建议：宏定义、掩码、读改写范式。

## Commands
```bash
rg -n "#define.*REG_|BIT\(|MASK" <driver_path>
rg -n "TODO.*register|FIXME.*reg" <driver_path>
```

## Evidence Template
```md
- Register Table:
- Bitfield Definition:
- Access Sequence:
- Side Effects:
- Validation Checklist:
```

## Failure Handling
- 数据手册语义冲突时，标注冲突点并暂停实现。
- 缺失复位值或时序要求时，结论为 `needs-fix`。

## Quality Gate
- 每个寄存器必须包含访问权限与复位值。
- 必须说明保留位处理策略与读改写规则。
- 必须附最小验证清单（读写/中断/异常）。
