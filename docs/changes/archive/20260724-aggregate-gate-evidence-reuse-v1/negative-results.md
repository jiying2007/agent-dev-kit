# 负结果记录：aggregate-gate-evidence-reuse-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | 直接删除 workspace 中两个重复测试 | coverage/standalone 分析 | `check-workspace-entrypoints.sh` 独立运行将失去覆盖 | standalone aggregate 必须完整 |
| 2026-07-23 | 复用前一次 full 的 result JSON | freshness/dirty 分析 | result JSON 不绑定当前父进程、脚本和工作区内容 | 会掩盖过期或漂移状态 |
| 2026-07-23 | 仅用 `git status` 文本作 fingerprint | dirty subrepo/untracked 分析 | 同一路径的 dirty/untracked 内容变化可能不改变 status 文本 | 必须加入 diff 与 untracked content digest |
| 2026-07-23 | 复用 harden/performance aggregate PASS | 覆盖矩阵分析 | 两者验证 isolated HEAD、benchmark/security/release 独特语义 | 不等价，保持独立执行 |
| 2026-07-23 | 对 evidence、源码和 captured output 统一要求不可 group-write | 首轮 contract tests + debug validator | 合法脚本/输出因仓库 `umask 0002` 为 775/664，被错误拒绝 | 700/600 仅约束临时 evidence；源码/输出改为 owner+regular+digest |
| 2026-07-23 | 从 workspace stdout 解析 `[REUSE]` 作为机器事实 | code review CR-001 | 失败命令若输出同格式文本，可能污染复用计数，虽不改变 gate exit | 改为父进程预建 600 report；append 失败即 fallback |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash scripts/check-all.sh --full --result-json ...` | 1 | 55/59；906s；workspace 207s | `reports/terminal-maturity-check-all-full-2026-07-23.json` | Workflow | R4/T1 |
| root timing JSON | 0 | 16/16；package 18.077s；promotion 38.040s | `reports/terminal-maturity-root-tests-2026-07-23.json` | Test | R1/R4 |
| `rtk bash tests/test_same_run_evidence.sh`（首轮） | 1 | valid evidence 被 mode policy 拒绝 | terminal debug trace | Test | T2 repair-1 |
| `rtk bash tests/test_same_run_evidence.sh`（修复后） | 0 | 合法与伪造/漂移边界通过 | terminal output | Test | T2/T4 |
| `rtk bash tests/test_check_all_contract.sh`（修复后） | 0 | parent evidence propagation/result JSON 通过 | terminal output | Test | T3/T4 |
| 首轮 fresh full | 1 | 54/59；reuse 6；workspace 148s；harden 发现前一 change 文档含外部仓名 | `full-result-repair-1.json` | Workflow | T5 repair-1 |
| `rtk bash tests/test_no_external_repo_refs.sh` | 0 | 前一 change 文档泛化后 external-reference gate 通过 | terminal output | Test | T5 repair-1 |
| `rtk bash tests/run_all.sh --timing-json ...` | 0 | root 17/17；84.630s | `root-regression-timing.json` | Test | T4/T5 |
| standalone `check-workspace-entrypoints.sh .` | 1 | 约 191s；0 reuse；仅既有 health/strict dirty 失败 | terminal output | Workflow | R3/T5 |
| `rtk bash scripts/check-all.sh --quick --result-json ...` | 1 | 51/53；57s；仅 current-status/subrepo-state strict dirty | root report | Workflow | R3/T5 |
| review 前 fresh full | 1 | 55/59；848s；reuse=6；workspace=150s | `full-result-review-before-fix.json` | Workflow | R4/T5 |
| `rtk shellcheck ...` | 0 | helper/producer/consumer/tests 静态检查通过 | terminal output | Test | T4/T6 |
| 最终 `rtk bash scripts/check-all.sh --full --result-json ...` | 1 | 55/59；854s；reuse=6；workspace=151s；失败集合不变 | `full-result.json` | Workflow | R1-R5/T5 |
