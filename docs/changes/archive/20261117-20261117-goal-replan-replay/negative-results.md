# 负结果记录：20261117-goal-replan-replay

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-11-17 | 当前 attestation 比较足以防止历史重放 | 独立冻结 A→B→A | 旧 A 被再次接纳 | 新 event_id 不能证明凭据未消费 |
| 2026-11-17 | 无 verifier 路径已发生实际授权绕过 | 原始无 verifier 控制 | gate=false，implementation floor 保持 | 不作真实宿主绕过声明 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| rtk proxy python replay_frozen_probe.py BASELINE | 1 | 历史旧 A 被接纳；全新 C 正控制通过 | evidence/original-counterexample/frozen-before.json | independent synthetic | requirements.md |
| rtk proxy python original_probe.py | 0 | 原始三个观察已保存 | evidence/original-counterexample/original-before.jsonl | independent synthetic | design.md |
| rtk proxy python -m unittest discover -s tests -p test_execution_policy.py | 1 | 新回归25 tests中3 failures，旧A和重启重用未拒绝 | evidence/implementation-observations.json:red-execution-policy.log | deterministic RED | REQ-001 |
| rtk proxy bash tests/test_target_contracts.sh | 0 | verifier拒绝/异常/非True原实现正确，首次即通过 | evidence/implementation-observations.json:baseline-target-contracts.log | synthetic contract | REQ-003 |
