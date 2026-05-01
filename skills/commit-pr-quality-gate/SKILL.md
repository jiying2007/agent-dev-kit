---
name: commit-pr-quality-gate
description: 提交与 PR 质量门禁检查
triggers:
  - 准备 commit/PR 或代码评审前
  - 需要声明“可合并/可交付”前
non_triggers:
  - 纯探索性代码阅读
inputs:
  - 改动集合、验证结果、评审记录
outputs:
  - 分级门禁结论（pass/needs-fix）与整改项
constraints:
  - 没有验证证据不得给通过结论
  - blocker 或 major 未闭环不得给 pass
  - 问题陈述不清或单次改动包含多个不相关问题时不得放行
---

# commit-pr-quality-gate

## Goal
- 在提交与合并前做统一门禁裁决，确保“结论与证据一致”。

## Prerequisites
- 汇总改动范围、验证命令结果、评审分级信息。
- 明确本次改动是否涉及 breaking change 与迁移影响。

## Workflow
1. 真实性核验：确认问题可复现，证据与改动目标一一对应。
2. 范围核验：确认单次改动是否聚焦一个问题，避免捆绑无关变更。
3. 证据核验：逐项核对 lint/test/build/smoke 命令与执行结果。
4. 分级评审：按 blocker/major/minor 输出问题清单与闭环状态。
5. 兼容性核验：显式声明 breaking change、迁移与回退路径。
6. Core/Optional 核验：确认能力归属是否应进 core，场景化能力应进入 optional。

## Commands
```bash
git diff --stat <base>...HEAD
<project-lint-cmd> && <project-test-cmd>
```

## Evidence Template
```md
- Scope Check:
- Verification Commands + Results:
- Review Findings (B/M/m):
- Breaking Change Decision:
- Core/Optional Decision:
- Final Gate Result:
```

## Failure Handling
- 任一 blocker 未闭环，直接输出 `needs-fix` 并阻断合并。
- 若证据缺失或命令不可复现，退回补证，不得先给通过结论。

## Quality Gate
- 输出必须可执行、可验证、可追溯。
- 结论必须与分级统计一致，且可复核。
- 若存在“多问题捆绑”或“证据缺失”，结论必须为 `needs-fix`。
