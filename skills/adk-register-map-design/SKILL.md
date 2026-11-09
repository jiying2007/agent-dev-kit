---
name: adk-register-map-design
description: "用于芯片寄存器映射、位域权限和驱动接口文档设计；不用于直接对真实寄存器写入或代替外设时序调试。"
version: 1.0.3
last_updated: 2026-11-09
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

# adk-register-map-design

## Goal
- 产出可直接用于驱动实现的寄存器映射规范。

## Prerequisites
- 已确认芯片手册版本、页码与勘误信息。
- 明确访问宽度、端序、读写副作用。

## Workflow
1. 建立寄存器清单：地址、复位值、访问权限、描述。
2. 细化位域定义：位宽、枚举值、保留位处理规则；区分已有芯片手册驱动适配与可自主定义的新寄存器接口。
3. 标注时序约束：写入顺序、延时、互斥条件。
4. 关联异常处理：错误状态位与清除机制。
5. 生成驱动映射建议：宏定义、掩码及安全的访问序列；W1C／读清／FIFO／保留位不应盲目使用通用 read-modify-write。

## Commands
```bash
rg -n "#define.*REG_|BIT\(|MASK" <driver_path>
rg -n "TODO.*register|FIXME.*reg" <driver_path>
rg -n "reserved|RESERVED" <header_path>
# ADK 不内置生成器或校验器。目标项目需给出真实工具路径和 datasheet 版本；不可伪造 PASS。
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
| 既有芯片保留位 | 严格遵循 datasheet/errata：可要求写 0、保留复位值或禁止访问；不能假定读 0／写忽略 |
| 自主设计的保留位 | 仅在设计明确选择时可采用 RAZ/WI（读零、写忽略），并写入契约与验证 |
| 读改写原子性 | 多位域共享寄存器需提供原子操作或锁 |
| 写 1 清除／读副作用 | W1C、read-clear、FIFO 等应单独规定访问序列与竞态，不用普通 RMW 模板 |
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
- 必须说明手册中的保留位写入限制及读写副作用；新设计与既有芯片适配不得混用默认语义。
- 必须附最小验证清单（读写/中断/异常）。

## 健壮性规范
- **输入验证**: 校验 datasheet 版本与寄存器地址是否匹配
- **异常隔离**: 单个寄存器定义错误不影响其他外设映射
- **日志记录**: 记录每个寄存器的来源（datasheet 页码/版本）
