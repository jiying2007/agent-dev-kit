# Requirements: Native Target Conformance Receipt V1

## 目标

把 target 的 `runtime/conformance-certified` 声明绑定到可机器验证的原生运行 receipt，禁止普通 Markdown、任意文件 hash、未来时间或单次输出冒充 discovery/load/trigger 全链路证据。

## 范围

- `manifests/target-contract.schema.json` 与 target contract loader。
- `schemas/native-target-conformance-receipt-v1.schema.json`。
- target contract 定向正负测试。
- Claude Code 原生 conformance 的隔离执行方案与负结果。

## 强制要求

1. Runtime conformance 必须引用 `adk-native-target-conformance-receipt/v1` JSON；loader 校验 receipt 路径、文件 hash、schema 和 identity。
2. Receipt 必须绑定 target、runtime binary + binary digest、exact version pin、bundle digest 和 normalized contract digest。
3. Discovery、load、trigger 必须是三个有序、独立 stage；每 stage 记录独立 command/result digest、exit code、开始/结束/时长、environment、privacy 和 authority。
4. 每 stage 只能使用与 stage 同名的 authority scope；authority attestation 由 canonical body 重算。
5. Loader 拒绝未来时间、阶段重叠、时长不一致、重复 command/result digest、bundle/contract/runtime identity 不一致，以及 receipt 与 contract `last_verified_at` 不一致。
6. Contract digest 只归一化 receipt 回填字段 `evidence` 与 `last_verified_at`，避免自引用循环；其余 runtime、adapter 与 target 事实全部参与摘要。
7. 当前 claude-code、opencode、hermes-agent 继续保持 `static/not-certified/not-run`，只有三个 stage 全部产生合格 receipt 才能提升。
8. Adapter 必须声明 `conformance_trust_policy`；当前 target 固定为 `enabled=false`、空 trusted authorities、`verification_backend=not-configured`。
9. Receipt 内自算 SHA-256 只证明结构完整性，不构成身份或来源信任。Production loader 没有外部 signature/CI provenance verifier 注入时必须拒绝 runtime promotion。

## 验收

- README + matching hash、missing path、wrong hash/runtime/contract、future receipt、stage evidence reuse 全部失败。
- 严格 fixture receipt 通过 schema 与 loader。
- 全部随机 digest 且 authority self-hash 自洽的 synthetic receipt，在无 trust verifier 时仍被拒绝。
- `tests/test_target_contracts.sh` fresh 通过。
