---
name: planning-execution-loop
description: 长任务计划审查、分阶段执行、恢复与收口闭环
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "执行计划"
  - "多阶段任务"
  - "计划审查"
non_triggers:
  - 单文件低风险修改
  - 仅做只读分析且无需执行计划
inputs:
  - 计划文件、任务边界、验证命令、阻塞条件、恢复上下文
outputs:
  - 执行检查点、恢复摘要、风险台账、完成前验证结论
constraints:
  - 每个阶段必须有明确完成标准和验证证据
  - 阻塞条件不清时不得继续执行
---

# planning-execution-loop

## Goal
- 把长任务从“靠会话记忆推进”改为可恢复、可验证、可审查的执行闭环。

## Prerequisites
- 已有需求或计划来源。
- 已明确任务边界、验证命令和停止条件。

## Workflow
1. 计划审查：检查依赖顺序、验证命令、隐含环境假设和阻塞条件。
2. 任务切片：每个阶段输出目标、scope、done criteria、验证命令。
3. 执行检查点：每完成一个阶段，更新状态、证据和风险。
4. 恢复记录：维护 `session-state`、`next-actions`、`risk-ledger`、`resume-prompt`。
5. 偏离处理：发现计划错误、共享契约冲突或验证失败时，暂停并回到计划审查。
6. 收口验证：进入完成声明前，执行 completion gate 并核对证据支持结论。

## Commands
```bash
bash scripts/devkit.sh propose --change <change-id> --title "<目标>"
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## Evidence Template
```md
- Plan Review:
- Stage Checklist:
- Session State:
- Next Actions:
- Risk Ledger:
- Resume Prompt:
- Verification Evidence:
- Final Gate:
```

## Failure Handling
- 同一验证失败两次仍无根因时，回到假设矩阵并更新风险台账。
- 缺少恢复摘要时，不得声明长任务可交接。

## Quality Gate
- 每个阶段必须有验证证据。
- 恢复摘要必须能让新会话继续执行。
- 完成结论必须经过 `verification-before-completion`。
