---
name: adk-production-field-readiness
description: 嵌入式量产、产测、烧录、诊断、OTA、回滚与现场维护 readiness
version: 1.0.0
last_updated: 2026-05-19
triggers:
  - "量产"
  - "产测"
  - "烧录"
  - "诊断"
  - "现场维护"
  - "OTA"
  - "回滚"
  - "RMA"
  - "设备健康检查"
  - "production-field"
  - "field readiness"
  - "embedded-production-field-readiness"
  - "simulate-device"
  - "模拟设备"
  - "设备状态机"
  - "自动推进"
non_triggers:
  - 通用 Web 发布
  - 纯版本号整理且不涉及设备交付
inputs:
  - 设备型号、硬件版本、固件/镜像版本、生产线流程、现场维护约束
outputs:
  - 量产/现场 readiness 清单、验证矩阵、回滚策略、诊断包与残留风险
constraints:
  - 不得把构建成功等同于可量产
  - OTA 或现场升级必须声明回滚路径
  - 产测和现场诊断必须有可审计证据
---

# adk-production-field-readiness

## Goal
- 覆盖嵌入式全栈中容易被软件开发流程遗漏的量产、产测、烧录、诊断、OTA、RMA 和现场维护闭环。
- 把“可运行”提升为“可生产、可诊断、可升级、可回退、可维护”。
- 明确该 skill 与 `adk-release-versioning` 的边界：版本策略归 release，设备交付 readiness 归本 skill。

## Prerequisites
- 已确认目标设备、硬件版本、BOM/板级差异、固件/镜像版本和生产批次约束。
- 已知道烧录入口、产测入口、日志/诊断入口和现场升级入口。
- 已明确哪些验证可自动化，哪些必须由 HIL、工装或人工板级证据补足。

## Workflow
1. **范围确认**：记录设备型号、硬件版本、固件版本、生产线/现场约束和非目标。
2. **制品清单**：列出 bootloader、kernel、rootfs、RTOS image、配置、签名、校验和、上位机工具版本。
3. **烧录链路**：确认 flashing 命令、工装、分区、失败重试、掉电保护和烧录日志留存。
4. **产测矩阵**：覆盖电源、时钟、外设、通信、传感器/执行器、校准、唯一标识和边界样本。
5. **诊断能力**：确认串口、日志、dump、健康状态、错误码、现场包导出和隐私/密钥处理。
6. **OTA 与回滚**：声明升级入口、兼容性、断电场景、双分区/恢复分区、回滚触发和验收证据。
7. **RMA/现场维护**：定义现场复现信息、最小日志包、恢复步骤、版本判定和不可恢复条件。
8. **验证证据**：记录命令、退出码、产测报告、boot log、OTA 演练、回滚演练和残留缺口。
9. **试点测量**：涉及 Agent/自动化生产率结论时，按 `references/pilot-measurement-evidence.md` 记录任务选择、人类基线、分离时间和并发证据。
10. **签署结论**：输出 `ready | needs-fix | blocked`，并列出 go/no-go 条件。

## Readiness Matrix
```md
| Area | Item | Evidence | Owner | Status |
|---|---|---|---|---|
| artifact | bootloader/kernel/rootfs/image checksum |  |  | pending |
| flashing | flash command + failure retry |  |  | pending |
| production-test | factory test report |  |  | pending |
| diagnostics | log/dump/error-code package |  |  | pending |
| ota | upgrade + rollback drill |  |  | pending |
| field | RMA/field recovery runbook |  |  | pending |
```

## Commands
```bash
# MCU 发布工具入口
rtk bash scripts/firmware-release.sh profile <profile>
rtk bash scripts/firmware-release.sh package-external --profile <profile> --boot <boot.hex> --app <app.hex> --version <x.y.z> --output-dir /tmp/adk-pilot/<target>/out
rtk bash scripts/firmware-release.sh check-package /tmp/adk-pilot/<target>/out/<bundle>

# 烧录/readback 先 dry-run，再进入实机阶段
rtk python3 /tmp/adk-pilot/<target>/out/<bundle>/burn_firmware.py --dry-run
rtk python3 /tmp/adk-pilot/<target>/out/<bundle>/readback_verify.py --dry-run

# SoC/Linux 与整机 OTA 入口
rtk bash build.sh verify
rtk bash build.sh self-check
rtk bash build.sh modules-status
rtk bash tools/ota-packager/ota-packager.sh self-test --json
```

## Evidence Promotion
- `planned -> evidence-ready`: 至少有一个真实工程输入、一组可复跑命令、制品清单、正负路径证据和残留缺口。
- `evidence-ready -> regression-ready`: 必须补实机烧录/readback、boot log、HIL/SIL 或产测报告、OTA/rollback 演练和现场诊断包。
- `production-ready`: 不是 pilot 状态；必须由项目 release gate 另行签署。

## Evidence Template
```md
- Device / HW Revision:
- Firmware / Image Version:
- Artifact List:
- Flashing Evidence:
- Production Test Matrix:
- Diagnostics Package:
- OTA / Rollback Evidence:
- Field Maintenance Runbook:
- Gaps / Not Tested:
- Final Readiness: ready | needs-fix | blocked
```

## Failure Handling
- 无法获取硬件或工装时，结论最多为 `blocked` 或 `needs-fix`，不得声明 ready。
- 烧录失败或启动失败时，切到 `adk-systematic-debugging`，先定位 boot log、分区、签名和电源状态。
- OTA 成功但回滚未验证时，不能发布现场可升级结论。
- 产测脚本不稳定时，先归类为测试波动或工装问题，不得把失败静默忽略。

## Quality Gate
- 必须列出制品、烧录、产测、诊断、升级、回滚六类证据或明确缺口。
- 必须说明硬件版本和固件版本，禁止只写“当前版本”。
- 发布到现场前必须有回滚或恢复路径。
- 诊断包不得包含未脱敏密钥、凭证或用户隐私。
- 最终 ready 结论必须可由命令、日志或报告复核。
