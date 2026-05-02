---
name: interface-contract-design
description: 定义模块/API/消息接口契约
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 新增或变更跨模块接口时
non_triggers:
  - 纯内部重命名
inputs:
  - 调用方与被调方约束
outputs:
  - 接口契约草案
constraints:
  - 必须明确输入、输出、错误码
---

# interface-contract-design

## Goal
- 输出稳定、可验证的接口契约，降低跨模块返工。

## Prerequisites
- 明确调用链 owner、版本策略和兼容窗口。
- 确定输入输出数据源与错误语义边界。

## Workflow
1. 定义接口清单：请求、响应、错误码、幂等语义。
2. 标注版本策略：向后兼容、废弃周期、迁移路径。
3. 约束异常行为：超时、限流、重试、降级策略。
4. 生成契约用例：正常、边界、异常三类样例。
5. 同步消费者影响：列出受影响模块与改造顺序。

## Commands
```bash
rg -n "interface|api|contract|schema" <module_path>
rg -n "TODO.*compat|deprecated" <module_path>
```

## Evidence Template
```md
- Interface:
- Input/Output:
- Error Codes:
- Compatibility Policy:
- Migration Plan:
- Validation Cases:
```

## Failure Handling
- 若调用方未确认兼容策略，结论置为 `needs-fix`。
- 若错误语义不一致，先冻结接口变更并回到设计讨论。

## Quality Gate
- 契约必须包含输入/输出/错误码/超时语义。
- 必须给出版本兼容与迁移方案。
- 必须附至少 3 条验证用例（正常/边界/异常）。
