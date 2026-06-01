---
name: adk-bsp-analysis
description: BSP 代码分析、架构梳理、历史追溯
version: 1.0.0
last_updated: 2026-05-16
triggers:
  - bsp 分析
  - 代码梳理
  - 架构分析
  - patch 分析
non_triggers:
  - 驱动开发
  - 硬件调试
inputs:
  - BSP 代码目录
  - datasheet 文档
  - patch 文件
outputs:
  - 架构分析报告
  - 代码结构图
  - patch 分析报告
constraints:
  - 必须引用 datasheet 页码或章节
  - 必须标注置信度
  - 不确定事实必须明示待确认
---

# adk-bsp-analysis

## Goal
- 分析 BSP 代码结构、启动链路、平台抽象和历史补丁，输出可验证的架构理解与迁移风险。

## Prerequisites
- 已获得 BSP 源码、目标 SoC/board 信息和最少一份硬件参考资料。
- 已明确分析问题，例如启动链路、驱动迁移、patch 风险或架构梳理。
- 能访问基本代码搜索工具和构建/日志材料。

## Workflow
1. 确认范围：记录 BSP 根目录、SoC、board、kernel/RTOS 版本和分析目标。
2. 扫描结构：梳理 arch、drivers、dts、include、bootloader 相关入口。
3. 追踪链路：按 boot、probe、clock/reset、pinctrl、irq、DMA 建立调用关系。
4. 对照资料：把关键寄存器、位域和初始化顺序映射到 datasheet 或 reference manual。
5. 分析历史：读取 patch/commit，识别行为变化、兼容逻辑和技术债。
6. 输出结论：按高/中/低置信度区分已确认事实、待确认项、风险和验证动作。

## Commands
```bash
rg -n "module_init|builtin_platform_driver|of_match_table|compatible" <bsp-dir>
rg -n "clk_|reset_|pinctrl|ioremap|readl|writel" <bsp-dir>
rg -n "TODO|FIXME|HACK|workaround|WA" <bsp-dir>
git log --oneline -- <target-path>
```

## Evidence Template
```md
- Scope:
- Code Entry Points:
- Hardware References:
- Call Flow:
- Patch History:
- Findings:
  - confidence: high|medium|low
    evidence:
    risk:
    verification:
- Gate Result: pass|needs-fix
```

## Quality Gate
- 每条硬件相关结论都有代码位置、日志片段或 datasheet 章节支撑。
- 所有低置信度结论都有下一步验证方法。
- 输出必须包含 `pass` 或 `needs-fix`，且 `needs-fix` 绑定阻塞原因。
- 不得把经验判断写成已确认事实。
