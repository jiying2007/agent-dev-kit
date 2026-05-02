---
name: artifact-gated-lite
description: 高风险变更时使用轻量 artifact 标签与门禁模板固定交付证据
triggers:
  - 涉及公共接口、schema、发布链路等高风险变更
  - 需要跨角色交接且必须保留可追溯产物
non_triggers:
  - 单文件低风险修复且无需跨团队交接
inputs:
  - 需求说明、实现范围、验证命令
outputs:
  - 标签化交付块、评审结论、测试结论
constraints:
  - 必须包含 artifact 标签和 status 字段
  - 缺少验证证据时必须输出 BLOCKED 或 needs-fix
---

# artifact-gated-lite

## Goal
- 用最小标签集合统一跨角色交付物，避免“结论存在但证据缺失”。

## Prerequisites
- 已有明确的变更范围、影响面和验收方式。
- 已准备至少一条可执行验证命令。

## Workflow
1. 选择最小 artifact 集合：`ImplementationPlan`、`ReviewReport`、`TestReport`。
2. 每个 artifact 必须写清 `status`、`owner`、`scope`、`inputs`、`handoff_to`。
3. 执行验证命令并记录真实结果，禁止补写或猜测。
4. 形成最终门禁结论：`pass` 或 `needs-fix`。

## Commands
```bash
rg -n "ImplementationPlan|ReviewReport|TestReport" docs/changes/<change-id>/
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## Evidence Template
```md
[artifact:ImplementationPlan]
status: READY
owner: <agent>
scope:
- <实现范围>
inputs:
- <上游输入>
handoff_to:
- <next-owner>

[artifact:ReviewReport]
status: PASS
owner: <reviewer>
verdict: pass | needs-fix
findings:
- [severity:high] <问题或 None>

[artifact:TestReport]
status: PASS
owner: <tester>
tests_run:
- <命令与结果>
```

## Failure Handling
- 任一 artifact 缺少 `status` 或验证证据时，结论固定为 `needs-fix`。
- 若发现共享契约变更未标注影响面，立即升级到架构评审。

## Quality Gate
- 三类 artifact 均存在且字段完整。
- `ReviewReport` 与 `TestReport` 的结论一致，不允许相互矛盾。
- 所有验证命令可复现，失败项必须列出修复责任人。

