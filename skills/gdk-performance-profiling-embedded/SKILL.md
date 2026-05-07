---
name: gdk-performance-profiling-embedded
description: 嵌入式性能剖析与优化路径
version: 1.0.0
last_updated: 2026-05-06
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

# gdk-performance-profiling-embedded

## Goal
- 用数据定位瓶颈并输出可回滚的优化方案。

## Prerequisites
- 锁定 KPI（时延、吞吐、CPU、内存、功耗）。
- 准备稳定可重复的基准场景。

## Workflow
1. 建立基线：采集未优化版本指标。
2. 瓶颈分析：CPU 热点、I/O 阻塞、锁竞争、内存抖动。
3. 优化实验：单变量改动并控制环境变量。
4. 对比评估：量化收益与副作用。
5. 稳定性复验：长稳测试确认无回归。

## Commands
```bash
perf stat -p <pid> -- sleep 30
perf record -g -p <pid> -- sleep 30 && perf report --stdio
gprof <binary> gmon.out > analysis.txt
valgrind --tool=callgrind --callgrind-out-file=callgrind.out <binary>
callgrind_annotate callgrind.out
valgrind --tool=massif --pages-as-heap=yes <binary>
ms_print massif.out.<pid>
<benchmark-cmd> --scenario <name> --repeat 5
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
| "Valgrind 太慢不实用" | 生产环境的内存泄漏代价更高 | CI 中用 -O0 跑 memcheck |
| "火焰图看不懂" | 火焰图是最直观的热点可视化 | 先看宽峰（占比高的函数） |

## Evidence Template
```md
- Baseline Metrics:
- Bottleneck Location:
- Optimization Change:
- Before/After Delta:
- Side Effects:
```

## Failure Handling
- 数据波动过大时，先固定环境和输入再复测。
- 优化带来副作用超阈值时立即回退并重新评估。

## Quality Gate
- 必须提供优化前后同口径对比数据。
- 必须说明收益与副作用是否可接受。
- 必须给出可执行回退方案。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
