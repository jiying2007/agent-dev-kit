---
name: adk-embedded-storage-layout-migration
description: 嵌入式存储布局和文件系统迁移治理；设计/构建与真实分区写入分权，覆盖 UBI/UBIFS/SquashFS/ubiblock、OTA 迁移和回滚
version: 2.0.0
last_updated: 2026-09-17
triggers:
  - "UBIFS"
  - "SquashFS"
  - "ubiblock"
  - "业务分区"
  - "分区保留"
  - "存储布局迁移"
  - "OTA布局迁移"
  - "文件系统切换"
non_triggers:
  - "普通固件发布"
  - "只改版本号"
  - "非持久化临时挂载问题"
inputs:
  - 分区表、配置链、rootfs 挂载脚本、ubinize/OTA layout、boot log、现场数据保留要求、目标设备 identity、回滚策略
outputs:
  - 迁移判定、受影响分区、保留策略、构建/升级路径、设备写入授权边界、boot/readback 验证和回滚证据
constraints:
  - 不得把文件系统形态切换称为普通 regular OTA，除非迁移和回滚证据完整
  - 必须优先保护 /factory、/data、/ota 等现场数据分区
  - release-preparation 不自动授权真实分区擦写、whole-device flash 或 destructive migration
  - live-device storage-write/flash 必须具备 target identity、explicit authorization、backup/recovery 和 post-write verification
---

# adk-embedded-storage-layout-migration

## Goal
- 管理嵌入式设备存储布局、UBI volume 和文件系统形态迁移。
- 防止“配置已改但产物/启动脚本/OTA 仍走旧路径”的半升级状态，以及“为了验证布局直接覆盖现场数据”的权限越界。

## Prerequisites
- 已知道产品 profile、分区布局、升级方式和目标设备/板卡 identity。
- 已拿到配置、构建产物或 boot log 中至少一种证据。
- 已明确必须保留的数据分区、最后可恢复版本和 recovery/backup 能力。

## Workflow
1. **现状矩阵**：列 boot/rootfs、factory/data/ota、misc/pstore 等 partition/volume 的 FS、mount、update method、preserve policy 和运行态证据。
2. **变更分类**：区分普通内容更新、布局迁移、FS 切换、回滚迁移、产线重刷；不同类别不能共享同一风险结论。
3. **配置链对齐**：核 defconfig/current config、partition table、ubinize、mount script、OTA layout、release metadata 和 artifact hash。
4. **现场数据保护**：优先只更新目标 volume；whole-UBI/whole-device 覆盖默认禁止，除非明确说明为什么无法增量迁移并有完整备份恢复。
5. **host/build 验证**：重新生成 rootfs/customer/OTA/SD artifact，在不写真实设备的前提下校验 layout、manifest、size、hash 和 migration script dry-run。
6. **device escalation gate**：真实 erase/flash/storage-write 前冻结 device identity、目标 partition/volume、预期前后布局、显式授权、backup/recovery 和 post-write readback/boot verification；缺任一项固定 blocked。
7. **受控迁移验证**：先单设备/测试板执行，再验证 cold boot、数据保留、read-only/write semantics、断电/失败恢复、rollback 和重复升级。
8. **扩展准入**：只有单设备证据通过且 residual risk 可接受，才允许进入更大批次；批量执行授权不能由单设备授权自动继承。

## Commands
```bash
# 默认只读/host-side
rtk rg -n "UBIFS|squashfs|ubiblock|factory|data|ota|ubinize|partition|layout" <repo>
rtk rg -n "MOUNTPT|MOUNTPARAM|FSTYPE|VOL_TYPE|rootfstype|ubi.mtd" <repo>
rtk rg -n "ubi0:|ubiblock|Mounted root|mounting .*customer|Kernel command line" <boot-log>
sha256sum <image-or-ota-package>
<migration-check-command> --dry-run

# 真实设备写操作仅在 escalation gate 完成后执行：
# <flash-tool> --device <device-id> --partition <partition> --image <image>
# <ubi-update-tool> <explicit-volume> <image>
```

## Evidence Template
```md
- Migration Type:
- Target Identity:
- Preserve Requirements:
- Layout Matrix: partition / volume / FS / mount / update_method / preserve
- Config Chain + Artifact Hashes:
- Host/Dry-run Evidence:
- Live-device Mutation:
  - required / operation / partition_or_volume / explicit_authorization
  - backup_or_recovery / post_write_readback / boot_verification
- Data Preservation Evidence:
- Failure / Power-loss / Rollback Evidence:
- Batch Expansion Decision:
- Gate Result: pass | needs-fix | blocked
```

## Failure Handling
- 配置、artifact 与 boot log 不一致时先停在 host/build 域，不通过设备写入“试出来”。
- 必须保留的数据没有可验证 backup/recovery 时禁止 destructive migration。
- 写后 readback、boot 或数据保留任一失败时立即停止扩批并执行 recovery/rollback。
- 设备出现只读/挂载异常时切 `adk-systematic-debugging`，保留原始 boot/storage evidence，不重复破坏性写入。

## Quality Gate
- 配置、产物和运行态证据必须可追溯；不一致时结论为 `needs-fix`。
- 每个必须保留的分区都要声明 erase/write 风险和验证方法。
- FS/布局切换必须有 dry-run、单设备真实迁移、失败恢复和 rollback 证据后才能扩批。
- `release-preparation`、构建成功或 OTA package 生成成功都不得推导 live-device storage-write/flash authority。
