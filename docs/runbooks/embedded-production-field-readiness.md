# Embedded Production Field Readiness Runbook

## 目标

用真实嵌入式工程把量产、产测、烧录、诊断、OTA、回滚和现场维护证据收敛成可复跑 pilot。该 runbook 用于把 `adk-production-field-readiness` 从文档声明推进到 evidence-ready，不把 dry-run 结果误判为真实 production-ready。

## 适用范围

- MCU 固件发布工具：profile、manifest、checksum、烧录脚本、readback 脚本、OTA payload、NAS 发布 dry-run。
- SoC/Linux 构建脚本：源码门禁、自检、模块状态、整机 OTA 配置、MCU release resolver、OTA packager。
- 不适用于通用 Web、互联网后端、云原生或纯业务系统发布。

## Phase 0：安全边界

禁止在 pilot 初跑阶段执行：

- 真实调试探针烧录或 readback。
- `--publish`、`--push-tag`、`--force-publish-soc`。
- 修改 NAS、挂载配置、凭证文件或工厂发布目录。
- 清理 dirty worktree、重置源码或删除产物。

允许执行：

- `--help`、`profile`、`--check`、`verify`、`self-check`。
- 输出到 `/tmp/adk-pilot/...` 的 package/checksum/dry-run。
- 带明确记录的负路径验证。

## Phase 1：MCU Release Evidence

推荐先使用 adk 统一 runner 收集证据：

```bash
rtk bash scripts/run-embedded-production-field-pilot.sh --mcu-root <firmware-release-tools> --soc-root <soc-build-root> --out /tmp/adk-pilot/embedded-production-field-readiness
```

该 runner 会生成 `evidence.md`、`summary.json` 和逐命令日志；它只执行 dry-run、自检和 `/tmp` 本地产物，不执行真实烧录、发布、tag 或源码修改。

在 MCU release tool 工作区执行：

```bash
rtk bash ./scripts/firmware-release.sh --help
rtk bash ./scripts/firmware-release.sh profile mm32spin023c
rtk bash ./scripts/setup-nas-mount.sh --check
```

使用临时 boot/app 样本或历史已脱敏固件，在 `/tmp/adk-pilot/<target>` 生成 package：

```bash
rtk bash ./scripts/firmware-release.sh package-external --profile mm32spin023c --repo /tmp/adk-pilot/mm32 --boot /tmp/adk-pilot/mm32/boot.hex --app /tmp/adk-pilot/mm32/app_v0.0.9.hex --version 0.0.9 --output-dir /tmp/adk-pilot/mm32/out
rtk bash ./scripts/firmware-release.sh check-package /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle
```

烧录、readback 和发布只跑 dry-run：

```bash
rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/burn_firmware.py --dry-run
rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/erase_and_burn.py --dry-run
rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/erase_and_burn.py --force-erase --role production-full --dry-run
rtk python3 /tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle/readback_verify.py --dry-run
rtk bash ./scripts/firmware-release.sh publish-nas --release-root /tmp/adk-pilot/mm32/nas-release --batch-id adk-pilot --timestamp 20260519-105700 --item mm32spin023c=/tmp/adk-pilot/mm32/out/mm32spin023c_firmware_bundle --dry-run --json
```

## Phase 2：SoC / Vehicle OTA Evidence

在 SoC/Linux 构建工作区执行：

```bash
rtk bash build.sh verify
rtk bash build.sh self-check
rtk bash build.sh verify --allow-dirty
rtk bash build.sh self-check --allow-dirty
rtk bash build.sh modules-status
rtk bash tools/firmware-release-tools/resolve-latest-release.sh --self-test
rtk bash tools/ota-packager/ota-packager.sh self-test --json
```

解释规则：

- 默认 `verify/self-check` 如果因 dirty gate 失败，这是有效负证据，说明 release gate 生效。
- `--allow-dirty` 只能证明入口和配置自检可运行，不能作为 clean release 证据。
- `modules-status` 中的 dirty repo、missing link、未同步 upstream 必须进入残留风险。

## Phase 3：升级到 Regression-ready

满足以下条件后才允许从 `evidence-ready` 升级：

- 至少一次真实调试探针烧录和 readback 对比通过。
- 串口 boot log 证明镜像启动到预期服务或 RTOS task。
- HIL/SIL 或工装产测报告覆盖关键外设、通信、校准和唯一标识。
- `vehicle-ota` 或等价整机 OTA 包生成通过，并记录升级和回滚演练。
- NAS publish 在受控 release root 上通过，release manifest 与 batch manifest 可审计。
- 现场诊断包、RMA 信息清单和恢复步骤已脱敏归档。

## Evidence Index Template

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `<command>` | `<n>` | `<summary>` | `<path or command output>` | Skill | `adk-production-field-readiness` |

## 退出结论

- `evidence-ready`：已有真实工程输入、可复跑命令、正负路径证据、制品清单和明确缺口。
- `needs-fix`：缺少实机、HIL、OTA 回滚或现场维护证据，不允许声明 production-ready。
- `blocked`：缺少固件样本、构建入口、权限或必要工具，无法建立最小证据链。
