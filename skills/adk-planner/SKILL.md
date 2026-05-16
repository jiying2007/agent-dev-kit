---
name: adk-planner
description: 需求分析、任务拆解、方案设计
version: 1.0.0
last_updated: 2026-05-16
triggers:
  - 需求分析
  - 任务拆解
  - 方案设计
non_triggers:
  - 编码实现
  - 代码评审
inputs:
  - 用户需求
  - 问题描述
  - 技术约束
outputs:
  - spec.md
  - tasks.md
  - design.md
constraints:
  - 设计者不写实现代码
  - 必须澄清需求后再设计
  - 方案必须经过评审
---

# adk-planner

## Goal
- 将模糊需求转换为可执行、可验证、可交接的 spec、design 和 tasks。

## Prerequisites
- 已获得用户目标、约束、影响范围和验收方向。
- 已读取相关代码、文档、历史决策或运行门禁。
- 已明确本次任务是否涉及 shared contract、生产链路或跨仓库交接。

## Workflow
1. 澄清目标：拆出目标、非目标、用户价值和成功标准。
2. 收集上下文：定位相关代码、测试、文档、风险和历史决策。
3. 方案对比：给出候选方案、成本、风险、兼容性和推荐路径。
4. 任务拆解：按依赖关系和验证边界拆成可独立完成的切片。
5. 验证规划：为每个切片绑定 lint/test/build/smoke 或人工验收。
6. 交接输出：列出 owner、输入、输出、阻塞项、回退和完成门禁。

## Commands
```bash
rg -n "TODO|FIXME|HACK|deprecated|legacy" <target-dir>
rg -n "<关键接口或模块名>" <repo>
<project-test-cmd> --help
```

## Evidence Template
```md
- Goal:
- Non-goals:
- Scope:
- Options:
- Recommended Design:
- Task Slices:
- Verification Plan:
- Risks:
- Gate Result: pass|needs-fix
```

## Quality Gate
- 验收标准可观察、可复现、可判断。
- 每个任务切片都有输入、输出、依赖和验证方式。
- 输出必须包含 `pass` 或 `needs-fix`，需求缺口不得被隐藏。
- 涉及 shared contract 或生产链路时必须升级评审门禁。
