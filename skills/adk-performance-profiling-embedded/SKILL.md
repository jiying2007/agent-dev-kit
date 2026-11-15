---
name: adk-performance-profiling-embedded
description: "用于有明确指标时对嵌入式真实负载做性能分析和可比较的 A/B 验证；无指标不启用，也不用于仅凭推测宣布性能改善。"
version: 1.1.4
last_updated: 2026-11-15
triggers:
  - "性能分析"
  - "性能优化"
  - "性能调优"
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
- 量化瓶颈。

## Prerequisites
- 锁定 KPI（时延、吞吐、CPU、内存、功耗）。
- 固定基准场景。

## Workflow
1. 确定是定位瓶颈还是比较候选；核实**真实负载**计数和正确输出，无活动记 `run-validity=invalid`。
2. 锁定源码/编译/输入哈希、频率/温度/供电/预热、采样点和样本预算；先核采样器对负载的扰动。
3. **定位瓶颈**：低开销统计区分 CPU、等待/I/O、锁和内存，再采样最可能原因。交付证据、可证伪候选和最小实验；无候选版本不强制 A/B。
4. **比较候选**：功能等价、负载有效后 A/B/A/B 采样，核波动与漂移。时延报 p50/p95/p99；吞吐报有效工作量/时间，Flash/RAM 报段/峰值，能耗按同工作量，不给段大小造分位数。
5. 核功能、内存、功耗及热稳定。无效样本记 `invalid`，样本不足或无法区分噪声记 `inconclusive`；有效证据支持无收益才记 `no-gain`，均不能宣传收益。
6. 副作用超预算须回滚；有效候选的长稳复验使用真实场景。只读诊断不要求实施优化或触发设备配置修改。

## Target Execution Gate
- `linux-embedded`：按内核/用户态、架构、计数器权限和资源选择 `perf`/`strace`/`valgrind`；用户态工具不通用于内核或 MCU。
- `mcu-rtos` / `mcu-baremetal`：用板端计数/trace、DWT/ETM（如有）、GPIO timing、stack/heap high-water、ELF/map；无板端证据时 host 分析记 `not-measured`。
- 采样前核工具、活动负载、输入、系统/编译身份和权限；不隐式注入或改配置。资源不足时选 host memcheck/ASan 或板端计数，不能跨编译优化等级比较性能。

## Commands
仅选目标支持的工具，窗口和次数来自采样预算。保留命令、退出码和耗时；采集失败不得消费旧结果：
```bash
perf stat -p <pid> -- sleep <sample-window-seconds>
perf record -g -p <pid> -- sleep <sample-window-seconds> && perf report --stdio
valgrind --tool=callgrind --callgrind-out-file=callgrind.out <binary> && callgrind_annotate callgrind.out
```
benchmark 使用项目真实命令，不假定通用参数。

## MCU 资源实测（按需）
Flash/RAM/stack、DMA/retention 或 KWS/音频比较时读 `references/mcu-memory-footprint.md`；用同工具链 ELF/map/size，不由行数推算资源节省。

## 瓶颈定位清单
Linux 目标参考：CPU 热点用 perf/flame graph，堆增长用 memcheck，I/O 等待用 strace -T/perf trace，锁等待用 perf lock/lockstat，LLC miss 用 perf stat -e cache-misses；先核采样计数，热点不等于整体收益。

## Evidence Template
```md
- Source / Build / Device / Input Hash:
- Workload Counts / run-validity: valid | invalid | not-run
- Diagnosis: bottleneck evidence / falsifiable candidate / next experiment
- Comparison (when requested): A/B/A/B order / sample count / KPI / uncertainty / inconclusive or no-gain reason
- Functional and Thermal Side Effects:
- Rollback / Reproduction:
```

## Quality Gate
- 诊断有活动负载、归因证据和下一步实验；无有效采样只给假设与缺口。
- 收益结论须有等价输入输出、环境/构建身份、run-validity 和同口径对照；噪声先查环境，不重复刷分。副作用超预算回滚。
