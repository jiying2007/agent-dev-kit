---
name: toolchain-debug-openocd-gdb
description: OpenOCD + GDB 联调流程
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 硬件断点、烧录、在线调试时
non_triggers:
  - 纯单元测试场景
inputs:
  - 芯片与探针配置
outputs:
  - 调试脚本与操作步骤
constraints:
  - 优先保留可复现命令序列
---

# toolchain-debug-openocd-gdb

## Goal
- 建立可复用的在线调试与烧录操作序列。

## Prerequisites
- 确认探针型号、芯片目标配置、调试接口速率。
- 准备 ELF 符号文件与启动脚本。

## Workflow
1. 连接校验：探针识别、目标芯片握手、时钟设置。
2. 烧录验证：最小镜像下载与校验。
3. 断点调试：入口断点、单步、寄存器/内存观察。
4. 异常定位：HardFault/异常向量回溯与调用栈解析。
5. 沉淀脚本：将可复现命令固化为脚本或文档。

## Commands
```bash
openocd -f interface/<probe>.cfg -f target/<chip>.cfg
gdb-multiarch <firmware.elf> -ex "target remote :3333" -ex "monitor reset halt"
```

## Evidence Template
```md
- Probe/Target Config:
- Flash Result:
- Breakpoint/Backtrace:
- Fault Register Snapshot:
- Repro Command Sequence:
```

## Failure Handling
- 无法连接时优先检查供电、线序、接口速率。
- 回溯失败时先核对符号文件与编译优化级别。

## Quality Gate
- 必须给出可复现命令序列。
- 必须提供至少一条异常定位证据（backtrace/寄存器快照）。
- 调试步骤需区分“烧录问题”与“运行时问题”。
