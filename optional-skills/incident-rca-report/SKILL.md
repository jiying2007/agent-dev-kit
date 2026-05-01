---
name: incident-rca-report
description: 线上事故复盘与根因分析闭环
triggers:
  - 出现线上故障且需要复盘闭环
non_triggers:
  - 本地开发阶段的临时报错
inputs:
  - 事故时间线、监控数据、变更记录
outputs:
  - RCA 报告、修复项、预防项
constraints:
  - 必须覆盖根因、触发条件、阻断措施
  - 结论必须区分事实证据与推断判断
---

# incident-rca-report

## Goal
- 用事实证据还原事故链路，给出可验证的修复与预防闭环。

## Prerequisites
- 具备统一时区的事故时间线与关键日志片段。
- 能获取对应发布记录、配置变更与监控告警数据。

## Workflow
1. 还原时间线：按分钟级记录发现、止损、恢复与复发节点。
2. 分层证据：将“事实证据”与“推断判断”分离，并记录被证伪假设。
3. 根因收敛：输出触发条件、放大路径、失效防线三段因果链。
4. 动作闭环：按 blocker/major/minor 分级生成修复与预防项。
5. 追踪计划：每个动作必须绑定 owner、截止时间、验收命令。

## Commands
```bash
git log --since "<incident-start>" --until "<incident-end>" --oneline
rg -n "error|fatal|timeout|oom" <log_dir>
```

## Evidence Template
```md
- Timeline (UTC+8):
- Impact Scope:
- Fact Evidence:
- Ruled-out Hypotheses:
- Root Cause Chain:
- Actions (B/M/m + owner + due):
- Verification Command Results:
```

## Failure Handling
- 关键证据缺失时，结论固定为 `needs-fix`，先补采样与日志再继续。
- 若修复涉及 breaking change，必须在报告中附迁移窗口与回退触发条件。

## Quality Gate
- RCA 必须包含责任边界、改进计划、验收标准与复验结果。
- 若涉及 breaking change，必须附迁移与回退路径。
