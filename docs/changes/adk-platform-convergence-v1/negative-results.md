# 负结果记录：adk-platform-convergence-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash agent-dev-kit/scripts/devkit.sh validate --strict`（before） | 1 | 28 条官方来源到期，当前 release baseline 不再全绿 | `manifests/official_docs_freshness_gates.json` | Source | R4/T4 |
| 三条组合否定 routing probe（before） | 0 | 长任务/调试/发布关键词覆盖只读否定，误命中可执行 Skill | `docs/changes/routing-ir-v2/negative-results.md` | Agent | R1/T1 |
| CR1 Evidence Graph 自由 `attributes.text` 探针 | 0 | benign key 可保存 raw prompt/credential body，构成长期敏感内容通道 | `tests/test_evidence_graph.py` | Test | R9/T9 |
| CR1 target native branch probe | 1 | target-contract/v2 首版只允许 static/not-run，R6 native conformance 不可表达 | `tests/test_target_contracts.sh` | Target | R6/T6 |
| CR1 core export inspection | 0 | core 导出嵌入式 `adk-test-strategy` matrix，平台中立门禁存在假阴性 | `tests/test_profile_coherence.sh` | Profile | R2/T2 |
| CR1 Workflow failure/body drift probes | 0 | 自由 failure target 和仅保留 stage 名的恶意正文可通过首版 compiler | `tests/test_workflow_ir.py` | Workflow | R5/T5 |
| CR1 trace benign-key sensitive-value probe | 0 | v2 首版自由文本值仍可承载 raw secret | `tests/test_trace_summary.py` | Runtime | R7/T7 |

## 处置状态

- official freshness：已逐页复核并固定 Asia/Hong_Kong 治理日，future 继续 fail-closed。
- routing：已建立 routing-ir/v2、权限上限、结构化 negation、artifact mode mapping 和 abstain。
- Evidence Graph：非 outcome attributes 必须空，outcome metrics 精确类型；owner 为受限 identifier；release graph 强制 layer/path；每节点由独立 typed claim 和脱敏 subject 绑定。
- target adapter：native branch 可表达且 evidence 绑定 path/hash/target/runtime/layer，loader 验证存在、containment 和 digest；当前仍明确 not-run。
- core：通用 test strategy 与 embedded matrix 分离，embedded-only 资产回归 Profile。
- Workflow IR：strict schema、I/O、typed edge、terminal/DAG、projection digest 和恶意漂移负例已补齐。
- trace：业务值改为 identifier/code/ref，schema 与 validator 双重拒绝自由敏感值；emitter 仍 not-available。
- R10：30 天独立 field、第二 operator 和双 runtime 属于真实外部证据，当前不能由本地代码替代。
