# 需求：privacy-ref-hardening-v1

## 目标

- Evidence Graph、Trace Summary 和 Agent Value receipt 共用同一 identifier、opaque ref、SHA-256 和 secret taxonomy。
- 所有 evidence reference 使用 `ref:<sha256>`，不得保存自由文本、原始 prompt、工具 payload 或凭证。
- Evidence Graph 的节点摘要必须绑定存在的受限路径、真实文件哈希和 typed evidence ref。

## 验收

- `ghp_`、`github_pat_`、`sk-`、Bearer、AWS access key、private key、raw prompt 和 tool payload 在三条链路均 fail-closed。
- Graph 拒绝未来 generated/verified 时间、verified 晚于 expires、非法 retention 与缺失 lifecycle edge。
- release-evidence pass 必须由真实 evidence 文件支持的完整 source-to-release path 证明。
- Trace emitter 保持 `not-available`；Agent Value emitter 保持 `not-measured`。

> 后续状态说明（2026-08-30）：本条冻结的是本 change 当时不得虚报 emitter 的阶段边界。
> `trace-summary-contract-v2` 后续增加了 explicit-call library emitter；`agent-value-lifecycle-v1` 后续增加了
> receipt-driven measurement API，但 canonical runtime integration/usage 仍未启用。后续能力不削弱本 change 的
> opaque ref、secret taxonomy 或 raw-content 禁止规则。

## 非目标

- 不启用 runtime emitter，不生成 field evidence，不修改 routing/Profile/Workflow/Runtime Control/target 或主 manifest。
