# 设计说明：20261117-goal-replan-replay

## 架构影响

coordinator 冻结契约；audit_core 仅实现本 C2，不实现其设计过的 C1；independent_review 保留原始反例并只读复核。现有 reduce_events 对完整输入事件逐条归约，可在同一次归约维护已消费 attestation 集合。有效 goal 创建及 replan 的 attestation 进入集合；同 event_id 的既有幂等处理仍先执行；新 event_id 携带已消费 attestation 应明确拒绝。该集合仅服务确定性重放，不新增外部持久账本或返回 schema。

## 数据与配置影响

不改输入 schema、trusted verifier contract、policy/revision 或输出结构。实际实现先检索所有调用者与既有初始化、缺失 intake 兼容路径；无 intake 的历史兼容输入不虚构 attestation。新有效 replan 的验证仍沿用唯一 _validate_goal_intake。

## 兼容性与迁移方案

拒绝先前不正确接受的历史凭据重用；合法 replan 与 exact event replay 不变。回滚通过受保护 revert 恢复源码和 Root gitlink，不删除或重写原始历史证据。

## 验证策略

执行既有 execution policy 全测试，新增同 Goal A→B→A（有/无 verifier）及全新 C 正控制。独立 reviewer 用冻结输入/生产函数复验，不能依赖新测试 helper。既有 target_contracts synthetic receipt 测试增加 verifier false/exception/truthy-nonboolean 控制，不改生产授权语义。安全逻辑变更要求完整 tests/run_all.sh、strict validation、独立 Spec/Quality 与发布校验。
