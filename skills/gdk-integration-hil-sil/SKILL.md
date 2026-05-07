---
name: gdk-integration-hil-sil
description: HIL/SIL 集成验证编排
version: 1.0.0
last_updated: 2026-05-06
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

# gdk-integration-hil-sil

## Goal
- 通过 HIL/SIL 组合验证系统级行为和回归稳定性。
- 建立可重复、可自动化的嵌入式集成测试流程。

## Prerequisites
- 明确系统拓扑、接口依赖和硬件资源占用计划。
- 定义 HIL 与 SIL 的覆盖边界和切换条件。
- 准备测试框架（Robot Framework / pytest-embedded / Unity + CMock）。

## Workflow
1. **分层建模**：模块级（SIL）与系统级（HIL）用例划分。
   - SIL：纯软件仿真，快速迭代，覆盖逻辑分支。
   - HIL：真实硬件在环，覆盖时序、电气特性、协议交互。
2. **SIL 环境搭建**：配置仿真环境与 mock 框架。
   ```bash
   # 编译 SIL 目标（host 架构）
   cmake -S . -B build/sil -DCMAKE_BUILD_TYPE=Debug -DTARGET_SIM=ON
   cmake --build build/sil -j$(nproc)
   # 运行 SIL 测试
   ctest --test-dir build/sil --output-on-failure
   # 或使用 pytest-embedded
   pytest tests/sil/ --tb=short -v
   ```
3. **HIL 环境搭建**：配置硬件探针、串口、CAN 适配器。
   ```bash
   # OpenOCD 连接目标板
   openocd -f interface/stlink.cfg -f target/stm32f4x.cfg &
   # GDB 加载固件
   gdb-multiarch build/hil/firmware.elf \
     -ex "target remote :3333" \
     -ex "monitor reset halt" \
     -ex "load" \
     -ex "continue"
   # 串口监控
   picocom -b 115200 /dev/ttyUSB0
   ```
4. **编排用例矩阵**：功能、性能、异常恢复三类场景。
   ```bash
   # Robot Framework HIL 测试
   robot --variable BOARD_ID:stm32f4disco tests/hil/
   # pytest HIL 测试
   pytest tests/hil/ --board=stm32f4disco --port=/dev/ttyUSB0 -v
   ```
5. **执行验证**：先 SIL 快速回归，再 HIL 关键链路验收。
   ```bash
   # CI 流水线：SIL 全量 + HIL 冒烟
   ./scripts/ci_test.sh --sil full --hil smoke
   # 完整 HIL 回归
   ./scripts/ci_test.sh --hil full --hardware-rig rig-01
   ```
6. **结果汇总**：输出失败模式、复现路径与修复优先级。

## Commands
```bash
# SIL 构建与测试
cmake --preset sil-debug && cmake --build build/sil-debug -j$(nproc)
ctest --test-dir build/sil-debug --output-on-failure

# HIL 固件烧录
openocd -f interface/<probe>.cfg -f target/<chip>.cfg \
  -c "program build/hil/firmware.elf verify reset exit"

# HIL 测试执行
pytest tests/hil/ --board=<board> --port=/dev/ttyUSB0 -v
robot --variable BOARD_ID:<board> tests/hil/

# 串口日志采集
picocom -b 115200 /dev/ttyUSB0 --logfile hil_serial.log

# CAN 总线监控
candump can0 | tee hil_can.log

# 测试报告生成
robot --loglevel DEBUG --outputdir results/ tests/hil/
pytest tests/hil/ --html=results/hil_report.html --self-contained-html
```

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
- 固件烧录失败，检查 OpenOCD 配置与目标板供电。

## Quality Gate
- 必须说明 HIL 与 SIL 的覆盖分工。
- 必须至少包含 1 条系统级异常恢复验证。
- 发布前必须给出"可发布/不可发布"明确结论。
- SIL 测试必须在 CI 中自动执行且通过率 100%。
- HIL 测试报告必须包含串口日志与固件版本信息。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
