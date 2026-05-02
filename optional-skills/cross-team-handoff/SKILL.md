---
name: cross-team-handoff
description: 跨团队交接时统一目标、边界和验收责任
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 模块即将交接给其他团队维护
non_triggers:
  - 同团队内小范围任务流转
inputs:
  - 当前方案、风险列表、待办事项
outputs:
  - 交接清单、责任矩阵、验收计划
constraints:
  - 必须明确 owner、截止时间与验收条件
---

# cross-team-handoff

## Goal
- 在交接窗口内冻结边界、责任与验收口径，避免“交接后才发现缺口”。

## Prerequisites
- 已明确交接对象、窗口时间与系统边界。
- 已汇总当前版本、风险清单与未决事项。

## Workflow
1. 盘点范围内资产、接口和运行约束。
2. 输出责任矩阵（交接方/接收方/批准方）与关键时间点。
3. 切分 section ownership：每个模块/文档只允许一个主负责人，其他人只评审不并行改写。
4. 对未决风险给出处置策略：继续推进、延期、降级或冻结。
5. 约定验收证据、回退路径和升级通道，并形成签收记录。

## Commands
```bash
rg -n "@deprecated|TODO|FIXME|HACK" <module_path>
git diff --name-status <handoff-base>...HEAD
```

## Evidence Template
```md
- Scope and Exclusions:
- Owner Matrix (R/A/C):
- Section Ownership:
- Open Risks + Decisions:
- Acceptance Evidence:
- Rollback Path:
- Escalation Channel:
- Sign-off (handoff / receiver / approver):
```

## Failure Handling
- 若 owner 或验收条件未明确，结论必须为 `needs-fix`，禁止进入交接完成态。
- 若发现共享契约未冻结，必须升级到架构评审后再继续交接。

## Quality Gate
- 交接文档必须覆盖范围、风险、验收、回退与升级通道。
- 每个关键模块必须有唯一主负责人，禁止责任重叠。
