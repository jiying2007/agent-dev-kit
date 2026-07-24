# 验证报告：aggregate-gate-evidence-reuse-v1

- 时间：2026-07-23T15:19:54Z
- 执行人：leiwenjun
- 验证命令：
  - scripts/validate-assets.sh --strict
  - scripts/check-format.sh
  - scripts/check-change-governance.sh <change_dir>
- 工件检查：proposal/design/tasks/checklist/negative-results

[PASS] change governance checks passed: /home/leiwenjun/bin/llm_agent/agent-dev-kit/docs/changes/aggregate-gate-evidence-reuse-v1
Validation passed. strict=1 quick=0
Format check passed

## 完成声明核验

- Claimant：同运行 evidence reuse 已实现且不改变 coverage/failure semantics。
- Verifier：
  - root regression 在最终 full 中 17/17 PASS；
  - harden/performance/root 均保持独立执行并 PASS；
  - 最终 full 失败集合与基线完全一致；
  - standalone workspace 没有复用，invalid evidence contract tests 全部拒绝；
  - `same_run_reuse.count=6` 来自 owner-only report，不来自 stdout。
- 缺失证据：没有 Git clean/source-to-live/live runtime 证据；本 change 为
  project-bound source change，不声明 delivery/release 完成。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash tests/test_same_run_evidence.sh` | 0 | 合法 PASS 接受；PID/root/digest/fingerprint/symlink/失败证据拒绝 | terminal output | Test | R2/R5 |
| `rtk bash tests/test_check_all_contract.sh` | 0 | parent evidence、专用 report、stdout spoof 与 result JSON 通过 | terminal output | Test | R1/R4 |
| `rtk shellcheck ...` | 0 | producer/consumer/helper/tests 静态检查通过 | terminal output | Test | T6 |
| `rtk bash scripts/check-all.sh --quick --result-json ...` | 1 | 51/53；仅 strict dirty 派生失败 | root report | Workflow | R3 |
| standalone workspace aggregate | 1 | 0 reuse；完整路径约 191s；仅既有 health/strict dirty 失败 | terminal output | Workflow | R3 |
| 最终 `check-all --full --result-json ...` | 1 | 55/59；854s；reuse 6；workspace 151s；失败集合不变 | `full-result.json` | Workflow | R1-R5 |
| `rtk bash scripts/devkit.sh verify --change ...` | 0 | governance/strict validation/format PASS | 本文件 | Workflow | T6 |

## 兼容、风险与回退

- Breaking change：否；result JSON 仅增加可忽略字段，standalone/quick/smoke
  保持原执行语义。
- Prompt/model/context/approval：均未变更。
- 回退：移除 producer evidence 初始化、consumer allowlist 和 helper；原
  `run_check` 路径始终存在。
- Retry audit：valid evidence 首轮因 umask mode policy 失败，单次修复后通过；
  harden 文档回归单次修复后通过，均未耗尽 retry budget。

## Final Gate Result

- Source gate：pass。
- Delivery/release gate：blocked by strict ADK dirty 与未授权 Git/source-to-live
  动作；未被本 change 伪装为 pass。
