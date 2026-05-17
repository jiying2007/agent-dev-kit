---
name: adk-intake-workflow
description: 子仓接入工作流——扫描、分析、决策与治理覆盖
version: 1.0.0
last_updated: 2026-05-08
triggers:
  - "接入新仓库"
  - "新增子仓"
  - "onboard"
  - "add repo"
  - "纳入治理"
non_triggers:
  - 已接入子仓的日常同步（使用 sync-subrepos.sh）
  - 纯代码阅读或探索
inputs:
  - 仓库 URL 或本地路径、预期定位、优先级
outputs:
  - 仓库分析报告（结构/优点/缺点/adk 借鉴点）
  - 接入决策（adopt / watch / reject）
  - registry.csv 更新、adoption-matrix.md 更新
constraints:
  - 未完成深度分析不得标记为 adopted
  - 优点/缺点必须有具体证据支撑
  - 接入决策必须更新 registry.csv 和 adoption-matrix.md
---

# adk-intake-workflow

## Goal

## Prerequisites

- 理解相关领域的基本概念
- 熟悉项目结构和工作流程
- 具备基本的文档编写能力


为新增参考子仓提供标准化的"扫描→分析→决策→治理覆盖"工作流，确保每个接入的仓库都经过结构化评估，避免"盲目纳入"或"遗漏高价值仓库"。


## Workflow

1. 扫描候选仓库（GitHub trending / 社区推荐 / 自动发现）
2. 5 分钟快筛（README / LICENSE / 目录结构 / 活跃度）
3. 深度分析（四阶段 Prompt 逆向 + 八阶段 Skill 拆解）
4. 提炼优点/缺点（需有具体证据支撑）
5. 接入决策（adopt / watch / reject）
6. 治理覆盖（更新 registry.csv + adoption-matrix.md）
7. 压实验证（adk 本地验证通过后才标记 adopted）


## Quality Gate

1. 未完成深度分析不得标记为 adopted
2. 优点/缺点必须有具体证据支撑
3. 接入决策必须更新 registry.csv 和 adoption-matrix.md
4. watch 类仓库必须设定复查周期
5. reject 决策必须记录具体原因


## Evidence Template

```md
status: pass | needs-fix | BLOCKED
commands:
- <command + exit code>
evidence:
- <path or output summary>
risks:
- <remaining risk or none>
```

## References
- 详细背景、命令、模板、示例和扩展检查项保存在 `references/details.md`。
- 入口文件只保留触发和执行所需的最小上下文，避免默认加载过多 token。
