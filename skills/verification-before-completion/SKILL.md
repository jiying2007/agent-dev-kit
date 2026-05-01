---
name: verification-before-completion
description: 完成前验证门禁，确保交付声明与证据一致
triggers:
  - 准备声明完成并发起PR前
  - 准备声明完成、准备提交 commit 或发起 PR 前
  - 需要给出可合并/可发布结论时
non_triggers:
  - 仅做方案讨论且尚未产生实现改动
  - 纯背景知识问答
inputs:
  - 改动清单、测试结果、评审结论、风险与回退信息
outputs:
  - 完成前核对清单、门禁结论、未闭环项与处理建议
constraints:
  - 没有验证证据不得给出完成或通过结论
  - 评审 blocker 未关闭时不得给通过结论
  - breaking change 必须显式声明与迁移/回退方案
---

# verification-before-completion

## Goal
- 在交付前统一核对验证证据、评审状态和风险闭环，避免“未验先结论”。

## Prerequisites
- 已整理改动文件清单与影响范围。
- 已收集 lint/test/build/smoke 与评审状态证据。

## Workflow
1. 收敛改动范围：确认本次改动边界、影响面与非目标。
2. 证据核验：核对 lint/test/build/smoke 等结果与执行环境。
3. 评审闭环：按 blocker/major/minor 分级，检查必须项是否关闭。
4. 兼容性检查：显式判断是否存在 breaking change，并给出迁移与回退方案。
5. 反向核验：逐条检查“结论是否被证据支持”，避免先给结论后补证据。
6. 结论输出：给出 pass/needs-fix，并列出下一步动作与责任人。

## Commands
```bash
git diff --name-only <base>...HEAD
<project-lint-cmd> && <project-test-cmd> && <project-build-cmd>
```

## Evidence Template
```md
- Scope Summary:
- Verification Command Results:
- Review Status (B/M/m):
- Breaking Change Decision:
- Risk + Rollback:
- Final Gate Result:
```

## Failure Handling
- 关键命令无法执行时，必须说明原因并降级完成度表述。
- 若 blocker 未闭环，结论固定为 `needs-fix`，不得放行。

## Quality Gate
- 输出必须包含验证命令、关键结果、风险项和处理状态。
- 若存在未闭环 blocker，结论必须为 `needs-fix`。
- 完成声明需与实际证据逐项可追溯。
- 禁止使用“应该可以/理论上通过”等无证据措辞。
