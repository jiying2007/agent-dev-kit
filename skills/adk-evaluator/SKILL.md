---
name: adk-evaluator
description: 代码评审、质量验证
version: 1.0.0
last_updated: 2026-05-16
triggers:
  - 代码评审
  - 质量验证
  - 代码检查
non_triggers:
  - 编码实现
  - 需求分析
inputs:
  - source code
  - coding_report.md
  - unit tests
outputs:
  - code_review.md
  - verification_report.md
constraints:
  - 审查者不修代码
  - 只产报告和修复 task
  - 必须检查代码质量
---

# adk-evaluator

## Goal
- 审查实现质量、验证证据和风险闭环，判断变更是否可以放行。

## Prerequisites
- 已获得 diff、实现报告、测试结果、设计文档和风险说明。
- 已明确变更范围、非目标和应运行的验证命令。
- 已确认本次审查是只读评估，不直接修复代码。

## Workflow
1. 范围核对：确认 diff、目标、非目标和影响面。
2. 证据核验：检查 lint/test/build/smoke 是否覆盖主要风险。
3. 代码审查：按行为、错误路径、并发、安全、兼容和可维护性检查。
4. 文档一致性：核对 README/runbook/manifest 与脚本行为。
5. 风险分级：按 blocker/major/minor/info 输出 findings。
6. 放行判断：给出 `pass` 或 `needs-fix`，并列出残留风险。

## Commands
```bash
git diff --stat
git diff --name-only
<changed-test-cmd>
bash scripts/devkit.sh runtime-boundary
```

## Evidence Template
```md
- Review Scope:
- Findings:
  - severity:
    location:
    issue:
    impact:
    recommendation:
- Verification Evidence:
- Residual Risks:
- Gate Result: pass|needs-fix
```

## Quality Gate
- blocker 或关键验证缺失时，结论必须是 `needs-fix`。
- findings 必须有位置、影响和建议。
- 输出必须包含 `pass` 或 `needs-fix`，不得只给模糊评价。
- 没有问题时也要说明剩余测试缺口或风险。
