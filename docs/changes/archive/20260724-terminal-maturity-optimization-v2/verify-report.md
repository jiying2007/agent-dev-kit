# 验证报告：terminal-maturity-optimization-v2

- 时间：2026-07-23T12:50:07Z
- 执行人：leiwenjun
- 验证命令：
  - scripts/validate-assets.sh --strict
  - scripts/check-format.sh
  - scripts/check-change-governance.sh <change_dir>
- 工件检查：proposal/design/tasks/checklist/negative-results

[PASS] change governance checks passed: /home/leiwenjun/bin/llm_agent/agent-dev-kit/docs/changes/terminal-maturity-optimization-v2
Validation passed. strict=1 quick=0
Format check passed

## 执行结论

- source/test 结论：pass。根仓回归 16/16、ADK 回归 57/57，受控
  Python 3.11/3.12 quick 各 20/20，两个版本的 dependency audit 均为
  `No known vulnerabilities found`。
- 聚合门禁结论：needs-fix。fresh `check-all --full` 为 55/59；四个失败均
  由 strict `agent-dev-kit` 工作树仍有未提交变更派生，分别是
  `current-status-consistency`、`evidence-bundle`、`subrepo-state` 和
  `workspace-entrypoints` 的 health 总状态。
- 成熟度结论：保持 overall M3、`terminal_mature=false`、Software M5
  certification blocked；本 change 不生成或伪造 runtime/field/final 证据。
- 发布结论：本地候选实现已验证，但不是 clean-commit/release 证据；不得声称
  可提交、可发布、可合并或终态成熟。

## Evidence Index

| Command | Exit | Result | Evidence |
|---|---:|---|---|
| `rtk bash tests/run_all.sh --timing-json .../adk-full-timing.json` | 0 | 57/57 pass；369574 ms | `adk-full-timing.json` |
| `rtk scripts/run-local-ci-parity.sh --python all --mode quick` | 0 | Python 3.11/3.12 各 20/20；audit clean；snapshot `0d06c2ec...` | terminal command evidence |
| `rtk bash ../tests/run_all.sh --timing-json ../reports/terminal-maturity-root-tests-2026-07-23.json` | 0 | 16/16 pass；80883 ms | `../reports/terminal-maturity-root-tests-2026-07-23.json` |
| `rtk bash ../scripts/check-all.sh --quick --result-json ...` | 1 | 51/53；仅 current-status/subrepo-state | `../reports/terminal-maturity-check-all-quick-2026-07-23.json` |
| `rtk bash ../scripts/check-all.sh --full --result-json ...` | 1 | 55/59；四项同根因状态失败 | `../reports/terminal-maturity-check-all-full-2026-07-23.json` |
| `rtk ../scripts/check-token-budget.sh .. --summary-json` | 0 | README 518/520；budget pass | fresh full result |
| `rtk ../scripts/check-reference-dirty-triage.sh .. --date 2026-07-23 --summary-json` | 0 | 三个 reference repo fingerprint/classification pass | `../reports/reference-dirty-triage-2026-07-23.json` |
| `rtk shellcheck ...`、`rtk bash -n ...`、`rtk git diff --check` | 0 | 新增/修改 shell 与 diff 静态检查通过 | terminal command evidence |

## 负向与恢复证据

- 首次 verify 因 checklist 精确标签缺失失败并进入 `verify-failed`。
- 根因不是业务实现，而是 workflow 原状态机不允许从 `verify-failed` 重试。
- 修复后 `test_workflow` 覆盖“失败 -> 保留状态 -> 补证 -> 同 change 重试成功”，
  本 change 随后从 `verify-failed` 进入 `verified`；未手改 state 掩盖失败。
- 首次 Docker audit 因沙箱网络无法升级 pip 失败；在脚本声明的受控
  audit-bridge 边界下重跑，两个 Python 版本均确认无已知漏洞。

## Source-to-live 决策

- `agent-dev-kit` 中存在 mapped asset 变更，但本 change 没有修改
  `~/codex` 或 `~/.codex`。
- 当前决定：`required-after-clean-commit-and-owner-approval`。
- 后续必须按 `agent-dev-kit -> ~/codex -> ~/.codex` 执行 build、doctor、
  plan、apply dry-run、经批准 apply、routing/check 与 runtime health，并保留
  rollback 证据；在提交与授权前不得执行或宣称 live refresh。

## 未解除的外部/权限 blocker

- 真实 clean commit、根仓 gitlink/adk.lock/current-status 刷新需要 owner 的
  Git 决策；本任务未获自动 commit/push/merge/rebase 授权。
- final 3.1.0、独立真实仓、第二位 human operator、30 天 pilot、双 runtime
  campaign、repository runtime campaign 与必需 field events 仍未完成。
- 本次无新增 Knowledge Hub candidate：长期事实仍由 scorecard、policy、
  pilot ledger 与本 change 工件承载，避免复制未提交候选状态。
