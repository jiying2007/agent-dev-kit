# Agent Dev Kit Harness Readiness Baseline

## 执行信息

- Command: `rtk agent-dev-kit/scripts/devkit.sh harness readiness --root agent-dev-kit --summary-json`
- Exit Code: 0（report-only）
- overall_status: `partial`
- counts: `pass=0, partial=6, needs-review=0, blocked=0, not-applicable=1`
- scan: `files_seen=597, truncated=false, errors=0`
- field_evidence_status: `not-verified`

## 已确认能力

- Spec/任务/验收工件、change state、runbooks、tests、CI、验证命令、backup/rollback 和 freshness checker 均可被机械发现。
- ADK 未配置目标仓 MCP，`tool_and_permission_boundary=not-applicable`；这不是缺陷，也不应为了分数接入 MCP。
- 没有 hardcoded secret、扫描截断或 blocked 维度。

## 真实 evidence gap

1. 根 `AGENTS.md` 为 270 行，超过 v1 合同的 180 行索引预算；需要另立变更把长生命周期说明下沉到 docs，而不是在本 change 中混改规则入口。
2. `.adk/harness-readiness.json` 尚未建立，六个适用维度没有显式 owner 与 `last_verified_at`。
3. 未发现 `CODEOWNERS/OWNERS`，freshness ownership 仍需人工识别。
4. 当前只有 source/test evidence，没有 30 天、多仓、多 operator 的 field evidence。

## 决策

- 本 change 不补造 owner、验证日期或现场证据，也不为取得 pass 扩大到 AGENTS 重构和仓库 ownership 治理。
- 后续试点先以此基线观察误报/漏报，再分别为 context compaction 与 ownership 建立独立 change。
