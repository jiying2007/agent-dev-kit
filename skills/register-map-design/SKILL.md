---
name: register-map-design
description: 定义寄存器映射与位域文档
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "设计寄存器"
  - "寄存器映射"
  - "芯片适配"
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
rg -n "reserved|RESERVED" <header_path>
python3 scripts/gen_reg_header.py --input reg_map.yaml --output reg_defs.h
python3 scripts/validate_reg_map.py --input reg_map.yaml --datasheet ds.pdf
```

## SVD 生成与验证
```yaml
# 寄存器映射 YAML 示例
peripherals:
  - name: GPIOA
    base_address: 0x40020000
    registers:
      - name: MODER
        offset: 0x00
        size: 32
        access: read-write
        reset_value: 0x00000000
        fields:
          - { name: MODE0, bit_offset: 0, bit_width: 2, enum: [Input:0, Output:1] }
```

## 位域设计规范
| 规则 | 说明 |
|------|------|
| 保留位处理 | 读返回 0，写忽略；不得用于新功能 |
| 读改写原子性 | 多位域共享寄存器需提供原子操作或锁 |
| 写 1 清除 | W1C 类型位必须在 ISR 中明确处理 |
| 复位值一致性 | 代码中复位值必须与 datasheet 一致 |
| 端序 | 多字节寄存器必须标注字节序 |

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "寄存器很简单不用文档" | 口头传递是寄存器 bug 的温床 | 每个寄存器必须有映射表 |
| "reserved 位随便写" | 某些芯片 reserved 位有隐藏功能 | 严格按 datasheet 读写规则 |

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

## 健壮性规范
- **输入验证**: 校验 datasheet 版本与寄存器地址是否匹配
- **异常隔离**: 单个寄存器定义错误不影响其他外设映射
- **日志记录**: 记录每个寄存器的来源（datasheet 页码/版本）
