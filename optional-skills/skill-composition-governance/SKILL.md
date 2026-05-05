---
name: skill-composition-governance
description: 治理技能组合、触发优先级、fallback 与弃用关系
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "技能组合"
  - "触发冲突"
  - "技能治理"
non_triggers:
  - 单个 skill 文案微调且不影响触发规则
  - 仅安装已有 profile 且不改变组合关系
inputs:
  - skill 清单、触发词、non_trigger、profile、候选任务场景
outputs:
  - 主技能、辅助技能、fallback、互斥关系和弃用决策
constraints:
  - 一个场景只能有一个主技能
  - 辅助技能不得抢占主技能触发
---

# skill-composition-governance

## Goal
- 用小技能组合提高覆盖面，同时避免 `~/.codex` 中触发噪音和职责重叠。

## Prerequisites
- 已列出涉及的 skill、optional skill 和目标 profile。
- 已有至少一条代表性任务输入。

## Workflow
1. 确定主技能：每个场景选择一个 primary skill。
2. 标注辅助技能：supporting skills 只作为建议，不直接抢占入口。
3. 定义 fallback：主技能不适用时，给出明确后备 skill。
4. 定义互斥关系：职责冲突或触发重叠时，明确优先级。
5. 弃用治理：旧技能需给 `deprecated_by` 或 `replaced_by`。
6. 回归样例：为每个组合场景补触发测试。

## Commands
```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill <skill> --text "<task text>"
bash ../scripts/check-runtime-routing.sh ..
```

## Evidence Template
```md
- Scenario:
- Primary Skill:
- Supporting Skills:
- Fallback Skill:
- Mutually Exclusive Skills:
- Deprecated/Replaced Decision:
- Trigger Regression:
```

## Failure Handling
- 若一个场景出现多个主技能，结论固定为 `needs-fix`。
- 若 fallback 不可安装或不在 profile 中，退回 profile 设计。

## Quality Gate
- 组合规则必须能被脚本检查。
- 触发样例必须覆盖正例、反例和 fallback。
