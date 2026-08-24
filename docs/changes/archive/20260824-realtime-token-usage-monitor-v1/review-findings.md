# Review Findings

## Snapshot

- Review Target：working-tree。
- HEAD：`302378e65dce8401dc2338960ce014097869ab13`。
- Source snapshot：`6f7b6a2bce2b8069ad3904d86f78ab2280d46a0b3e2b47e9aa38b0693c24bf2f`。
- Reviewer Independence：`author-self-review`，不得冒充 independent review。

## Findings

| ID | Severity | File | Evidence | Required Action | Status |
|---|---|---|---|---|---|
| RF-001 | major | `token_monitor.py:252` | 失败事件先增加 received，异常后 state counters 不一致 | 只在成功 apply/duplicate 后计数，补恢复测试 | fixed |
| RF-002 | major | `cli.py:774` | 事件先 flush、state 后写；写失败会让 consumer 与恢复状态分叉 | state 原子写成功后再输出事件 | fixed |
| RF-003 | major | `cli.py:749` | `~` state path 在 exists 前未 expand，可能漏载已有状态 | 初始化时统一 expand + resolve | fixed |
| RF-004 | major | `token_monitor.py:177` | state 未交叉校验 fingerprints/applied 与 scope type/snapshot | 增加恢复状态一致性校验 | fixed |
| RF-005 | minor | `token_monitor.py:122` | dedupe fingerprints 随已应用事件线性增长 | 本版记录残余风险；阶段边界轮换 state，后续评估有界 history/cursor contract | open-follow-up |

## Re-review

- RF-001：`test_failed_event_does_not_corrupt_state_counters` 证明失败 snapshot 后 state 可恢复。
- RF-002：源码顺序已变为 `write_state -> _json -> flush`；写失败不会发布未持久化 decision。
- RF-003：`state_path` 在 exists/load/write 前统一解析。
- RF-004：恢复校验要求 `len(event_fingerprints) == events_applied`，且 snapshot scope 与 type 对齐。
- 定向测试：8/8；format/diff check 通过。

## Remaining Boundary

- RF-005 不影响当前 4 小时/有限 Token 预算场景，但不宣称无限时长、无限事件规模。
- runtime adapter、真实 provider usage 和自动动作执行不在本 change；需要独立 pilot/owner review。
