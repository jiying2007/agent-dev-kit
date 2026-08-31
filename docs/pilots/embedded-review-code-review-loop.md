# Pilot: embedded-review-code-review-loop

status: evidence-ready

## 目标场景

嵌入式变更完成后，独立审查 diff、验证证据和风险边界，并对 review 反馈做真实性核验与复审。

## 预期路由

- primary: `adk-code-review-loop`
- supporting: `adk-commit-pr-quality-gate`, `adk-verification-before-completion`
- internal fallback: 审查工具不可用时输出可转交的只读审查包

## 验证证据

### 原始任务输入

用户要求 ADK 原生覆盖 code review / receiving review 闭环，并让误报、越界建议和复审有可审计证据。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot review --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `review-scope.md` | 审查范围和非目标 |
| `review-report.md` | blocker/major/minor/question 分级 |
| `feedback-triage.md` | accepted、false_positive、out_of_scope |
| `rereview.md` | 修复后复审结论 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot review --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成 review scope、分级报告、反馈核验和复审通过证据 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-review-code-review-loop/evidence.md` |

### 残留缺口

- 仍需绑定真实 diff 和真实 reviewer 反馈。
- 远端 PR 工具和权限操作仍需人工确认。
