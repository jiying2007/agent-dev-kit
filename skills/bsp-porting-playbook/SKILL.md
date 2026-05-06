---
name: bsp-porting-playbook
description: BSP 移植流程与风险控制
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "BSP移植"
  - "板级移植"
non_triggers:
  - 仅业务代码改动
inputs:
  - 旧平台信息、新平台约束
outputs:
  - 移植步骤与验证矩阵
constraints:
  - 先最小可启动，再扩展外设
---

# bsp-porting-playbook

## Goal
- 在可控风险下完成 BSP 迁移，并保留回退路径。
- 确保新平台最小启动链路完整，外设分阶段验证上线。

## Prerequisites
- 明确旧/新平台差异（CPU 架构、时钟树、内存映射、外设基地址）。
- 准备交叉编译工具链（arm-none-eabi-gcc / aarch64-linux-gnu-gcc）。
- 获取目标板原理图、芯片手册、参考 BSP 源码。
- 约定迁移范围与阶段里程碑。

## Workflow
1. **平台差异矩阵**：逐项比对 CPU 架构、时钟配置、内存映射、中断控制器、外设 IP 差异。
2. **设备树 / 配置适配**：修改 DTS/DTSI 文件，适配新的 SoC 节点、时钟源、引脚复用。
   ```bash
   # 设备树编译与检查
   dtc -I dts -O dtb -o new_board.dtb new_board.dts
   dtc -I dtb -O dts new_board.dtb | grep -A5 "serial@"
   ```
3. **交叉编译链路搭建**：配置 Makefile / CMake toolchain 文件，指定交叉编译器与 sysroot。
   ```bash
   # Linux 内核交叉编译
   export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
   make defconfig O=../build/new_board
   make -j$(nproc) O=../build/new_board
   # U-Boot 交叉编译
   make CROSS_COMPILE=aarch64-linux-gnu- <board>_defconfig
   make CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
   ```
4. **最小可启动验证**：仅启用串口控制台、基础存储，确认 boot → kernel → shell 链路。
5. **外设分阶段接入**：按关键业务优先级逐步上线（网络 → 显示 → 音频 → 传感器）。
6. **回归验证**：启动时间、稳定性、关键功能与功耗指标。
7. **发布前收口**：输出遗留风险与后续补齐计划。

## Commands
```bash
# 交叉编译
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
make defconfig O=../build && make -j$(nproc) O=../build

# 设备树编译
dtc -I dts -O dtb -o output.dtb input.dts

# 烧录验证
fastboot flash boot boot.img
# 或
dd if=boot.img of=/dev/mmcblk0p1 bs=4M conv=fsync

# 启动日志抓取
minicom -D /dev/ttyUSB0 -b 115200 -C boot.log
# 或
screen /dev/ttyUSB0 115200

# 硬件验证清单
cat /proc/cpuinfo
cat /proc/meminfo
cat /proc/interrupts
ls /dev/i2c-* /dev/spi-* /dev/ttyS*
```

## Evidence Template
```md
- Platform Diff Matrix (old vs new):
  - CPU/Arch: ____
  - Clock Tree: ____
  - Memory Map: ____
  - Peripheral IPs: ____
- Device Tree Adaptation: [link to dts diff]
- Cross-compile Config: [toolchain version, sysroot path]
- Boot Log: [link to boot.log]
- Bring-up Milestones:
  - [ ] 最小启动（串口控制台）
  - [ ] 存储可用
  - [ ] 网络可用
  - [ ] 外设全部上线
- Device Enablement Status: [table: device | status | notes]
- Regression Result: [启动时间/稳定性/功耗]
- Rollback Plan: [回退步骤与触发条件]
```

## Failure Handling
- 内核无法启动时，回退到上一个可启动配置并做二分定位（git bisect 或 config bisect）。
- 设备树编译报错时，先检查 `#include` 路径与节点引用完整性。
- 外设接入引入系统不稳定时，按模块回滚并隔离问题（逐个 disable 外设节点）。
- 交叉编译链接失败时，检查 sysroot 中库文件架构是否匹配（`file libxxx.so`）。

## Quality Gate
- 必须先达到"最小可启动"再进入功能扩展阶段。
- 每个里程碑必须包含验证结果与阻塞项。
- 必须提供已验证回退路径（含恢复命令）。
- 设备树变更必须通过 `dtc` 编译无 error/warning。
- 交叉编译产出必须通过 `file` 命令验证架构正确性。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
