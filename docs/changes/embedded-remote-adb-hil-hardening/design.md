# Embedded Remote ADB/HIL Hardening Design

## Design

远程会话采用单向状态机：

```text
DISCOVER -> READONLY_PREFLIGHT -> ARTIFACT_GATE -> AUTHORIZED_MUTATION
 -> SINGLE_SMOKE -> SHORT_CYCLE -> LONG_STRESS -> RESTORE -> ARCHIVE

any connectivity loss -> UNREACHABLE -> stop writes -> external recovery
 -> READONLY_PREFLIGHT
```

每一阶段只有一个 primary skill。`adk-embedded-remote-debug-log-triage` 负责发现、只读 preflight 和失联判断；artifact、diagnostic harness、test strategy、systematic debugging、verification/release 分别在对应阶段接管。

## Health Layers

1. host route/network hint；
2. transport（ADB/SSH/serial/GDB remote）；
3. remote shell/heartbeat；
4. app/diag。

四层独立计时和判定。网络提示不能短路 transport；transport 存在不能替代 shell/app 证据。

## Mutation Gate

任何 push、kill、restart、remount、覆盖、rollback、flash/OTA 都要求：

- 明确授权；
- artifact identity；
- before evidence；
- backup/rollback anchor；
- bounded timeout/retry；
- postcondition；
- restore plan。

## HIL Expansion

single smoke 通过后才允许 5～10 次短循环；短循环无 fatal signal、泄漏和身份漂移后才允许长循环/soak。失联、core、fatal log、恢复失败立即停止。

## Evidence

保留脱敏 manifest、原始证据路径/哈希、逐层结果、时延、身份、gate、residual risk。端点、凭证、raw log/core/binary 不进入长期正文。
