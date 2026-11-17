# 需求：拒绝已消费的 Goal 重规划凭据重放

## 问题与范围

独立复核在 11.3.15 `5f113b8f5ae6f83662d41d99d0907026f4e44c9d` 复现：readonly replan A → implementation replan B → 将旧 A 装入新 event_id，现有 reducer 再次接纳并递增 intake_revision。只比较当前 attestation 无法证明凭据尚未消费。本变更修复同一 logical Goal 的历史消费检测，不新增宿主、adapter 或权威状态。

## 验收

- REQ-001 / ACC-001：已消费的历史 intake attestation 即使换外层 event_id，也不能再次改变该 Goal 的 canonical 状态；拒绝不依赖 verifier。原始冻结 A→B→A 反例修复前失败、修复后拒绝。
- REQ-002 / ACC-002：真正全新且有效的 replan 仍可接纳；同 event_id 同 payload 幂等、冲突 payload 拒绝、错 Goal/错摘要拒绝及无 verifier 的保守 implementation floor 均保持。
- REQ-003 / ACC-003：在既有摘要一致 synthetic native receipt 上，trust verifier 明确拒绝、抛异常、返回 truthy 非 True 均不能取得信任；生产实现若已正确则只补窄测试。
- REQ-004 / ACC-004：独立 reviewer 原样复跑冻结反例、核对全新 replan 控制，并核验完整安全回归和当前源码 Spec/Quality；原始 RED 不覆盖。

## 证据限定

复现使用既有 synthetic unit-test managed verifier。默认无 verifier 路径仍保持 implementation floor，不能据此声称真实宿主权限被绕过。真实外部副作用去重、来源身份准入、旧租约和 crash/ACK 对账由实际宿主验证，本变更不赋予 native certification。

## 原始冻结输入

独立反例目录为 `/workspace/scratch/d417066aafa8/independent-review/c2-attestation-replay/`。`frozen-inputs.json` SHA-256 为 `1bddace1b0edebc3475f8e51f1cd0d9a4878c5e9f0c4b17d6d2bf001a2779d60`，`replay_frozen_probe.py` 为 `b6f5a02415a3310e12fc554f8d166767bf585709b1469c5bd1ecbe10f8ebfa7d`。复审须原样保留 before、输入和 verifier，候选结果另存。

同字节归档位于本 change 的 `evidence/original-counterexample/`；保留原始来源路径和时间，归档不改写历史结果。
