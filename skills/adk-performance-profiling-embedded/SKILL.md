---
name: adk-performance-profiling-embedded
description: "用于有指标的嵌入式性能分析、栈上界判读和真实负载 A/B；不用于无指标猜测或推断收益。"
version: 1.1.5
last_updated: 2026-11-15
triggers:
  - "性能分析"
  - "性能优化"
  - "性能调优"
  - "评估 MCU 栈上界"
  - "评估 RTOS 栈上界"
non_triggers:
  - 无性能指标诉求的小改
inputs:
  - 性能指标、采样数据
outputs:
  - 瓶颈定位与优化建议
constraints:
  - 优化效果必须可量化对比；只定位瓶颈时不要求已有候选改动
---

# adk-performance-profiling-embedded

## Goal
固定基准场景与 KPI（时延、吞吐、CPU、内存、功耗），量化瓶颈或候选收益。

## Workflow
1. 核**真实负载**计数/正确输出；无活动 `run-validity=invalid`。固定源码/编译/输入 hash、设备、频率/温度/供电/预热、采样点/预算及扰动。
2. **定位瓶颈**：先低开销统计 CPU、等待/I/O、锁、内存，再采样原因；给证据、可证伪候选和最小实验，无候选不强制 A/B。
3. **比较候选**：等价输入输出、有效负载后 A/B/A/B，核波动/漂移。时延报 p50/p95/p99，吞吐报有效工作量/时间，Flash/RAM 报段/峰值，能耗按同工作量；段大小不用分位数。
4. 核功能、内存、功耗及热稳定，超预算回滚；有效候选做真实长稳复验。无效 `invalid`，样本不足/噪声不可分 `inconclusive`，有效证据支持无收益才 `no-gain`；均留原因、不宣传收益。噪声先查环境不刷分；只读诊断不授权优化/设备配置变更。

## Target Execution Gate
- `linux-embedded`：核内核/用户态、架构、计数器权限/资源；CPU 用 perf/flame graph，堆用 memcheck，I/O 用 strace -T/perf trace，锁用 perf lock/lockstat，LLC miss 用 perf stat -e cache-misses。先核采样计数；热点不等于整体收益，用户态工具不通用于内核/MCU。
- `mcu-rtos` / `mcu-baremetal`：按支持用板端计数/trace、DWT/ETM、GPIO timing、stack/heap high-water、ELF/map；host 分析不能替代板端 `not-measured`。
- 核工具、系统/编译身份和权限，不隐式注入/改配置。资源不足可选 host memcheck/ASan 或板端计数；不跨编译优化等级比较性能。

## Commands
仅选支持工具和预算窗口，留命令/退出码/耗时；失败不消费旧结果：
```bash
perf stat -p <pid> -- sleep <sample-window-seconds>
perf record -g -p <pid> -- sleep <sample-window-seconds> && perf report --stdio
valgrind --tool=callgrind --callgrind-out-file=callgrind.out <binary> && callgrind_annotate callgrind.out
```
benchmark 使用项目真实命令，不假定通用参数。

## MCU 资源实测（按需）
Flash/RAM/stack、DMA/retention 或 KWS/音频读 `references/mcu-memory-footprint.md`：同工具链 ELF/map/size，区分 `.su` frame、调用链和实测余量，不从行数或 high-water 推断完整资源上界。

交付上述原始证据、样本数/KPI/不确定性和复现入口；无有效采样只给假设与缺口。
