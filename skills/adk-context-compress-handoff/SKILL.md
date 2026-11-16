---
name: adk-context-compress-handoff
description: "用于长任务上下文压缩、跨会话恢复及交接时保存目标、证据指针和下一动作；不用于替代原始高风险证据或任务执行。"
version: 1.0.2
last_updated: 2026-11-16
triggers:
  - "上下文压缩"
  - "会话接力"
  - "恢复提示"
  - "压缩前处理"
  - "context preflight"
  - "resume prompt"
  - "90秒模板"
non_triggers:
  - "只做当前会话总结"
  - "只写日报"
  - "直接写长期 memory"
inputs:
  - 当前目标、已完成动作、证据路径、未决阻塞、风险、下一步、无效旧目标
outputs:
  - 恢复摘要、resume prompt、证据索引、下一步、excluded context 和 memory/archive 候选
constraints:
  - 不保存完整聊天记录或敏感原文
  - 不静默写入长期 memory
  - 压缩结果不能替代原始证据路径
---

# adk-context-compress-handoff

## Goal
生成可恢复、可审计的 handoff，排除过期目标、失败假设和敏感原文。

## Prerequisites
- 已知最新目标、验证状态、下一步及可回读证据。
- 已识别需排除的旧计划、错误事实与敏感内容。

## Workflow
1. 确认最新目标：记录 latest goal，列出 invalidated goals。
2. 分层压缩：stable、dynamic、evidence、excluded 分开写。
3. 连续性证明：默认使用下方模板记录 active plan/findings/progress/attestation；仅在 ADK 源码根已确认且文件可读时，可选根下 `templates/context/continuity-attestation.md`。
4. 证据索引：命令、路径、结果摘要和回退条件必须可追溯。
5. 风险与阻塞：列出 unresolved blockers、residual risks、manual approval points；handoff 不扩大权限。
6. 下一步：给出最多 3 个优先动作和第一条建议命令。
7. 记忆边界：长期规则只输出 candidate，不直接写 memory 或 AGENTS。
8. 恢复提示：生成新会话可直接粘贴的 resume prompt。

## Evidence Template
```md
- Latest Goal:
- Invalidated Goals:
- Stable Context:
- Confirmed Facts:
- State / Blockers:
- Scope / Permission:
- Evidence / Fallback:
- Continuity Attestation:
- Excluded Context:
- Next Actions:
- Resume Prompt:
- Memory Candidates:
- Archive Candidates:
- Gate Result: pass / needs-fix
```

## Quality Gate
- 必须包含 latest goal、next actions、raw evidence 和 fallback condition。
- excluded context 不得重新进入 active instructions。
- 不能把压缩摘要当成完成证据；必须保留原始路径或命令。
- 涉及长期提升时必须转交 memory/archive 治理。
