# Negative Results

## 已验证的负结果

| 时间 | 尝试 | 结果 | 决策 |
|---|---|---|---|
| 2026-07-31 | 检查 `rehearse_release` 版本比较合同 | candidate 必须严格高于 previous，两个 RC5 artifact 不构成合法升级 | 提升到 RC6，不绕过版本门禁 |
| 2026-07-31 | Python 3.11/3.12 local-CI full 首轮 | 两套环境均为 56/57；唯一失败是 change tasks 写入外部参考仓专名，被 residue gate 拒绝 | 改为平台中立的 reference worktree 边界后重跑，不弱化 gate |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk sed -n '657,690p' src/agent_dev_kit/release.py` | 0 | 确认 rehearsal 调用 `_prerelease_is_newer` 并对同版本 fail closed | command output | Release | proposal/design |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（首轮） | 1 | Python 3.11 与 3.12 均 56/57，external repo residue 负例命中 | command output; `source_snapshot_sha256=6de1a2a5...` | Test | T2 negative |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（修复后） | 0 | Python 3.11 与 3.12 均 57/57；security、performance、deterministic eval、release check、wheel、pip-audit 全通过 | command output; `source_snapshot_sha256=52bf3f94...` | Test/Release | T2 |
