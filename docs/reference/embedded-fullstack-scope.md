# Embedded Full-stack Scope

## 目标

本文定义 adk 的嵌入式全栈边界，避免把范围误收缩为 `SoC/MCU/Linux/RTOS/驱动/组件/设备应用/上位机工具` 这类软件层枚举。

adk 面向嵌入式全栈开发，覆盖从芯片和板级约束、启动链、BSP、OS/runtime、驱动、中间件、协议栈、设备侧应用、上位机/产测/诊断工具，到构建、调试、验证、发布、量产和现场维护的完整工程闭环。

不覆盖通用 Web、互联网后端、云原生和纯业务系统开发；只有当主机侧工具服务于嵌入式交付链路时，才纳入 adk 范围。

## 范围层级

| 层级 | 覆盖内容 | 典型验证 |
|---|---|---|
| 芯片/板级约束 | SoC、MCU、MPU、DSP/NPU/GPU、FPGA、板卡、电源、时钟、复位、pinmux、memory map | 原理图/手册核对、寄存器读回、示波器/逻辑分析仪 |
| 启动链 | BootROM、SPL、U-Boot/Bootloader、secure boot、分区、镜像、rootfs、启动失败恢复 | boot log、串口控制台、镜像签名、启动回退 |
| BSP/系统层 | DTS/DTSI、Kconfig、kernel config、Yocto、Buildroot、SDK、rootfs、init/systemd | 交叉编译、最小系统启动、模块加载 |
| OS/runtime | bare-metal、RTOS、Linux、AMP/SMP、IPC、调度、内存、中断、DMA | 调度/时序测试、trace、latency、SIL/HIL |
| 驱动/外设 | 字符设备、网络、块设备、I2C/SPI/UART/CAN/USB/PCIe/Ethernet、sensor、display、audio、camera | probe 日志、寄存器、协议抓包、HIL |
| 中间件/协议栈 | 文件系统、网络栈、BLE/Wi-Fi/Cellular、工业协议、日志、配置、升级、诊断 | 协议一致性、异常路径、兼容性 |
| 设备侧应用 | RTOS task、Linux daemon、CLI/service、数据采集、控制逻辑、edge inference | host unit、SIL、系统 smoke、性能指标 |
| 上位机/交付工具 | 烧录、标定、诊断、日志解析、产测、HIL 控制、协议仿真 | CLI/GUI smoke、产测脚本、工具链回归 |
| 构建/制品 | CMake、Make、Yocto、Buildroot、toolchain、SDK、镜像、版本、签名 | build smoke、制品校验、SBOM/签名 |
| 验证/调试 | host unit、ctest、QEMU/SIL、HIL、静态分析、fault injection、设备调试通道、trace | Evidence Index、日志、波形、测试报告 |
| 安全/可靠性 | secure boot、密钥、权限、watchdog、brownout、恢复策略、长期稳定性 | 安全检查、故障注入、长稳、恢复演练 |
| 量产/现场 | 工厂测试、烧录流程、RMA、现场日志、远程升级、回滚、设备健康检查 | 产测报告、OTA 演练、现场诊断包 |

## 路由原则

- 需求探索默认使用 `adk-requirements-triage`，必须确认目标层级、非目标、接口边界、运行环境和验证资源。
- 启动链、BSP、rootfs 和板级移植默认使用 `adk-bsp-porting-playbook`。
- 驱动 bring-up 默认使用 `adk-driver-bringup-checklist`，必要时叠加 `adk-register-map-design` 与 `adk-embedded-debug-transport`。
- 量产、烧录、产测、诊断、OTA、回滚和现场维护默认使用 `adk-production-field-readiness`。
- 测试策略默认使用 `adk-test-strategy`，并按 host unit、cross-build、SIL/QEMU、HIL、手工板级证据分层。
- 发布、版本和回退策略默认使用 `adk-release-versioning`，但不替代量产/现场 readiness。
- 最小可复跑测试样例位于 `examples/embedded-test-matrix/`，用于说明 host unit、CMake/CTest、交叉编译 smoke、QEMU/SIL、HIL 手工记录和故障注入证据形态。

## Pilot 覆盖要求

嵌入式全栈 pilot 不应只覆盖软件功能，还应逐步覆盖：

1. 板级/启动链：power/clock/reset/pinmux、Bootloader、kernel/rootfs、boot log。
2. 驱动/外设：寄存器、中断、DMA、协议交互、硬件 errata。
3. 设备侧应用/组件：接口契约、配置、日志、性能、异常路径。
4. 上位机/产测工具：烧录、诊断、标定、日志解析、HIL 控制。
5. 发布/现场：OTA、回滚、RMA、现场日志、设备健康检查。
6. 安全/可靠性：secure boot、watchdog、故障注入、长稳和恢复演练。
