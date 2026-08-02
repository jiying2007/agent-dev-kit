# Review Findings

## 已闭环发现

| ID | Severity | Finding | Fix | Verification |
|---|---|---|---|---|
| RF-001 | major | build receipt 未绑定 target，plan 后并发修改可能被旧动作覆盖 | 增加 target mutation receipt；区分 `ready/already-applied/stale`，混合状态 fail closed | target drift negative + idempotent tests |
| RF-002 | minor | content no-op 快路径可能跳过缺失空目录的 mkdir ensure | no-op 仅在目录已就绪时返回 already-applied，否则执行 idempotent mkdir | missing-empty-dir test |
| RF-003 | minor | `check.sh` 的完整 governance JSON 会把大量静态 catalog 注入输出 | 新增 `governance-summary-v1` 并限制在 2 KiB | summary test；实际 823 bytes |
| RF-004 | minor | Hub 无效显式 project 会暴露 Python traceback | CLI 捕获 ValueError 并转为 argparse fail-closed error | CLI negative test |

## 开放项

- blocker：0。
- major：0。
- root clean-state 门禁：当前 ADK 是本次未提交工作树，strict subrepo policy 预期失败；这不是实现缺陷，提交后需重跑 root quick/full。
- root smoke 并行/共享 runtime inventory：未在本 change 扩权实现；保留 32s 证据，后续独立优化。
