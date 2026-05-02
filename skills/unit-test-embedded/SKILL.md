---
name: unit-test-embedded
description: 嵌入式单元测试策略与样例
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 新增逻辑模块或回归缺陷时
non_triggers:
  - 纯硬件连线问题
inputs:
  - 模块接口、边界条件
outputs:
  - 单测清单与断言策略
constraints:
  - 优先覆盖边界与错误路径
---

# unit-test-embedded

## Goal
- 为嵌入式模块建立高价值、低维护成本的单元测试。

## Prerequisites
- 明确模块输入输出、依赖替身（mock/stub）策略。
- 定义最小覆盖目标（关键路径与错误路径）。

## Workflow
1. 提炼可测单元：隔离外设依赖与全局状态。
2. 设计用例：正常、边界、异常、时序四类。
3. 编写断言：重点验证状态变化和错误处理。
4. 构建回归集：把历史缺陷固化为回归测试。
5. 执行与评估：统计通过率与失败根因。

## Commands
```bash
<unit-test-cmd> --module <module_name>
<coverage-cmd> --module <module_name>
```

## Evidence Template
```md
- Test Scope:
- Case Matrix:
- Assertion Strategy:
- Coverage Snapshot:
- Regression Cases Added:
```

## Failure Handling
- 测试不稳定时先排查时间依赖和全局共享状态。
- 覆盖率提升导致噪声时，优先保留关键路径测试。

## Quality Gate
- 必须覆盖至少 1 条边界与 1 条错误路径。
- 新增缺陷修复必须附对应回归用例。
- 测试结果需可复现且可追溯到模块版本。
