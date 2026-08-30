# 验证证据：privacy-ref-hardening-v1

## 语义证据

- 共享 validator：`src/agent_dev_kit/privacy_ref.py`。
- Graph schema：`schemas/evidence-graph-v1.schema.json`。
- Trace schema：`schemas/adk-workflow-trace-summary-v2.schema.json`。
- Receipt schema：`schemas/asset-invocation-receipt-v1.schema.json`。

## 定向结果

| 命令 | 结果 | 层级 |
|---|---|---|
| `rtk tests/test_evidence_graph.sh` | 5/5 pass | source-test |
| `rtk tests/test_trace_summary.sh` | 8/8 pass | source-test |
| `rtk tests/test_agent_value.sh` | 7/7 pass | source-test |
| `rtk scripts/devkit.sh validate --strict --summary-json` | pass；Python 3.8 development-only | source-test |
| `rtk tests/test_runtime_boundary.sh` | pass | source-test |
| `rtk tests/run_all.sh --quick --fail-fast` | 28/28 pass | source-test |
| `rtk git diff --check -- <CR4 scope>` | pass | source-test |

## 边界

- Trace emitter 仍为 `not-available`。
- Agent Value emitter 仍为 `not-measured`、`runtime_enabled=false`。

> Supersession note（2026-08-30）：以上是本 change 验证时的历史状态。当前 Trace 已有 explicit-call emitter，
> Agent Value 已有显式 receipt 聚合 API；两者都不代表 automatic runtime/native integration，canonical global usage
> 仍是 not-measured。当前状态以各自 change 与 umbrella verification evidence 为准。
- 测试 evidence 文件仅位于临时目录，不作为 runtime/field evidence。
