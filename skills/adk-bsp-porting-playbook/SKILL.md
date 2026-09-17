---
name: adk-bsp-porting-playbook
description: BSP 移植流程与风险控制；源码/构建变更与真实设备刷写权限严格分离
version: 2.0.0
last_updated: 2026-09-17
triggers:
  - "BSP移植"
  - "板级移植"
  - "BSP适配"
  - "启动链"
  - "Bootloader"
  - "rootfs"
  - "secure boot"
non_triggers:
  - 仅业务代码改动
inputs:
  - 旧平台信息、新平台约束、目标 runtime、板卡 identity、回退锚点
outputs:
  - 移植步骤、平台差异矩阵、验证矩阵、设备刷写授权与回退证据
constraints:
  - 先最小可启动，再扩展外设
  - workspace/build 权限不得隐式授权 fastboot、dd、烧录器或分区写入
  - live-device flash/storage-write 必须具备 target identity、explicit authorization、rollback/recovery 和 post-write verification
---

# adk-bsp-porting-playbook

## Goal
- 在可控风险下完成 BSP 迁移，并保留可验证回退路径。
- 同时覆盖 Linux、RTOS 与 bare-metal 平台差异，不把 Linux 特有流程当成通用前提。

## Prerequisites
- 明确旧/新平台的 CPU/ISA、时钟树、内存映射、IRQ、DMA、启动介质和外设 IP 差异。
- 明确 runtime：`linux | rtos | bare-metal`，并准备对应 toolchain。
- 获取目标板原理图、芯片手册、参考 BSP 源码和已知 errata。
- 冻结板卡/设备 identity、迁移范围、里程碑和最后已知可启动回退锚点。

## Workflow
1. **平台差异矩阵**：比较 CPU/ISA、boot stages、clock/reset、memory map、interrupt controller、DMA/cache、storage、security chain 和 peripheral IP。
2. **启动链建模**：按 runtime 显式列出阶段，例如 Linux 的 ROM→SPL→U-Boot→kernel→rootfs，或 MCU 的 ROM→bootloader→application；不得套用不适用阶段。
3. **配置与源码适配**：Linux 可包含 DTS/Kconfig/defconfig；RTOS/裸机使用 board config、linker script、startup/vector table 和 HAL/BSP 配置。
4. **构建链路**：记录 toolchain identity、sysroot/SDK、配置输入、产物 hash；构建超时按 command class/历史基线配置，不使用统一 30s/300s 硬编码。
5. **最小启动产物**：先只保留 console/基础存储或最小通信通道，形成可刷写但尚未执行设备写入的候选 artifact。
6. **live-device 刷写门禁**：只有在 target identity、显式授权、恢复介质/回退镜像、目标分区和写后 readback/boot verification 均明确后，才允许执行 flash/storage-write。
7. **最小可启动验证**：抓取完整 boot evidence，确认目标 stage 到 console/shell/application heartbeat；失败则停止扩外设。
8. **外设分阶段接入**：按依赖和业务优先级逐项开启，每一步保留可回退配置。
9. **回归与发布交接**：验证启动、稳定性、关键功能、功耗/实时性；真实量产放行交给 production-field readiness。

## Commands
```bash
# Linux 构建示例
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
make defconfig O=../build/new_board
make -j$(nproc) O=../build/new_board

dtc -I dts -O dtb -o output.dtb input.dts
file <bootloader-or-kernel-artifact>
sha256sum <artifact>

# RTOS / bare-metal 示例
<toolchain> --version
<build-command>
file <elf-or-bin>
sha256sum <elf-or-bin>

# live-device 示例仅供授权后执行，不属于默认 workspace/build 权限
# fastboot flash boot boot.img
# dd if=boot.img of=/dev/<explicit-target-partition> bs=4M conv=fsync
# <vendor-programmer> --target <device-id> --image <artifact>
```

## Evidence Template
```md
- Runtime: linux | rtos | bare-metal
- Target Identity: board_rev / device_id / SoC-or-MCU
- Platform Diff Matrix:
- Boot Chain:
- Source / Config Adaptation:
- Toolchain / Build Artifacts + Hashes:
- Last-known-good Rollback Anchor:
- Live-device Mutation:
  - required: yes | no
  - operation: flash | storage-write | none
  - explicit_authorization:
  - target_partition_or_region:
  - recovery_path:
  - post_write_verification:
- Boot Evidence:
- Device Enablement Status:
- Regression Result:
- Gate Result: pass | needs-fix | blocked
```

## Failure Handling
- 构建或配置失败先在 host/build 域收敛，不升级到设备写操作。
- 刷写前 identity/partition/recovery 任一不明确时固定 `blocked`。
- 刷写或启动失败立即停止继续写，执行预先声明的 recovery/rollback，再做二分定位。
- 外设接入引入不稳定时回到最后已知可启动配置并隔离问题。

## Quality Gate
- 必须先达到最小可启动证据，再进入外设扩展。
- 每个里程碑有 artifact identity、验证结果和阻塞项。
- live-device flash/storage-write 不能由源码修改、构建成功或 release-preparation 权限推导。
- 回退路径必须在设备写入前定义；生产/现场放行必须由独立 readiness gate 签署。
