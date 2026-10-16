---
name: adk-performance-profiling-embedded
description: 嵌入式性能剖析与优化路径
version: 1.1.0
last_updated: 2026-10-16
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
  - 优化前后必须可量化对比
---

# adk-performance-profiling-embedded

## Goal
- 用数据定位瓶颈并输出可回滚的优化方案。

## Prerequisites
- 锁定 KPI（时延、吞吐、CPU、内存、功耗）。
- 准备稳定可重复的基准场景。

## Workflow
1. 固定真实性：确认真实负载确实执行（请求/帧/任务计数与有效输出）；无活动则 `run-validity=invalid`，不得报性能增益。
2. 冻结可比条件：代码 SHA、构建选项、输入哈希、CPU 频率、设备与固件、温度、供电、并发及预热条件。
3. 采集基线与候选：按预先声明的样本预算做 A/B/A/B 交替测量，避免时序、热漂移或缓存偏差；不接受单次最佳值比较。
4. 瓶颈定位：CPU、I/O、内存、锁、功耗与实时尾时延；同时记录 p50/p95/p99、误差范围和异常样本原因。
5. 保留负结果：样本不足、环境漂移、真实负载未运行、输出不等价或显著回归时标为 invalid/no-gain，不能挑选有利数据。
6. 验证副作用与回滚：同时检查功能、热稳定、能耗/内存峰值和实时任务期限，按目标预算执行稳定性复验。

## Commands
```bash
perf stat -p <pid> -- sleep 30
perf record -g -p <pid> -- sleep 30 && perf report --stdio
gprof <binary> gmon.out > analysis.txt
valgrind --tool=callgrind --callgrind-out-file=callgrind.out <binary>
callgrind_annotate callgrind.out
valgrind --tool=massif --pages-as-heap=yes <binary>
ms_print massif.out.<pid>
<benchmark-cmd> --scenario <name> --repeat <declared-sample-count>
```

## 火焰图生成
```bash
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
# 嵌入式场景：从 DWT/ETM trace 导出
<trace-decode-cmd> --input etm_trace.bin | stackcollapse-perf.pl | flamegraph.pl > mcu_flame.svg
```

## 瓶颈定位清单
| 瓶颈类型 | 诊断信号 | 工具 |
|----------|----------|------|
| CPU 热点 | 函数采样占比 >20% | perf record + flame graph |
| 内存泄漏 | 堆持续增长 | valgrind --tool=memcheck |
| I/O 阻塞 | 线程长时间 wait | strace -T / perf trace |
| 锁竞争 | mutex wait 时间长 | perf lock / lockstat |
| 缓存未命中 | LLC miss rate 高 | perf stat -e cache-misses |

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "看起来没问题了" | 未经量化对比无法确认优化效果 | 必须提供前后同口径数据 |
| "Valgrind 太慢不实用" | 目标设备可能无法运行 Valgrind | 选择宿主 memcheck/ASan 或板端内存计数；不得把不同编译优化等级当作同口径性能对照 |
| "火焰图看不懂" | 火焰图是最直观的热点可视化 | 先看宽峰（占比高的函数） |

## Evidence Template
```md
- Source/Build/Device/Input Hashes and Real Workload Counts:
- run-validity: valid | invalid | not-run
- Warmup/Sample Budget and Alternating A/B/A/B Order:
- Baseline Metrics and p50/p95/p99 Distribution:
- Bottleneck Location:
- Optimization Change:
- Before/After Delta / Uncertainty:
- Side Effects (power, memory, thermal, deadlines):
- Rollback and Reproduction Commands:
```

## Failure Handling
- 数据波动过大时，先固定环境和输入再复测。
- 优化带来副作用超阈值时立即回退并重新评估。

## Quality Gate
- 必须提供优化前后同口径对比数据，含真实负载活动、输入输出等价性、环境/构建身份和 run-validity。
- 必须说明收益与副作用是否可接受。
- 必须给出可执行回退方案。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 失败先分类，测量无效不以同样条件盲目重试；需要重测时使用任务约定的预算与退避。
- **超时控制**: 根据目标设备/负载的声明预算设置单步和总体上限；不可把示例常数当硬件通用阈值
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
