---
name: adk-embedded-storage-layout-migration
description: 嵌入式存储布局和文件系统迁移治理，覆盖 UBI/UBIFS/SquashFS/ubiblock、业务分区保留、OTA 迁移、启动日志校验和回滚边界
version: 1.0.0
last_updated: 2026-06-28
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
  - 分区表、defconfig/current.configs、rootfs 挂载脚本、ubinize/OTA layout、boot log、业务分区保留要求、回滚策略
outputs:
  - 迁移判定、受影响分区、保留策略、构建/升级路径、boot log 验证点、回滚与剩余风险
constraints:
  - 不得把文件系统形态切换称为普通 regular OTA，除非迁移和回滚证据完整
  - 必须优先保护 /factory、/data、/ota 等现场数据分区
  - boot log 与配置冲突时，以运行态证据为准继续追查
---

# adk-embedded-storage-layout-migration

## Goal
- 管理嵌入式设备存储布局、UBI volume 和文件系统形态迁移。
- 防止“配置已改但产物/启动脚本/OTA 仍走旧路径”的半升级状态。

## Prerequisites
- 已知道目标产品 profile、分区布局和升级方式。
- 已拿到配置、构建产物或 boot log 中至少一种证据。
- 已明确哪些现场分区必须保留。

## Workflow
1. 建立现状矩阵：boot/rootfs、业务分区、factory/data/ota、misc/pstore 等分区的 volume type、filesystem、mount path。
2. 判定变更类型：普通内容更新、布局迁移、文件系统切换、回滚迁移或产线重刷。
3. 对齐配置链：defconfig、current.configs、partition table、ubinize config、rootfs mount script、OTA layout 和 release metadata。
4. 保护现场数据：优先采用只更新目标 volume 的迁移包；避免 whole-ubia 覆盖 `/factory`、`/data`、`/ota`。
5. 检查构建顺序：确认 rootfs、customer image、OTA/SD 包在配置变更后重新生成。
6. 解析 boot log：确认 kernel cmdline、UBI attach、volume type、`ubiblock` 创建、mount 成功/失败和 fallback 路径。
7. 设计验证：冷启动、OTA 升级、断电、回滚、重复升级、现场数据保留和只读/可写语义。
8. 输出迁移门禁：哪些证据通过，哪些仍需 HIL 或板端数据。

## Commands
```bash
rtk rg -n "UBIFS|squashfs|ubiblock|factory|data|ota|ubinize|partition|layout" <repo>
rtk rg -n "MOUNTPT|MOUNTPARAM|FSTYPE|VOL_TYPE|rootfstype|ubi.mtd" <repo>
rtk rg -n "ubi0:|ubiblock|Mounted root|mounting .*customer|Kernel command line" <boot-log>
```

## Evidence Template
```md
- Migration Type:
- Preserve Requirements:
- Layout Matrix:
  | Partition | Volume | FS | Mount | Update Method | Preserve |
  |---|---|---|---|---|---|
- Config Chain:
- Build Artifacts:
- Boot Log Evidence:
- OTA/SD Path:
- Rollback Plan:
- Gate Result: pass / needs-fix / blocked
```

## Quality Gate
- 配置、产物和 boot log 必须三方一致；不一致时结论为 `needs-fix`。
- 每个必须保留的分区都要声明是否会被擦写。
- 文件系统切换必须有升级路径、失败回滚和板端验证计划。
- 只读/可写语义必须和产品 profile 一致。
