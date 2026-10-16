---
name: adk-performance-profiling-embedded
description: 嵌入式性能分析：有指标时测真实负载并交替 A/B；无指标不启用
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
- 量化瓶颈。

## Prerequisites
- 锁定 KPI（时延、吞吐、CPU、内存、功耗）。
- 固定基准场景。

## Workflow
1. 核实**真实负载**计数和正确输出，无活动记 `run-validity=invalid`。
2. 锁定源码/编译/输入哈希、频率/温度/供电/预热与样本预算。
3. 交替 A/B/A/B 采样，比较 p50/p95/p99、波动和环境漂移。
4. 检查热点/内存/功耗、功能等价及热稳定；无效样本记 no-gain。
5. 超预算须回滚，长稳复验须用真实场景。

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

## 火焰图
按目标 trace 能力选择 perf 或 DWT/ETM，生成热点归因报告。

## 瓶颈定位清单
| 瓶颈类型 | 诊断信号 | 工具 |
|----------|----------|------|
| CPU 热点 | perf 采样热点 | perf record + flame graph |
| 内存泄漏 | 堆持续增长 | valgrind --tool=memcheck |
| I/O 阻塞 | 线程长时间 wait | strace -T / perf trace |
| 锁竞争 | mutex wait 时间长 | perf lock / lockstat |
| 缓存未命中 | LLC miss rate 高 | perf stat -e cache-misses |

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "看起来没问题了" | 未经量化对比无法确认优化效果 | 必须提供前后同口径数据 |
| "Valgrind 太慢不实用" | 目标设备可能无法运行 Valgrind | 选择宿主 memcheck/ASan 或板端内存计数；不得把不同编译优化等级当作同口径性能对照 |
| "火焰图看不懂" | 归因不等于整体收益 | 先用采样计数复核热点 |

## Evidence Template
```md
- Source / Build / Device / Input Hash:
- Workload Counts / run-validity: valid | invalid | not-run
- A/B/A/B Order and Sample Count:
- p50/p95/p99 Before/After and Uncertainty:
- Functional and Thermal Side Effects:
- Rollback / Reproduction:
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

- **输入验证**：校验输入与数据口径
- **重试/超时**：按目标场景预算；无效测量不重复刷分。
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
