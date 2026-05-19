# Pilot: embedded-verification-completion

status: evidence-ready

## 目标场景

嵌入式全栈任务准备声明完成前，必须把 scope、验证命令、负路径、运行态配置、breaking change、风险回滚和最终门禁结论统一核对，避免只凭局部脚本成功就声称完成。

## 预期路由

- primary: `adk-verification-before-completion`
- supporting: `adk-commit-pr-quality-gate`, `adk-release-versioning`
- fallback: 仅当用户显式要求对照 Superpowers completion 流程时使用

## 验证证据

### 原始任务输入

用户要求把 adk 推进到可替代 Superpowers 的生产门禁状态。该 pilot 聚焦完成前证据闭环，不声明任何真实硬件已经 production-ready。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot verification --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `scope-summary.md` | 完成声明的目标范围和非目标 |
| `verification-index.md` | 命令级验证证据索引 |
| `negative-results.md` | 不能放行的负路径 |
| `runtime-config-audit.md` | `~/codex -> ~/.codex` 运行态声明要求 |
| `breaking-change.md` | breaking change、迁移和回滚判断 |
| `final-gate.md` | 最终门禁结论和残留风险 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot verification --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成完成前验证 scope、命令证据、负路径、运行态配置、breaking change 和最终门禁记录 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-verification-completion/evidence.md` |

### 残留缺口

- 该 pilot 证明 completion gate 行为，不替代真实硬件 HIL、OTA rollback 或现场维护证据。
- 涉及 `~/.codex` 生产可用性声明时，仍必须附 `~/codex` build/apply 和 global health 证据。
