---
name: adk-pilot-framework
description: 跨仓库 Pilot 试跑框架——场景定义、证据收集与门禁验收
version: 1.0.0
last_updated: 2026-05-08
triggers:
  - "试跑"
  - "pilot"
  - "真实场景验证"
  - "运行目录验证"
  - "codex 试跑"
non_triggers:
  - 纯本地单元测试（无需运行目录验证）
  - 文档编写或方案讨论
inputs:
  - 待验证能力清单、目标运行目录、场景定义、预期行为
outputs:
  - 试跑报告（场景+证据+结论）
  - 门禁验收结果（pilot-pass / pilot-fail）
  - 回灌建议（采纳/改进/淘汰）
constraints:
  - 无真实运行证据不得声明 pilot 通过
  - 门禁三联证据必须全部 PASS（health-check / global-health / pilot-gate）
  - 失败项必须记录根因并转入调试流程
---

# adk-pilot-framework

## Goal

## Prerequisites

- 理解相关领域的基本概念
- 熟悉项目结构和工作流程
- 具备基本的文档编写能力


在将 adk 资产正式发布前，通过结构化的"场景→试跑→证据→门禁→回灌"闭环，在真实运行目录中验证能力有效性，避免"本地通过但实战失败"。


## Workflow

1. 定义试跑场景（目标运行目录、预期行为、验收标准）
2. 准备试跑环境（隔离配置、基线快照）
3. 执行试跑（运行能力、收集证据）
4. 门禁验收（health-check / global-health / pilot-gate 三联）
5. 记录结果（pass/fail + 根因 + 负结果留痕）
6. 回灌建议（采纳/改进/淘汰 → 更新 adoption-matrix.md）


## Quality Gate

1. 无真实运行证据不得声明 pilot 通过
2. 门禁三联证据必须全部 PASS（health-check / global-health / pilot-gate）
3. 失败项必须记录根因并转入调试流程
4. 负结果必须留痕（negative-results.md）
5. 回灌建议必须有具体证据支撑


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
