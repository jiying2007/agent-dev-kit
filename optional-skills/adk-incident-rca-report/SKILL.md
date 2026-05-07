---
name: adk-incident-rca-report
description: 线上事故复盘与根因分析闭环
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "线上事故"
  - "故障复盘"
  - "RCA分析"
  - "根因分析"
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

# adk-incident-rca-report

## Goal
- 用事实证据还原事故链路，给出可验证的修复与预防闭环。
- 通过 5-Why 分析确保根因穿透到系统层面而非停留在表面症状。

## Prerequisites
- 具备统一时区的事故时间线与关键日志片段。
- 能获取对应发布记录、配置变更与监控告警数据。

## Workflow
1. 还原时间线：按分钟级记录发现、止损、恢复与复发节点。
2. 分层证据：将"事实证据"与"推断判断"分离，并记录被证伪假设。
3. 5-Why 根因分析：从表面症状逐层追问，直到到达系统性根因。
4. 根因收敛：输出触发条件、放大路径、失效防线三段因果链。
5. 动作闭环：按 blocker/major/minor 分级生成修复与预防项。
6. 追踪计划：每个动作必须绑定 owner、截止时间、验收命令。
7. 改进措施跟踪：建立改进项看板，定期回顾执行进度。

## 5-Why 分析模板
```md
[5-why-analysis]
问题: <表面症状>

Why-1: <直接原因>
  证据: <日志/监控数据>

Why-2: <中间原因>
  证据: <配置/代码变更>

Why-3: <流程原因>
  证据: <流程文档/操作记录>

Why-4: <组织原因>
  证据: <团队结构/职责分工>

Why-5: <系统性根因>
  证据: <架构/设计决策>

根因分类: 代码缺陷 | 配置错误 | 流程缺失 | 监控不足 | 架构缺陷
```

## 时间线重建模板
```md
[timeline]
时区: UTC+8

HH:MM - [触发] <触发事件描述>
HH:MM - [发现] <如何发现事故>
HH:MM - [止损] <采取的止损措施>
HH:MM - [恢复] <恢复操作>
HH:MM - [验证] <恢复验证>
HH:MM - [关闭] <事故关闭>

持续时间: <分钟>
影响范围: <用户数/请求量/服务数>
```

## Commands
```bash
# 查询事故期间的 Git 提交
git log --since "<incident-start>" --until "<incident-end>" --oneline

# 搜索错误日志
rg -n "error|fatal|timeout|oom" <log_dir>

# 查询配置变更历史
git log --all --oneline -- "*.yaml" "*.yml" "*.conf" --since "<incident-start>"

# 检查监控告警记录
rg -n "alert|warning|critical" <monitoring_log_dir>

# 统计影响范围
rg -c "error" <log_dir> | sort -t: -k2 -rn | head -20

# 生成 RCA 报告骨架
bash scripts/devkit.sh verify --change <incident-id>
```

## Evidence Template
```md
- Incident ID:
- Severity: P0 | P1 | P2 | P3
- Timeline (UTC+8):
- Impact Scope:
- 5-Why Analysis:
- Fact Evidence:
- Ruled-out Hypotheses:
- Root Cause Chain:
- Actions (B/M/m + owner + due):
- Verification Command Results:
- Prevention Measures:
- Monitoring Gaps:
```

## Failure Handling
- 关键证据缺失时，结论固定为 `needs-fix`，先补采样与日志再继续。
- 若修复涉及 breaking change，必须在报告中附迁移窗口与回退触发条件。
- 若根因无法收敛到单一原因，必须列出所有候选根因并标注概率。
- 若改进措施超过 30 天未完成，必须升级到管理层复审。

## Quality Gate
- RCA 必须包含责任边界、改进计划、验收标准与复验结果。
- 若涉及 breaking change，必须附迁移与回退路径。
- 5-Why 分析必须至少穿透到第 3 层，禁止停留在表面症状。
- 时间线必须覆盖从事发到恢复的完整链路，禁止遗漏关键节点。
- 改进措施必须绑定 owner 与截止时间，禁止无主改进项。
