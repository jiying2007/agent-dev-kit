# C2 独立历史 attestation 重放反例

基线：`5f113b8f5ae6f83662d41d99d0907026f4e44c9d`，ADK 11.3.15。

所有文件属于独立审查的内部证据，不是实现者测试输入；不得为使候选通过而修改。候选可以更换下列命令的仓库路径，冻结 inputs 与 verifier 语义保持原样。没有调用真实 runtime、模型、GitHub 或其他外部写操作。

## 原始观察

`original_probe.py` 是首次执行的代码，调用基线原有测试 helper 生成合法事件。`original-before.jsonl` 是在确认相关生产目录和 helper 相对基线没有 diff 后重新执行并保存的原始 stdout，退出码 0。

`frozen-inputs.json` 固化该三条完整 events/policy/as_of，另加一个真正全新 readonly replan 正控制。`replay_frozen_probe.py` 不再导入实现者测试 helper，只读取冻结输入并调用指定候选仓库的生产 reduce_events/evaluate。`frozen-before.json` 是实测 stdout，退出码 1；原始三项现象不变，新 replan 正控制通过。

1. 合法 readonly A → 较新 implementation B：最终缺 build/repo，gate/completion false。
2. A → B → 给旧 A 换新 event_id 再投递：当前 reducer 接受 intake_revision 3→4；使用原 synthetic managed verifier 时退回 readonly，gate/completion true。
3. 相同旧 A 重投递，但不注入 verifier：reducer 仍接受旧 intake；evaluate 保留 implementation artifact floor，gate/completion false。
4. A → B → 真正新的 readonly C（新 decision_id、issued_at、attestation）：应保持可接受，不能用禁止一切 mode replan 来修反例。

限定：verifier 是基线 tests/test_execution_policy.py 的 synthetic unit-test verifier，只用于机械判定已输入的声明。默认生产路径没有该 verifier，仍有 implementation floor。本反例证明 reducer 的历史已消费 attestation 可被作为“新 replan”重新接纳，不证明真实宿主授权已被绕过。

## 根因位置与验收

`src/agent_dev_kit/execution_policy/reducer.py::reduce_events` 的 goal.updated 分支只比较输入 attestation 与当前 attestation，不能识别 A→B→A 的历史重用。`contracts.py::_validate_goal_intake` 校验绑定摘要、goal ID、provenance kind 与 issued_at 不晚于外层事件，但不负责历史消费检测。现有 exact event_id 去重只覆盖外层 ID 相同的重放。

最小验收：同一 logical Goal 已消费的旧 attestation 即使装在新的外层 event_id 中，也不能再次改变 canonical mode；拒绝不依赖是否注入 verifier。真正全新且有效的 replan 仍可被接纳；原有同 event_id 幂等重放、错 Goal/错 hash 拒绝与无 verifier artifact floor 保持。

本次修复不需要建立 runtime adapter、外部租约服务、第二 Goal 权威或新的持久总账。

## 精确复验

```bash
/workspace/scratch/fe8de3b42084/verification-tools/rtk proxy /workspace/scratch/d417066aafa8/agent-dev-kit/.venv/bin/python -B /workspace/scratch/d417066aafa8/independent-review/c2-attestation-replay/replay_frozen_probe.py /workspace/scratch/d417066aafa8/agent-dev-kit
```

基线预期退出 1；修复候选应退出 0，四项 acceptance controls 全部成立。后续结果写新文件，不覆盖 before 或冻结输入。
