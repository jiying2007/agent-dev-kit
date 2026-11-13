---
name: adk-branch-closeout
description: "用于代码与验证完成后的分支收口、PR 选择和保留或清理决策；不用于未验证时直接合并、删除用户工作树或替代评审。"
version: 1.1.0
last_updated: 2026-11-13
triggers:
  - "分支收尾"
  - "开发完成"
  - "创建 PR"
  - "合并分支"
  - "收尾"
  - "结束开发分支"
  - "branch closeout"
non_triggers:
  - 仍有测试失败且未定位根因
  - 只是询问 git 概念
  - 不做分支收尾
inputs:
  - 当前分支、基础分支、验证命令、测试结果、PR/合并目标
outputs:
  - 收尾选项、验证结论、合并或 PR 计划、清理决策与残留风险
constraints:
  - 测试或关键验证失败时不得进入合并或 PR
  - 丢弃工作必须要求明确确认
  - 不得自动删除用户未确认的分支或 worktree
---

# adk-branch-closeout

## Goal
只对已完成或要求检查的分支进行**最小必要收尾**。不强迫每次展示四种收尾选项，也不在未验证、未授权或 dirty 不明时合并/删除。

## Choose one operation
- **status-only**：只问收尾状态、CI 或下一步时，只读实际分支、PR、检查和阻塞；不自动修改、推送或创建额外 PR。
- **create-pr**：明确要求提交 PR 时，核 HEAD/diff、真实验证、review 责任与保护规则；不要求再逐项展示 local-merge / keep / discard。
- **merge**：已有 PR 需要合并时核精确 HEAD、必需 checks、权限和目标分支身份；合并后核 fresh-main CI。没有有效证据则 `blocked`。
- **keep / discard**：保持源资产默认不清理；discard 和 worktree/branch 删除必须明确同意和可核实的来源/dirty 状态。

## Workflow
1. 读取 `git status --short`、base/head/worktree 和可信 CI/PR 回执；用户原有 dirty 变化不得被覆盖。
2. 只针对请求的操作执行必要步骤；若测试失败、review blocker 未关闭或目标分支已变化，停止并给最小修复建议。
3. 合并/PR 操作使用宿主现有工具和独立授权，不能把计划视为批准。GitHub/SCM 工具不可用时交付可复制的 PR 草稿，不虚报创建成功。
4. 真正执行合并后在新主线再次验证受影响范围；状态更新需精确 commit/check 绑定。不能把功能分支通过当成 fresh-main 通过。
5. 清理需选择可验证的目标与实际来源，**只在 explicit destructive cleanup approval 后操作**；已发布但未确认可删的 worktree 默认保留。
6. 输出短报告：`operation / HEAD / evidence / result / blockers / remaining risk / next action`。完整分支生命周期选项按需见 `references/closeout-options.md`。

## Quality Gate
- 未关闭真实 blocker、缺验证或保护规则不满足时不得 PR/merge；未知写操作结果先核远端再重试。
- 不强制展示所有四个选项；真实 destructive 操作必须明确批准并保护用户改动。
- 真实合并后再次验证，未获得下游成功回执不宣称部署、发布或产品完成。
