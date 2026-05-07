---
name: adk-toolchain-debug-openocd-gdb
description: OpenOCD + GDB 联调流程
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "OpenOCD"
  - "GDB调试"
  - "JTAG调试"
non_triggers:
  - 纯单元测试场景
inputs:
  - 芯片与探针配置
outputs:
  - 调试脚本与操作步骤
constraints:
  - 优先保留可复现命令序列
---

# adk-toolchain-debug-openocd-gdb

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
gdb-multiarch <firmware.elf> -x debug.gdb  # 批量脚本
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program <file>.elf verify reset exit"
```

## OpenOCD 配置详解
```tcl
source [find interface/stlink.cfg]  # 探针驱动
transport select hla_swd             # SWD/JTAG 选择
adapter speed 4000                    # 时钟频率（kHz）
source [find target/stm32f4x.cfg]   # 目标芯片配置
$_TARGETNAME configure -rtos auto    # 自动检测 RTOS
```

## GDB 常用命令速查
| 命令 | 说明 |
|------|------|
| `b main` | 在 main 函数设断点 |
| `hb *0x08001234` | 硬件断点（Flash 中必须用） |
| `watch *ptr` | 数据观察点（值变化时中断） |
| `x/20xw 0x20000000` | 查看内存（20 个 word 十六进制）|
| `monitor reset halt` | 复位并暂停在 Reset_Handler |
| `bt` | 查看调用栈回溯 |
| `info threads` | 查看 RTOS 线程（需 RTOS 支持）|

## 断点管理策略
| 场景 | 策略 |
|------|------|
| Flash 中的代码 | 必须用硬件断点 `hb`（数量有限，通常 4-6 个）|
| RAM 中的代码 | 用软件断点 `b`（数量不限）|
| 条件断点 | `b foo if x > 10`（注意性能影响）|
| 临时断点 | `tbreak`（命中一次后自动删除）|

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "串口 printf 够用了" | printf 无法暂停查看状态 | 关键路径必须 GDB 断点验证 |
| "硬件断点不够用" | 合理规划 + 条件断点可以覆盖绝大多数场景 | 先清理不需要的断点 |

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

## 健壮性规范
- **输入验证**: 校验探针连接、芯片 ID、ELF 符号文件
- **异常隔离**: 烧录失败不影响调试会话，反之亦然
- **日志记录**: 记录 OpenOCD/GDB 命令序列与输出
