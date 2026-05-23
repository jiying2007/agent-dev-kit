# Pilot: embedded-production-field-readiness

status: evidence-ready

## 目标场景

面向量产、产测、烧录、诊断、OTA、回滚、RMA 和现场维护的 readiness 验证，确认 adk 能把设备交付从“软件可运行”推进到“可生产、可诊断、可升级、可回退、可维护”。

## 预期路由

- primary: `adk-production-field-readiness`
- supporting: `adk-release-versioning`, `adk-integration-hil-sil`, `adk-verification-before-completion`
- fallback: 仅当设备交付链路无法提供产测、诊断或现场证据时显式记录 blocked

## 验证证据

### 原始任务输入

用户要求基于两个真实嵌入式工程推进落地：

- MCU 发布链路：`firmware-release-tools`
- SoC/Linux 构建与整机 OTA 链路：`pcr02_ssc305_compile/build.sh`

### Evidence Sources

| Source | Role | 本次使用方式 |
|---|---|---|
| MCU firmware release tools | MCU 制品、manifest、checksum、烧录脚本、OTA payload、NAS 发布 dry-run | 使用 `mm32spin023c` profile，在 `/tmp/adk-pilot/mm32` 生成样本 boot/app IHEX、package、checksum、dry-run 烧录/readback 和 NAS would-publish 证据 |
| PCR02 SoC build script | SoC/Linux 源码门禁、自检、模块状态、整机 OTA 入口 | 执行 `verify`、`self-check`、`modules-status`、MCU resolver self-test 与 OTA packager self-test；默认 clean gate 失败作为负证据保留 |
| Simulated device harness | 无硬件的设备状态机验证 | `--simulate-device` 自动生成 flash/readback/boot/HIL/OTA/rollback/field-package 证据，推进到 `simulated-pass` |

### Scope / Non-goal

- 本 pilot 证明 adk 可以把真实 MCU + SoC 发布链路收敛为可审计 evidence-ready 证据。
- 本次没有执行真实 J-Link 烧录、真实 readback、真实启动串口采集、真实 HIL 产测、真实整机 OTA 包生成、NAS publish、tag 或 push。
- 模拟设备闭环可把 pilot 推进到 `simulated-pass`，但不能声明设备已 production-ready；生产放行仍需真实硬件和现场证据。

### Readiness Matrix

| Area | Item | Evidence | Status |
|---|---|---|---|
| artifact | MCU package manifest、image list、checksum、zip、模拟现场包 | `package_manifest.json` schemaVersion `2.0`，`validation.passed=true`，`checksums.sha256.txt` 校验通过；模拟现场包含 manifest 和 guide | pass |
| flashing | 默认烧录脚本、factory recovery 脚本、保留区保护、模拟 flash | `burn_firmware.py --dry-run` 生成 merged image J-Link script；`erase_and_burn.py --dry-run` 拒绝擦除保留区；`--force-erase --role production-full --dry-run` 生成 factory script；模拟 flash 写入版本化状态 | simulated-pass |
| readback | readback 验证入口与模拟 hash 对比 | `readback_verify.py --dry-run` 生成 `savebin` 脚本；模拟 readback digest 与 flash state 匹配 | simulated-pass |
| ota | MCU app OTA payload、SoC 整机 OTA 工具入口、模拟 OTA | `ota_upgrade_plan.json` 指向 `mm32spin023c_app.bin`；PCR02 resolver self-test 与 ota-packager self-test 通过；模拟 OTA 切换 inactive slot 并启动新版本 | simulated-pass |
| release | NAS 挂载检查与发布 dry-run | `setup-nas-mount.sh --check` 通过；`publish-nas --dry-run --json` 输出 `would-publish` | partial |
| source | SoC 源码一致性门禁 | 默认 `build.sh verify/self-check` 因 dirty gate 失败；`--allow-dirty` 只读复跑通过并输出 main/app SHA | partial |
| modules | SoC 组件状态 | `modules-status` 输出 repo/local/prebuilt 模块状态；存在 dirty repo 与一个未链接模块，保留为下一阶段风险 | needs-fix |
| production-test | boot log、HIL/SIL、诊断 CLI | 模拟 boot log 输出 `BOOT_OK`，模拟 HIL 覆盖 power-cycle、diagnostic CLI 和 fault injection；真实工装待补 | simulated-pass |
| field | RMA、现场日志、升级失败恢复 | 模拟 rollback 恢复旧版本和 active slot，生成无凭据现场维护包；真实现场包待补 | simulated-pass |

### 模拟设备自动推进

`scripts/run-embedded-production-field-pilot.sh --simulate-device` 会在输出目录下生成 `sim-device/` 状态机：

1. `sim-device-flash`：写入 profile、version 和 flash digest。
2. `sim-device-readback`：计算 readback digest 并与 flash digest 比对。
3. `sim-device-boot`：生成 `BOOT_OK` 和诊断通过日志。
4. `sim-device-hil`：生成 power-cycle、diagnostic CLI、fault injection 报告。
5. `sim-device-ota`：模拟 inactive slot OTA 升级并启动新版本。
6. `sim-device-rollback`：模拟回滚到上一版本和 active slot。
7. `sim-device-field-package`：生成不含凭据的现场维护包 manifest 与 guide。

该模式只用于无硬件环境的自动推进和回归，不替代真实设备放行。

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/firmware-release.sh --help` | 0 | MCU release CLI 暴露 profile、package-external、check-package、publish-nas 等入口 | command output |
| `rtk bash scripts/firmware-release.sh profile mm32spin023c` | 0 | profile 覆盖 flash base/size、boot flag、app address、J-Link、OTA payload | command output |
| `rtk bash scripts/setup-nas-mount.sh --check` | 0 | CIFS tool、credentials、fstab、mount、release root 检查通过 | command output |
| `rtk python3 -c "<write_ihex sample boot/app into /tmp/adk-pilot/mm32>"` | 0 | 生成本地 boot/app IHEX 样本，避免依赖真实固件或仓库写入 | `/tmp/adk-pilot/mm32` |
| `rtk bash scripts/firmware-release.sh check-package /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle` | 2 | 负路径：package 生成前缺少 manifest，检查正确失败 | command output |
| `rtk bash scripts/firmware-release.sh package-external --profile mm32spin023c --repo /tmp/adk-pilot/mm32 --boot /tmp/adk-pilot/mm32/boot.hex --app /tmp/adk-pilot/mm32/app_v0.0.9.hex --version 0.0.9 --output-dir /tmp/adk-pilot/mm32/out` | 0 | 生成 package、manifest、checksums 和 zip | `/tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle` |
| `rtk bash scripts/firmware-release.sh check-package /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle` | 0 | package manifest 与 checksums 校验通过 | command output |
| `rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/burn_firmware.py --dry-run` | 0 | 生成默认 merged image J-Link 烧录脚本，不擦除保留区 | command output |
| `rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/erase_and_burn.py --dry-run` | 3 | 负路径：检测到 data reserve，拒绝直接 chip erase | command output |
| `rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/erase_and_burn.py --force-erase --role production-full --dry-run` | 0 | 生成 factory/full recovery J-Link 脚本 | command output |
| `rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/readback_verify.py --dry-run` | 0 | 生成 readback `savebin` 验证脚本 | command output |
| `rtk bash scripts/firmware-release.sh publish-nas --release-root /tmp/adk-pilot/mm32/nas-release --batch-id adk-pilot --timestamp 20260519-105700 --item mm32spin023c=/tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle --dry-run --json` | 0 | NAS 发布 dry-run 输出 `would-publish` 与 source digest | command output |
| `rtk bash build.sh verify` | 1 | 负路径：默认源码 clean gate 因主仓 dirty 失败 | command output |
| `rtk bash build.sh self-check` | 1 | 负路径：默认自检同样被 dirty gate 拦截 | command output |
| `rtk bash build.sh verify --allow-dirty` | 0 | 只读源码验证通过，输出 main/app SHA；不作为 clean release 证据 | command output |
| `rtk bash build.sh self-check --allow-dirty` | 0 | SoC project/app/toolchain/vehicle OTA config/resolver/ota-packager 入口自检通过 | command output |
| `rtk bash build.sh modules-status` | 0 | 输出 local/repo/prebuilt 模块状态，暴露 dirty repo 与未链接模块风险 | command output |
| `rtk bash tools/firmware-release-tools/resolve-latest-release.sh --self-test` | 0 | MCU release resolver 自检通过，不访问 NAS | command output |
| `rtk bash tools/ota-packager/ota-packager.sh self-test --json` | 0 | OTA packager CLI 自检通过 | command output |
| `rtk bash scripts/run-embedded-production-field-pilot.sh --mcu-root <firmware-release-tools> --soc-root <soc-build-root> --simulate-device --out /tmp/adk-pilot/embedded-production-field-readiness` | 0 | MCU + SoC + simulated device production-field evidence runner 可复跑，生成 `evidence.md`、`summary.json` 和模拟设备现场包 | command output |

### 生成制品摘要

- Package dir: `/tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle`
- Runner evidence: `/tmp/adk-pilot/embedded-production-field-readiness/evidence.md`
- Simulated device state: `/tmp/adk-pilot/embedded-production-field-readiness/sim-device/state`
- Version: `0.0.9`
- Default image: `mm32spin023c_boot_flag_app_merged.hex`
- Factory image: `mm32spin023c_flash_full.hex`
- OTA payload: `mm32spin023c_app.bin`
- Package manifest: `package_manifest.json`
- Checksum file: `checksums.sha256.txt`
- OTA plan: `ota_upgrade_plan.json`

### Go / No-go Decision

| Decision | Result | Reason |
|---|---|---|
| Pilot status | `evidence-ready` | 已有真实工程输入、可复跑命令、正负路径证据和制品清单 |
| Device production readiness | `simulated-pass` | 模拟设备 flash/readback/boot/HIL/OTA/rollback/field-package 闭环通过；真实硬件放行仍需补证据 |
| Fallback decision | `no fallback` | 该场景由 adk 原生 `adk-production-field-readiness` 承接，Superpowers 无需介入 |

### 残留缺口

- 设备型号、硬件版本和固件/镜像版本。
- 实机 J-Link 烧录、真实 readback 对比和串口 boot log。
- PCR02 `release`、`vehicle-ota` 和 `publish-soc` 的真实或 dry-run 输出。
- 产测矩阵、HIL/SIL 报告、诊断包与错误码清单。
- 真实 OTA 升级和回滚演练。
- RMA/现场维护 runbook、真实现场日志包和责任 owner。
