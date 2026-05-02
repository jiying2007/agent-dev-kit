---
name: performance-profiling-embedded
description: 嵌入式性能剖析与优化路径
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 出现时延抖动、CPU 占用过高时
non_triggers:
  - 无性能指标诉求的小改
inputs:
  - 性能指标、采样数据
outputs:
  - 瓶颈定位与优化建议
constraints:
  - 优化前后必须可量化对比
---

# performance-profiling-embedded

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
<benchmark-cmd> --scenario <name> --repeat 5
```

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
