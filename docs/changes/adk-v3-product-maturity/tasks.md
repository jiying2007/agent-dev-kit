# Tasks: adk-v3-product-maturity

| Task | Status | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| T1 red-contracts | done | `tests/test_product_maturity_v3.sh`、root 对应测试 | reference subrepos | 两个测试在旧实现上失败，修复后转绿 |
| T2 structured-core | done | `src/agent_dev_kit/`、`scripts/devkit.sh`、manifest schema | live runtime roots | strict validate、mirror 和 wheel smoke |
| T3 install-release | done | installer、target adapters、release workflow | `~/.codex` | install rollback + reproducible release contract |
| T4 quality-eval | done | benchmark/security/eval、fixtures | real hardware | deterministic 30/30；Codex baseline 27/30、ADK 30/30、comparison pass；Claude not-run |
| T5 root-intake | done | root intake/analyze/pipeline/CI | reference source worktrees | root intake contract + active pipeline |
| T6 docs-assets | in-progress | maturity SSOT、migration、status、report registry | memory active store | docs/architecture 已通过，current status 待提交基线更新 |
| T7 delivery | ready | source-to-live evidence、commits、push | dirty reference repos | ADK source gates pass；等待父仓 gitlink/status 提交与 remote verification |

## Retry 与停止条件

- 单个测试失败最多进行两轮同假设修复；第三次前必须更新根因。
- heartbeat 为每完成一个 task 更新 change checkpoint 与高层 plan。
- stop condition 仅允许 `pass`、`replan`、`split`、`blocked`、`abort`。
- 实机证据缺失不阻塞软件侧交付，但设备 maturity 固定为 `field_not_verified`。
