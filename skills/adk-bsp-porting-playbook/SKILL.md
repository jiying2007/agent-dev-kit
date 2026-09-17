---
name: adk-bsp-porting-playbook
description: BSP 移植流程与风险控制；源码/构建与真实设备刷写权限分离
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
  - 旧平台信息、新平台约束、runtime 类型、目标板 identity
outputs:
  - 移植步骤、验证矩阵、刷写授权 handoff、回退证据
constraints:
  - 先最小可启动，再扩展外设
  - workspace/build 权限不得推导真实设备 flash/storage-write 权限
  - 真实刷写必须有 target identity、explicit authorization、recovery 和 post-write verification
---

# adk-bsp-porting-playbook

## Goal
- 在可控风险下完成 Linux/RTOS/bare-metal BSP 迁移，并保留最后已知可恢复锚点。
- 把源码适配、构建产物和真实设备写入分成不同授权域。

## Prerequisites
- 明确 runtime：`linux-embedded | mcu-rtos | mcu-baremetal`，以及 SoC/MCU、board revision、boot chain 和存储介质。
- 获取原理图、芯片手册、参考 BSP、目标 toolchain 和当前 last-known-good artifact。
- 约定迁移范围、阶段里程碑、目标设备 identity 和恢复入口。

## Workflow
1. **冻结平台 identity**：记录 old/new platform、runtime、board/device identity、source commit 和 last-known-good artifact/hash。
2. **差异矩阵**：比较 CPU/core、clock/reset、memory map、interrupt、DMA/cache、pinmux、storage/boot media 和 peripheral IP。
3. **启动链建模**：
   - Linux：ROM/SPL/U-Boot(or equivalent) → kernel → DT → rootfs/userspace。
   - RTOS：ROM/bootloader → vector/startup → BSP/HAL → scheduler/application。
   - bare-metal：ROM/bootloader → startup/linker → clocks/memory → application loop。
4. **源码/配置适配**：只在 workspace 域修改 DTS/config/startup/linker/HAL/board files，并保留最小 diff。
5. **构建闭环**：锁 toolchain、构建入口、artifact identity/hash；构建超时按项目基线，不使用固定 30s/300s 通用阈值。
6. **设备写升级门禁**：若需要 flash/storage-write，生成 handoff payload：target identity、artifact hash、目标 region/partition、explicit authorization、recovery、post-write verification。缺任一项固定 blocked；本 Skill 不提供可直接复制执行的设备写命令。
7. **最小可启动验证**：抓取完整 boot evidence，确认目标 stage 到 console/shell/application heartbeat；失败则停止扩外设。
8. **外设分阶段接入**：按依赖和业务优先级逐项开启，每一步保留可回退配置。
9. **回归与发布交接**：验证启动、稳定性、关键功能、功耗/实时性；真实量产放行交给 production-field readiness。

## Commands
```bash
# Linux host/build 示例
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
make defconfig O=../build/new_board
make -j$(nproc) O=../build/new_board
dtc -I dts -O dtb -o output.dtb input.dts
file <bootloader-or-kernel-artifact>
sha256sum <artifact>

# RTOS / bare-metal host/build 示例
<toolchain> --version
<build-command>
file <elf-or-bin>
sha256sum <elf-or-bin>

# live-device mutation 只生成 operator handoff，不在本 Skill 输出刷写命令。
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
- Live-device Handoff:
  - required: yes | no
  - operation: flash | storage-write | none
  - target_identity:
  - artifact_sha256:
  - target_partition_or_region:
  - explicit_authorization:
  - recovery_path:
  - post_write_verification:
- Boot Evidence:
- Device Enablement Status:
- Regression Result:
- Gate Result: pass | needs-fix | blocked
```

## Failure Handling
- 构建或配置失败先在 host/build 域收敛，不升级到设备写操作。
- 设备写 handoff 前 identity/region/recovery 任一不明确时固定 `blocked`。
- 受控 operator 返回写入/启动失败时停止后续 mutation，执行预先声明的 recovery/rollback，再做二分定位。
- 外设接入引入不稳定时回到最后已知可启动配置并隔离问题。

## Quality Gate
- 必须先达到最小可启动证据，再进入外设扩展。
- 每个里程碑有 artifact identity、验证结果和阻塞项。
- live-device flash/storage-write 不能由源码修改、构建成功或 release-preparation 权限推导。
- 回退路径必须在设备写入 handoff 前定义；生产/现场放行必须由独立 readiness gate 签署。
