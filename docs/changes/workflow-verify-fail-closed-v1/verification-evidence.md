# Verification Evidence

| Command | Exit | Result | Evidence |
|---|---:|---|---|
| `test_workflow_verify_fail_closed.sh` before | 1 | validate=23 被 format=0 覆盖，假 verified | negative-results |
| `test_workflow_verify_fail_closed.sh` after | 0 | 首 gate 失败、format 不运行、state=verify-failed | deterministic fixture |
| `test_workflow.sh` | 0 | lifecycle/artifact consistency 全分支通过 | workflow test |
| host quick | 0 | 25/25 | timing transcript |

- Breaking change：否；只修复错误放行路径。
- Rollback：恢复函数顺序与删除测试；会重新引入已证明的假绿风险。
- Final：Python 3.11 source `268dc95b…`，63/63、strict/targets/routing/dependency audit pass。
