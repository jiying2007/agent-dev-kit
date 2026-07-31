# 设计：mcp-2026-final-metadata-refresh-2026-07-30

## 架构决策

复用 `skill_mcp_dependencies.json` 作为 MCP compatibility SSOT，复用
`external_agent_pattern_contracts.json` 保存来源/吸收 provenance，继续使用
`check-agent-ecosystem-standards.sh` 作为唯一 validator。不会新增 Skill、Workflow、manifest
或 runtime adapter。

## 状态模型

```text
final source retrieved = true
            |
candidate release_status = released
            |
active protocol = 2025-11-25
runtime / Tasks / Apps / extensions = false
final_compatibility_claim = false
            |
schema + client/server + auth + rollback evidence
            |
future independent activation decision（本 change 不包含）
```

`final_spec_retrieved=true` 只证明 final tag/release metadata 已取回。它不改变任何
`*_completed=false`，也不使 `activation_allowed` 变为 true。

## 数据设计

- source ID：`mcp-2026-07-28-final`
- candidate protocol：`2026-07-28`
- release status：`released`
- `feature_enablement`：
  - `tasks=false`
  - `apps=false`
  - `extensions=false`
- `compatibility_test=not-run-required-evidence-pending`
- `runtime_enabled=false`
- `final_compatibility_claim=false`
- activation gate：
  - `final_spec_retrieved=true`
  - 四项 required 保持 true
  - 四项 completed 固定 false
  - `activation_allowed=false`

## Checker 与测试

- manifest candidate 必须引用 final source，并包含 feature enablement。
- checker 必须分别验证 release fact、active protocol、feature/runtime disabled 和 activation
  blockers，禁止用一个 `released` 状态推导 compatibility。
- pass fixture 更新为 final metadata。
- 新增负 fixture：只要 Tasks、Apps 或 extensions 任一启用，即使 runtime 仍为 false 也必须失败。
- 保留 runtime-enabled 与 weak-auth 负例，证明旧安全边界没有放宽。

## 兼容性与维护成本

- 既有 JSON consumer 可忽略新增字段；严格 checker 会要求新字段，属于治理合同增强，不改变
  runtime API。
- 历史 archive 和 2026-07-23 adoption 记录保持不变；新决策以追加记录表达演进。
- source/freshness 以后按 expiry 复核；不依赖易变 main branch commit 作为 final identity。

## 风险与回退

- 风险：把 `released` 误读为 compatible。通过 `final_compatibility_claim=false`、
  `activation_allowed=false` 和未完成证据字段三重阻断。
- 风险：混合许可证被简化。source record 明确边界，本 change 不复制上游内容。
- 回退：恢复两个 manifest、checker/test/fixture 的 RC metadata；active/runtime 状态始终不变。
