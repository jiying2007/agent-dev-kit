# 需求基线：runtime-profile-health-and-compat-cleanup-v1

## 目标

- 让 Codex live health 按 `~/.codex/control/state/active-profile.env` 对应的受管清单核验，不再用默认 build 误判已受管的 `team-collab` 资产。
- 彻底移除 Superpowers 作为 Codex 运行时 profile、workflow、fallback 或 vendor plugin 的来源资产；保留只读参考仓 provenance。
- 将 root 的 ADK lock、运行态证据和状态报告绑定到当前 clean source snapshot；证据过期或 live health 失败时不得继续宣称当前已验证。

## 非目标

- 不直接修改或递归删除 `~/.codex`。
- 不覆盖既有 `agent-dev-kit` 生命周期契约变更、参考子仓 dirty 内容或历史报告。
- 不启用新的 runtime target，也不自动提交、推送、合并或发布。

## 验收标准

1. 运行态健康检查能够证明 live managed-files 的 profile 与 active-profile 一致，并不会把同一受管清单中的 `team-collab` assets 判为 unmanaged。
2. 任意不在 live managed-files 清单中的 direct 或 vendor skill 仍被判为 unmanaged；Superpowers plugin 路径仍是硬失败。
3. Codex source 不再导出 `vendor/plugins/superpowers`，新 plan 将其显示为可审查的删除项。
4. root lock 只在 ADK 当前工作树完成 clean commit 后同步；本轮不伪造 release identity。
5. runtime health / footprint 失败时，current-status 的 live refresh 结论降级为 stale 或 needs-fix。

## 风险与停止条件

- source-to-live 的 delete 只可经 plan、dry-run、明确审批和 rollback anchor 执行。
- 若 profile 清单与 active-profile 不匹配，或两次同类验证失败没有新根因，停止 apply 并 replan。
- `agent-dev-kit` 现有未提交文件属于其他生命周期任务，禁止修改。
