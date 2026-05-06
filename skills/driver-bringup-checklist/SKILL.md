---
name: driver-bringup-checklist
description: 驱动 bring-up 标准检查清单
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "驱动开发"
  - "驱动调试"
  - "外设联调"
non_triggers:
  - 稳定量产驱动小改
inputs:
  - 芯片型号、总线类型
outputs:
  - bring-up checklist
constraints:
  - 必须覆盖时钟、复位、中断、DMA
---

# driver-bringup-checklist

## Goal
- 通过清单化流程快速收敛驱动首板联调问题。
- 确保每个外设从上电到稳定运行的完整路径可验证。

## Prerequisites
- 确认硬件版本、引脚复用（pinmux）、供电和时钟配置一致。
- 准备串口日志、调试探针和寄存器读写工具（devmem/OpenOCD）。
- 获取芯片参考手册（TRM）与外设寄存器映射表。

## Workflow
1. **上电前检查**：电源电压、时钟源、复位信号、pinmux 配置。
   ```bash
   # 验证时钟使能
   devmem2 0x40023830 w  # RCC_AHB1ENR (STM32 示例)
   # 验证 pinmux
   devmem2 0x40020000 w  # GPIOA_MODER
   ```
2. **驱动框架结构确认**：确认驱动代码遵循平台框架（Linux platform_driver / RTOS 设备模型）。
   ```bash
   # Linux: 检查设备树节点与驱动匹配
   ls /sys/bus/platform/devices/
   cat /proc/device-tree/soc/serial@40011000/status
   # RTOS: 检查设备注册
   list_device
   ```
3. **总线连通性验证**：I2C/SPI/UART/CAN 基础收发。
   ```bash
   # I2C 扫描
   i2cdetect -y 0
   # SPI 回环测试
   spidev_test -D /dev/spidev0.0 -p "Hello" -v
   # UART 收发
   echo "AT" > /dev/ttyS1 && cat /dev/ttyS1
   # CAN 发送
   cansend can0 123#DEADBEEF
   ```
4. **设备注册与初始化路径验证**：最小功能先通，再启中断/DMA。
   ```bash
   # 检查中断注册
   cat /proc/interrupts | grep <device>
   # 检查 DMA 通道
   cat /sys/class/dma/dma0chan*/in_use
   # dmesg 驱动初始化日志
   dmesg | grep -i <driver_name>
   ```
5. **异常分支验证**：超时、CRC 错误、设备不存在、总线错误。
6. **稳定性检查**：循环收发、长稳运行（>= 24h）、重启恢复。

## Commands
```bash
# 寄存器读写
devmem2 <phys_addr> w <value>
devmem2 <phys_addr>

# 内核日志
dmesg | tail -n 200
dmesg -w  # 实时跟踪

# 设备节点检查
ls -la /dev/<device>*
cat /sys/class/<class>/<device>/uevent

# 中断统计
cat /proc/interrupts
cat /proc/softirqs

# I2C/SPI 工具
i2cdetect -y <bus>
i2cget -y <bus> <addr> <reg>
i2cset -y <bus> <addr> <reg> <value>
spidev_test -D /dev/spidev<b>.<c> -p "test"

# GPIO 操作
echo <pin> > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio<pin>/direction
echo 1 > /sys/class/gpio/gpio<pin>/value

# 驱动自检
<driver-selftest-cmd> --smoke
```

## Evidence Template
```md
- Hardware Baseline:
  - Board Rev: ____
  - SoC: ____
  - Power Rail: ____V (measured)
  - Clock Source: ____ MHz
- Pinmux Config: [link to dts/pinctrl diff]
- Bus Probe Result:
  | Bus | Device | Address | Status |
  |-----|--------|---------|--------|
  | I2C0 | sensor | 0x68 | PASS/FAIL |
- Init Sequence Result: [dmesg log link]
- Interrupt/DMA Result:
  - IRQ registered: YES/NO
  - DMA channel: ____
  - Latency: ____ us
- Error Path Result: [timeout/CRC/missing device]
- Long-run Result: [duration, error count, restart count]
```

## Failure Handling
- 若总线基础通信失败，先回滚到硬件基线排查（万用表量电压、示波器看波形）。
- 若中断异常，先禁 DMA 做最小闭环验证再逐项开启。
- 若 devmem 读回全 0 或全 F，检查时钟使能与地址映射。
- 若驱动 probe 失败，检查设备树 compatible 字符串与驱动 of_match_table 一致性。

## Quality Gate
- 清单需覆盖时钟、复位、中断、DMA 四类检查。
- 每类至少给一个通过证据或失败日志。
- 未完成最小闭环前，不得声明"驱动已完成 bring-up"。
- 所有寄存器读写操作必须记录物理地址与预期值。
- 长稳测试需 >= 24h 且零异常计数。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
