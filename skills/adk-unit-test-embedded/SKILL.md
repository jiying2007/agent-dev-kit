---
name: adk-unit-test-embedded
description: "用于 MCU/RTOS 的单元测试断言、替身与外设边界模拟；非跨模块测试策略，也不用于直接证明真实 HIL 性能。"
version: 1.1.4
last_updated: 2026-11-10
triggers:
  - "单元测试"
  - "写测试"
  - "测试用例"
non_triggers:
  - 纯硬件连线问题
inputs:
  - 模块接口、边界条件
outputs:
  - 单测清单与断言策略
constraints:
  - 优先覆盖边界与错误路径
---

# adk-unit-test-embedded

## Goal
- 建立嵌入式模块单测。

## Prerequisites
- 明确模块输入输出、依赖替身（mock/stub）策略。
- 定义最小覆盖目标（关键路径与错误路径）。
- 需要跨板级、SIL/HIL、boot、OTA 或现场层次时使用 `references/embedded-tdd-matrix.md`。

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
# Unity 框架
ceedling test:<module_name>
ceedling gcov:<module_name>
# 启用 module_generator 后生成源文件、头文件、测试骨架（并非直接生成 CMock mock）
ceedling "module:create[Sensor]"
# CMock 的 mock 通过测试中依赖头文件和 Ceedling 配置生成
# 覆盖率报告
gcovr --root . --filter src/ --xml -o coverage.xml
lcov --capture --directory build --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

## Unity/CMock 框架速查
```c
// Unity 常用断言
TEST_ASSERT_EQUAL_INT(expected, actual);
TEST_ASSERT_EQUAL_STRING(expected, actual);
TEST_ASSERT_TRUE(condition);
TEST_ASSERT_NULL(pointer);
TEST_ASSERT_EQUAL_MEMORY(expected, actual, len);
```

## 测试覆盖率策略

| 指标 | 正确使用边界 | 验证证据 |
|---|---|---|
| 行、分支、函数覆盖 | 以项目风险与基线设目标；固定 80%/70%/100% 不可作为跨平台认证 | 实际覆盖报告 |
| 条件/决策覆盖 | 核对工具语义；不能自动等同 MC/DC | 规则和逐项结果 |
| MC/DC | 安全关键场景按适用规范、真实工具能力和独立报告验证；BullseyeCoverage 的 condition/decision 本身不等于 MC/DC | 独立 MC/DC 报告或 not-evaluated |

关键路径、边界、错误恢复优先；覆盖率不代替板级时序和 HIL 证据。

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

---

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "硬件相关代码没法单元测试" | HAL mock 和 SIL 桩可以覆盖绝大多数逻辑 | 按 SKILL.md 分层策略，业务逻辑与硬件解耦后分别测试 |
| "跑过集成测试就够了" | 集成测试无法精确定位模块内部缺陷 | 必须覆盖边界和错误路径的单元级验证 |
| "改动很小不需要补测试" | 小改动也可能破坏隐含的不变量 | 行为变更或缺陷修复必须附相应回归或明确缺口；无行为变化采用最小适用验证 |
