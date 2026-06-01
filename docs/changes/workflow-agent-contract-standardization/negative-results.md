# Negative Results: workflow-agent-contract-standardization

## 已验证的负结果
| 时间 | 尝试 | 结果 | 后续动作 |
|---|---|---|---|
| 2026-06-01 | 在 workflow 命令校验中允许 `~/codex/scripts/*` | `runtime-boundary` 拦截平台绑定残留 | 删除例外，只允许仓内 `scripts/` 与 `tests/` |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash scripts/devkit.sh validate --strict --summary-json` | 0 | strict validate 通过，workflows=6 | terminal output | validation | manifest.yaml |
| `rtk bash tests/run_all.sh --fail-fast` | 0 | 全量回归通过 | terminal output | regression | tests/run_all.sh |
| `rtk bash ~/codex/scripts/apply.sh --plan ~/codex/build/apply-plan.json --dry-run` | 0 | source-to-live dry-run 通过，无 copy/overwrite/delete | terminal output | dry-run | apply-plan.json |
| `rtk bash ~/codex/scripts/check.sh` | 0 | codex source/live/smoke 检查通过 | terminal output | source-live | ~/codex |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | final-ready pass，提示上下文压力 | terminal output | readiness | session coach |
