---
name: adk-unit-test-embedded
description: "用于 MCU/RTOS 的单元测试断言、替身与外设边界模拟；非跨模块测试策略，也不用于直接证明真实 HIL 性能。"
version: 1.1.6
last_updated: 2026-11-15
triggers:
  - "单元测试"
  - "写测试"
  - "测试用例"
non_triggers:
  - 纯硬件连线问题
inputs:
  - 模块接口、边界条件
outputs:
  - 仅设计时交付用例与断言；已授权实施后交付实际测试、fixture 路径、命令和结果
  - 未覆盖的硬件或实时边界及后续验证条件
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

## Target / Test Seam Gate
- 按目标选择最小必要组合：host-unit、cross-build compile-only、SIL/emulator、HIL/board-runner 可覆盖不同边界，分别记录结论；compile-only 不证明断言已运行。`ceedling/gcovr/lcov` 仅为条件性示例，先核实工具、runner 和 compiler flags，不默认在无 libc/无 host runner 的 MCU 上执行 host 工具。
- 校验真实公开模块接口而不是 mock 的内部调用次数；W1C 寄存器、DMA ownership、ISR/任务竞态、队列溢出等边界应在可观察 seam 加负例。无法模拟的电气/实时行为保留 `needs-hil`，不推断板上已通过。

## Workflow
1. 读公开接口与现有测试入口，识别外设、时钟及全局状态的替身边界，不另建平行框架。
2. 从验收和历史缺陷选择正常、边界、异常、时序用例，明确输入、期望状态或输出。
3. 仅要求设计时交付清单；要求写测试时，交已有授权的实现职责编写测试与必要 fixture，再回传验证。本 Skill 不提升写权限，也不能用清单关闭实施任务。
4. 采用项目已核实的定向命令；缺陷用例先确认原失败，再核修复及原通过路径。未执行写 `not-run`，保留真实退出码。
5. 交付实际文件、命令和断言结果，区分编译、模拟与板上证据；不可模拟的时序保留 `needs-hil`。

## Commands
从已选项目工具中使用适用入口，不逐项执行所有示例，不为未知 runner 追加通用 `--module` 参数。
```bash
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

## 测试覆盖率策略

| 指标 | 正确使用边界 | 验证证据 |
|---|---|---|
| 行、分支、函数覆盖 | 以项目风险与基线设目标；固定 80%/70%/100% 不可作为跨平台认证 | 实际覆盖报告 |
| 条件/决策覆盖 | 核对工具语义；不能自动等同 MC/DC | 规则和逐项结果 |
| MC/DC | 安全关键场景按适用规范、真实工具能力和独立报告验证；BullseyeCoverage 的 condition/decision 本身不等于 MC/DC | 独立 MC/DC 报告或 not-evaluated |

关键路径、边界、错误恢复优先；覆盖率不代替板级时序和 HIL 证据。

## Evidence Template
```md
- Scope / Test Layer:
- Cases / Assertions / Regression:
- Test / Fixture Paths: actual paths | design-only
- Command / Exit Code / Result: pass | fail | not-run
- Coverage / needs-hil:
```

## Failure Handling
- 测试不稳定时先排查时间依赖和全局共享状态。
- 覆盖率提升导致噪声时，优先保留关键路径测试。

## Quality Gate
- 必须覆盖至少 1 条边界与 1 条错误路径。
- 新增缺陷修复必须附对应回归用例。
- 测试结果需可复现且可追溯到模块版本。
