---
name: adk-integration-hil-sil
description: "用于软件在环与硬件在环的集成测试、场景配置与结果证据编排；不用于仅做单元测试或绕过真实设备操作授权。"
version: 1.0.2
last_updated: 2026-11-10
triggers:
  - "集成测试"
  - "HIL测试"
  - "SIL测试"
non_triggers:
  - 只改注释文档
inputs:
  - 系统拓扑、测试资源
outputs:
  - HIL/SIL 用例矩阵
constraints:
  - 必须标注硬件依赖与替代方案
---

# adk-integration-hil-sil

## Goal
- 通过 HIL/SIL 组合验证系统级行为和回归稳定性。
- 建立可重复、可自动化的嵌入式集成测试流程。

## Prerequisites
- 锁定设备族、board revision、固件 hash、runner、资源占用、受控 HIL operator 和安全恢复路径。
- 优先使用目标仓现有 build/test 工具；先查 CMake option、pytest 插件、脚本和工装，不假定 `TARGET_SIM`、`pytest --board`、`scripts/ci_test.sh` 存在。
- 设备编程、主动探测、重启、断电和故障注入分别执行授权与效果分级。

## Workflow
1. **分层**：区分 host-unit、compile-only、SIL/QEMU、HIL、人工板级和量产资格；哪层实测就只报告哪层。
2. **确认执行后端**：以当前仓库的配置和真实命令为准；记录 compile-only/host/emulator/board-runner，`ctest` 在目标未注册 runner 时不等于真机运行。
3. **资源隔离**：冻结构建输出、测试二进制、缓存、端口、串口、rig 和 device identity；共享资源禁止并行运行。
4. **SIL**：按真实构建/仿真入口执行，采集架构、模拟精度、未覆盖硬件行为和原始证据。
5. **HIL preflight**：只读核对 device/firmware、测试硬件、故障停止条件和健康恢复；需要刷写或改变设备状态时另交授权 operator。
6. **逐级扩大**：单次 smoke→功能/异常回归→可选长稳；失联、身份漂移、core/fatal log 或恢复失败立即停止，不能重试刷到绿。
7. **复验**：区分失败、跳过、未执行和预期负结果，记录命令、退出码、固件身份、串口/总线证据及 postcondition。
8. **交付**：说明各层 pass/fail/not-run、依赖与残留缺口；本 Skill 不单独批准量产。

## Commands
以下命令仅适用于**已验证使用 CMake/CTest 的工程**，不是任意项目通用入口：
```bash
ctest --test-dir build/sil --show-only=json-v1
ctest --test-dir build/sil --output-on-failure
```
pytest 工程须先检查实际插件/选项；目标不存在时不得猜测 `--board` 或 `--port`。现场命令、rig 与固件刷写由项目提供。

## Budget / Retry
- 按目标动作、恢复 SLA、硬件负载和阶段确定 timeout、退避及最大重试，不套用统一 30 秒/300 秒和三次重试。
- 外部动作状态不明时先对账 artifact／boot_id／device status，不盲目重放。
- 无设备或授权时只能 `not-run/blocked`，SIL 绿不代表 HIL 或 production-ready。

## Evidence Template
```md
- Coverage Split (HIL/SIL):
  | Layer | Cases | Pass | Fail | Skip |
  |-------|-------|------|------|------|
  | SIL | __ | __ | __ | __ |
  | HIL | __ | __ | __ | __ |
- Environment Baseline:
  - SIL: host compiler ____, test framework ____
  - HIL: probe=____, board=____, firmware=____
- Case Result Summary: [link to report]
- Failure Repro Steps:
  - [ ] SIL 可复现
  - [ ] HIL 可复现
  - [ ] 最小复现命令: ____
- Release Readiness: [可发布/不可发布 + 理由]
```

## Failure Handling
- HIL 资源不可用时，先以 SIL 保持回归连续性并标注硬件覆盖缺口。
- HIL/SIL 结果冲突时，优先核对环境差异与 mock 假设是否偏离真实硬件行为。
- HIL 测试超时，检查串口连接与目标板状态（可能 hang）。
- 固件烧录失败，检查调试通道配置与目标板供电。

## Quality Gate
- 必须说明 HIL 与 SIL 的覆盖分工。
- 必须至少包含 1 条系统级异常恢复验证。
- 发布准备应明确证据和未测缺口；最终 go/no-go 归项目发布门禁。
- 纳入 CI 的适用 SIL 用例必须区分 pass/fail/skip/not-run，不以未执行或有未解释失败冒充 PASS。
- HIL 报告记录固件/设备身份、原始证据（具备串口时包含串口日志）、退出码和最终健康状态。
