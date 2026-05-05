---
name: driver-bringup-checklist
description: 驱动 bring-up 标准检查清单
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "驱动开发"
  - "驱动调试"
  - "外设联调"
non_triggers:
  - 稳定量产驱动小改
inputs:
  - 芯片型号、总线类型
outputs:
  - bring-up checklist
constraints:
  - 必须覆盖时钟、复位、中断、DMA
---

# driver-bringup-checklist

## Goal
- 通过清单化流程快速收敛驱动首板联调问题。

## Prerequisites
- 确认硬件版本、引脚复用、供电和时钟配置一致。
- 准备串口日志、调试探针和寄存器读写工具。

## Workflow
1. 上电前检查：电源、时钟、复位、pinmux。
2. 总线连通性验证：I2C/SPI/UART/CAN 基础收发。
3. 初始化路径验证：最小功能先通，再启中断/DMA。
4. 异常分支验证：超时、CRC 错误、设备不存在。
5. 稳定性检查：循环收发、长稳运行、重启恢复。

## Commands
```bash
dmesg | tail -n 200
<bus-tool-cmd> --probe <device>
<driver-selftest-cmd> --smoke
```

## Evidence Template
```md
- Hardware Baseline:
- Init Sequence Result:
- Interrupt/DMA Result:
- Error Path Result:
- Long-run Result:
```

## Failure Handling
- 若总线基础通信失败，先回滚到硬件基线排查。
- 若中断异常，先禁 DMA 做最小闭环验证再逐项开启。

## Quality Gate
- 清单需覆盖时钟、复位、中断、DMA 四类检查。
- 每类至少给一个通过证据或失败日志。
- 未完成最小闭环前，不得声明“驱动已完成 bring-up”。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
