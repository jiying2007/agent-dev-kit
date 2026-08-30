# Verification Evidence：adk-platform-convergence-v1

## Current Verdict

- implementation status：`applied / local-candidate-verified`
- completion verdict：`NEEDS-FIX`
- release readiness：`false`
- field readiness：`not-verified`
- evidence snapshot：`5.0.0-rc.1` 当前 working tree；未 commit/stage，不构成 release-clean evidence

## Requirement Status

| Requirement | Status | Evidence | Open boundary |
|---|---|---|---|
| R1 routing IR | implemented-local | routing 39/39、routing IR contract 4/4，且 contract suite 已接入聚合 | runtime/field feedback emitter 未启用 |
| R2 neutral core | implemented-local | profile、target、taxonomy、core/embedded closure | measured usage 未证明长期效果 |
| R3 Runtime Control | implemented-local | runtime 19/19、goal intake/attestation、event/policy/state 统一 secret taxonomy | source-to-live/runtime adapter 尚未启用 V2 |
| R4 source/toolchain | verified-supported-quick | 69 official sources；Python 3.11/3.12 quick parity 各 29/29；wheel/audit pass | supported full parity 未在最终版本快照复跑 |
| R5 Workflow IR | implemented-local | Workflow IR 5/5、7 workflows/41 nodes | 外部 runtime 尚未消费 IR |
| R6 Runtime Adapter | contract-only | target v2 receipt/loader tests pass；Codex/Claude runtime 可发现 | Claude 最小 smoke 超过 4 分钟无结果后人工终止，3 target 仍 static/not-run |
| R7 Trace/Eval | implemented-local | Trace 12/12；Run Evidence 4/4；Effect Comparator 3/3；完整 task population/coverage-aware delta | target automatic/native integration、真实 baseline/ADK runtime campaign 未完成 |
| R8 Agent value | implemented-local | Agent value 18/18；receipt-driven measurement、managed authority 默认关闭、coverage/window/layer 门禁 | canonical runtime usage 仍 not-measured；无真实 runtime/field receipt |
| R9 Maintainability/Graph | implemented-local / evidence-open | Graph 5/5；11 static budgets + 3 evidence metrics；population/repo/revision/freshness 绑定 | 当前 churn/owner/inactive source 均 not-available/null，不宣称健康 |
| R10 runtime/field | open-external | Software M5 certifier | dual runtime、independent repo、2 operators、30 days |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash agent-dev-kit/tests/run_all.sh` | 0 | 68/68；含完整 `test_match_effectiveness` | terminal output | Product/Test | R1-R9 |
| `rtk bash agent-dev-kit/scripts/run-local-ci-parity.sh --python all --mode quick` | 0 | source snapshot `2cf93216...`；Python 3.11.15/3.12.13 各 29/29；routing 30/30；wheel、dependency audit、strict/security/release pass | terminal output；snapshot SHA 由仓外 current Evidence Index 记录，避免 evidence 文件自引用 | Release/Test | R4 |
| Python 3.12 quick 初跑与原配置复跑 | 1 / 1 | 30/30 功能通过，但总时长 128342/120636ms 超 120000ms；未放宽预算 | terminal output | Performance/Negative | R4/T11 |
| quick test pyramid 收敛后双 Python parity | 0 | `test_skill_trigger_matrix` 保留在 quick；重复的进程级 `test_match_effectiveness` 留在 full；各 29/29 且预算通过 | `tests/run_all.sh` | Performance/Test | R4/T11 |
| `rtk bash agent-dev-kit/scripts/devkit.sh release check --summary-json` | 0 | `5.0.0-rc.1` version/direct-target/source contract pass | terminal output | Release/Test | T11 |
| `rtk bash agent-dev-kit/scripts/devkit.sh release build --version 5.0.0-rc.1 ...` | 0 | source distribution 954 files；candidate artifact build pass；未发布 | `/tmp/adk-5.0.0-rc.1-build.S17qUK/` | Release/Test | T11 |
| `rtk bash agent-dev-kit/scripts/run-local-ci-parity.sh --python all --mode full` | interrupted after fail | source snapshot `74c48195ff0b85875e77ba9df676d4ae16f146fce76aac2773a34899bb4c70f2`；tracked deleted embedded matrix 被 Git-index inventory 正确阻断 | terminal output | Negative/Release | R4/T11 |
| `rtk scripts/check-all.sh --quick --working-tree` | 1 | 53/55；current-status/M5 因 2026-08-24 rehearsal manifest digest stale fail | terminal output | Workspace/Negative | R6-R10 |
| `rtk tests/test_maintainability_budgets.sh` | 0 | 11 budget/semantic axes contract pass | `tests/test_maintainability_budgets.sh` | Workspace/Test | R9 |
| Claude native discovery attempt 1 | rejected before model | invalid empty MCP shape；无 token/cost | `docs/changes/native-target-conformance-receipt-v1/negative-results.md` | Runtime/Negative | R6 |
| Claude native discovery attempts 2/3 | fail/no evidence | 历史尝试无 structured evidence；当时 `Not logged in`；token/cost 0 | `docs/changes/native-target-conformance-receipt-v1/negative-results.md` | Runtime/Negative | R6 |
| Claude runtime smoke（认证就绪后） | 130 | `--limit 2` 超过 4 分钟无结果后人工终止；未生成 output receipt，不能形成 runtime capability claim | terminal output | Runtime/Negative | R6 |

## Independent Review

- CR1：首轮发现 2 blocker、4 major；修复后 blocker/major/minor 为 0。
- CR2：routing 首轮发现 4 major、1 minor；均已修复并复审。
- CR3：Runtime task applicability 无 blocker/major，1 个测试缺口已补。
- CR4：整合审查发现 R1/R3/R6/R9、privacy、Workflow 权限、report freshness 和 release digest 缺口；
  第二阶段已修复可由 source/test 关闭的项。
- CR5：发现 packaging、近义否定、Runtime/target trust 与 privacy、Graph claim 绑定缺口；均已修复。
- CR6：最终树独立复审确认 code blocker/major 为 0；整体仍因 R6/R10、emitter/R9 未测轴和 release/M5 证据保持 NEEDS-FIX。
- CR7：R7-R9 首轮实现发现 emitter trust、coverage、provenance/population/freshness 等 blocker/major；
  三轮反例修复后 R8、R9 独立复审 blocker/major=0，R7 定向 12/12。
- CR8：子代理额度耗尽后只保留已有完整设计的 Run Evidence composition，由主 Agent 串行实现；
  trace/receipt/measurement 绑定、abstain inference、projection tamper 和 test-only authority 4/4 通过。
- CR9：用户恢复目标后新增完整 population Effect Comparator 与 Git churn review-required candidate generator；
  comparator 3/3、candidate 2/2，均不产生 runtime/field/promotion authority。

## Replayable Evidence Boundary

- input snapshot：综合评估报告、R1-R10 requirements、当前 manifest/contract/source tree。
- environment：host Python 3.8 development；Docker Python 3.11/3.12 supported parity；runtime discovery 为 Codex 0.144.1、Claude 2.1.138。
- raw transcript：不保存；只保留命令摘要、hash、exit 和脱敏原因。
- sensitive review：Trace/Graph/Agent/native/Runtime event-policy-state 复用 strict opaque ref 与 secret taxonomy；
  Graph 每节点还必须有独立 typed claim 和脱敏 subject。
- non-replayable：Claude 外部调用无结果的环境原因和 30 天 field 时间窗口不可由 fixture 重放。

## Completion Guard

- build：source/test wheel build pass in Python 3.11/3.12 quick parity；本地 source candidate artifact 已建立但未发布。
- lint/format：pass。
- test：ADK 68/68 pass；root terminal gate 53/55，两个 release/M5 integrity gate 按预期 fail-closed。
- smoke：static targets pass；Claude execute smoke 无 receipt 后终止，native target 仍 not-run。
- security：typed privacy/permission negative tests pass；最终全量安全门禁待 release closeout。
- release：candidate build/check pass；未完成 4.0.0→5.0.0-rc.1 checksum-bound rehearsal、tag、发布或 source-to-live。
- completion_allowed：`false`。
