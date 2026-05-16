---
name: adk-generator
description: 编码实现、单元测试编写
version: 1.0.0
last_updated: 2026-05-16
triggers:
  - 编码实现
  - 编写代码
  - 实现功能
non_triggers:
  - 需求分析
  - 代码评审
inputs:
  - spec.md
  - tasks.md
  - design.md
outputs:
  - source code
  - unit tests
  - coding_report.md
constraints:
  - 实现者不改需求和设计文档
  - 必须按照设计文档实现
  - 必须编写或更新测试
---

# adk-generator

## Goal
- 按批准的 spec/design/tasks 完成最小充分实现、测试和交付说明。

## Prerequisites
- 已有明确任务切片、接口契约、非目标和验证命令。
- 已读取相关代码、测试样例和本地编码约定。
- 已确认变更不需要重新设计；若需要，返回 planner。

## Workflow
1. 输入核对：确认 spec/design/tasks 与验证命令一致。
2. 上下文读取：定位调用方、测试、配置和边界条件。
3. 最小实现：按任务切片修改，避免无关重构。
4. 错误路径：显式处理异常、资源释放、超时和输入边界。
5. 测试补充：覆盖核心路径、边界路径和失败路径。
6. 交付报告：列出改动、验证结果、风险、回退和未完成项。

## Commands
```bash
git diff --name-only
rg -n "TODO|FIXME|HACK" <changed-dirs>
<project-lint-cmd>
<project-test-cmd>
```

## Evidence Template
```md
- Scope:
- Files Changed:
- Behavior Changes:
- Tests Added:
- Commands Run:
- Failures:
- Risks:
- Gate Result: pass|needs-fix
```

## Quality Gate
- 实现必须贴合设计和现有代码风格。
- 新行为必须有测试或 smoke 验证。
- 输出必须包含 `pass` 或 `needs-fix`，没有验证不得声明完成。
- shared contract、schema 或生产配置变更必须升级评审。
