# 自审报告：adk-v3-1-rc2-target-conformance

- 时间：2026-07-14T01:06:14Z
- 范围：TargetContract/adapter、export/install transaction、Schema/version、eval/performance、CI/security/release、文档与根仓治理声明。
- 结果：本地实现与提交质量门禁 `pass`；target stable promotion、remote release evidence 与 M4/M5 certification `blocked`。

## Findings

| Severity | Finding | Disposition |
|---|---|---|
| blocker | 三个 direct target 缺少真实 discovery/load/trigger/permission runtime evidence | 保持 `experimental`，不得提升 stable/M4 evidence |
| blocker | remote CI/Scorecard/attestation、双 runtime、第二操作者、30 天 field evidence 未执行 | 保持总体 M3 release candidate |
| major | 无本地未闭环 major | — |
| minor | 无影响交付的未闭环 minor | — |

## 自审重点

- 路径安全：destination containment、support-file symlink、plan tamper/expiry、active receipt drift、cross-target receipt、atomic replace/recovery 均有负例。
- 契约一致性：export/install 使用同一 renderer，target-specific 逻辑集中在 versioned contracts。
- 兼容性：有意破坏旧 direct tree 与 plan v1；receipt v1/v2 只保留 rollback，迁移演练验证从 rc.1 artifact 重装恢复。
- 证据诚实性：static、source/test、integration、runtime、field 分层；`not-run` 不计 pass，root lock failure 不被绕过。
- 平台中立：Claude/OpenCode/Hermes SDK 均未进入 core；外部官方资料仅作 provenance，`runtime_enablement: false`。

该自审不替代独立 reviewer 或第二操作者门禁；它仅用于本次本地实现收口。

2026-07-14，用户已明确授权执行检查、commit、push 和声明式 apply。该授权解除源码交付与 `~/codex -> ~/.codex` owner gate，但不等于 direct target runtime 认证、GitHub 远端工作流通过或 M4/M5 promotion 签署。
