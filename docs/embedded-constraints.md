# Embedded Constraints

## 目标

本文件是嵌入式场景的常驻约束层，只保留会影响方案安全性的硬限制。

## 约束

- 默认假设目标环境可能跨芯片/板级约束、启动链、BSP、OS/runtime、驱动、组件、设备应用、上位机、产测诊断、量产和现场维护，并存在交叉编译、平台差异、资源受限和硬件状态不可完全模拟的问题。
- 任何驱动、BSP、RTOS、协议栈、启动链、OTA 或现场维护改动必须声明目标芯片、板卡、硬件版本、toolchain、OS/runtime 和验证环境。
- 不得把主机侧单测结果等同于上板验证；涉及寄存器、DMA、中断、电源、时钟、复位、pinmux、secure boot、烧录或外设时必须说明 HIL/SIL、boot log、波形、寄存器读回或替代验证证据。
- 性能结论必须附测量口径，包括负载、采样点、编译选项、缓存状态和硬件版本。
- 安全、发布、量产或现场结论必须覆盖回滚方式、降级路径、诊断包和现场恢复条件。

完整层级定义见 `docs/reference/embedded-fullstack-scope.md`。

## 加载方式

该文件由 `embedded_context_layers.L1-always-loaded` 引用，正文必须保持短小；详细案例放入 `knowledge/` 或具体 skill 的 `references/`。
