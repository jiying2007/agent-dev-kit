# 验证证据：agent-value-lifecycle-v1

验证日期：2026-08-30。以下均基于当前共享工作树；没有生成或提交 runtime/field usage receipt。

| 命令/检查 | 结果 | 覆盖 |
|---|---|---|
| `rtk bash tests/test_agent_value.sh` | pass，18/18 | Agent/Skill/Profile emitter、managed authority、attestation scope、manifest/bundle/runtime binding、age/window、coverage、evidence scope、privacy/no-zero/dedupe |
| `rtk bash tests/test_runtime_boundary.sh` | pass | 新 validator 未启用 runtime、网络或外部写入 |
| `rtk bash scripts/devkit.sh validate --strict` | pass，Python 3.8.10 development-only warning | strict manifest/asset gate；未宣称 release evidence |
| `rtk bash tests/test_file_modes.sh` | pass | 新 shell test executable 边界 |
| `rtk bash tests/test_format.sh` | pass | Python/shell/asset 格式 |
| `rtk bash tests/run_all.sh --quick --fail-fast` | pass，28/28 | ADK quick 回归，包含 agent value、trace、workflow、target、runtime boundary |
| `rtk jq empty <contract-and-schema-files>` | pass | 三个 JSON 文件语法 |
| scoped trailing-whitespace/secret-pattern scan | no match | 新增文件 hygiene 与常见 secret pattern |

## Requirement 对账

- live identity：validator 报告 `agent_count=13`、`skill_count=65`、`profile_count=9`，均从当前 manifest 解析。
- SSOT：合同没有 Skill/Profile 清单，也未复制 Agent description/path/default skills；`agent_id` 和 handoff 是受校验引用。
- usage 真实性：默认仍为 `emitter_status=not-measured`、`runtime_enabled=false`、`usage_evidence=none-claimed`；仅显式 schema-valid receipt 输入产生 measured output。
- 权限：rank、effect、tool capability 三层不能超过 manifest permission profile。
- 退役：receipt 只产生 candidate signal，固定需要 owner decision，不执行删除/禁用。
- KPI：asset/invocation/PR/report count 与 input/output/total Token 只能在 diagnostic-only 集合。

## 限制与交叉复核

- 本机解释器不满足 Python 3.11/3.12 release baseline，因此 strict 只构成 development evidence。
- emitter 不主动生成真实 invocation；`not-measured` 是无输入时的预期状态。test fixture 只证明确定性计算，不是 runtime/field usage evidence。
- 本 Agent 已完成自检；最终 blocker/major 交叉审查由父 Agent 在整合阶段完成。

## R8 Measured Emitter Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tests/test_agent_value.sh` | 0 | 18/18，含 managed authority、attestation、future/age/window、完整性、coverage、scope、隐私与状态负例 | `tests/test_agent_value.py` | test | measured emitter |
| `rtk bash -lc 'PYTHONPATH="$PWD/src" python3 -m agent_dev_kit.agent_value --manifest-root . --emit-measurements --summary-json'` | 0 | 空输入返回 not-measured，无 metrics/source count | CLI stdout | smoke | empty emitter |
| `rtk tests/test_format.sh` | 0 | Python/JSON/文档格式通过 | terminal output | source | scoped assets |
| duplicate receipt/asset invocation injection | expected failure | replay/double-count fail-closed | `tests/test_agent_value.py` | negative-test | authenticity boundary |

## Completion Guard

- claimant：R8 子任务实现 Agent/Skill/Profile receipt-driven measured emitter。
- verifier：当前为实现 Agent 的确定性测试；独立 parent review 尚待主线执行。
- required_checks：agent value unit/CLI smoke/format/privacy negative/schema validation。
- passed_checks：unit、CLI smoke、format、opaque refs、secret/raw path、duplicate observation、状态矛盾。
- failed_checks：none in scoped checks。
- skipped_with_reason：quick/full 由主线在并行集成后统一运行；runtime/field smoke 不适用，因为本 change 不实现采集 adapter 且没有真实 runtime receipt。
- trace_eval_regression：not applicable；未修改 prompt、routing、completion gate 或 guidance。
- runtime_control_plane_audit：not applicable；未修改 MCP、hook、permission、approval、sandbox 或 live runtime 配置。
- privacy review：输出只含 manifest asset ID、枚举/数值和 `ref:<sha256>`；`raw_content_stored=false`。
- breaking change：候选 receipt v1 从单一 `evidence_ref` 收紧为 receipt/invocation/source-trace/manifest/evidence opaque refs，并新增 bundle/runtime/authority/window 合同；当前均为未发布共享工作树资产。若已有私有 fixture，按新 schema 迁移后再输入。
- completion_allowed：scoped-test-pass；最终整合放行需 parent 独立 review 与主线 quick/full。
