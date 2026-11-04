# adk-interrupt-dma-patterns — 补充参考资料

此参考文件只提供可选背景、示例和检查提示；当前能力流程、权限、回退与放行结论以 `../SKILL.md`、Manifest 及运行时门禁为准。示例命令不得被解释为写权限授权。

## Commands
```bash
# 中断统计
cat /proc/interrupts
watch -n 1 "cat /proc/interrupts | grep <device>"

# 中断延迟测试
cyclictest -p 99 -i 1000 -l 10000 --mlockall -m

# DMA 状态
cat /sys/class/dma/dma0chan*/in_use

# ISR 代码审查
rg -n "ISR|IRQ|irq_handler|DMA.*IRQ" <driver_path>

# 寄存器级别中断检查
devmem2 <NVIC_ISER_addr>    # 中断使能寄存器
devmem2 <NVIC_IPR_addr>     # 中断优先级寄存器

# 逻辑分析仪 / 示波器触发
# （硬件工具，记录 GPIO toggle 测量 ISR 延迟）

# 压力测试
stress-ng --cpu 4 --io 4 --timeout 60s &
<latency-measure-cmd> --irq --dma --duration 60
```

## 设备权限说明

- `devmem2` 示例只允许只读参数并且设备身份已确认；任何寄存器写入或有负载影响的测试均需独立授权与回退方案。
