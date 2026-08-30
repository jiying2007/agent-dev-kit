# Verification Evidence: Runtime Control Task Mode Applicability V2

## 2026-08-30 首轮验证

| 命令 | 结果 | 证据层 | 结论 |
|---|---:|---|---|
| `rtk tests/test_runtime_control.sh` | 0，18/18 | ADK targeted | V1 回归、V2 state-bound mode/applicability、attestation、managed authority 与 replan 用例全部通过 |
| `rtk scripts/devkit.sh validate --strict` | 0 | ADK strict | manifest、schema 与资产严格校验通过 |
| `rtk scripts/devkit.sh validate --quick` | 0 | ADK quick | 快速校验通过 |
| `rtk python3 -m py_compile ...` | 0 | syntax | Engine、导出 API 和测试文件可编译 |
| `rtk git diff --check` | 0 | source hygiene | 无尾随空白或 patch 格式错误 |
| `rtk tests/test_official_docs_timezone.sh` | 0 | unrelated rerun | full run 中并发刷新造成的一次暂态失败已单项复验通过 |

## Full run 说明

`rtk tests/run_all.sh` 在并行分支仍写入 official source freshness 资产期间得到 63/64；唯一失败为与 Runtime Control 无调用关系的 `test_official_docs_timezone`。待并发修改稳定后，该测试已独立复跑通过。Runtime Control 在该 full run 中通过；最终 64/64 由主线整合阶段统一复跑，避免把并发工作树的暂态结果冒充全绿证据。

## 行为证据

- V1 基线：闭环的只读目标因缺少 `build/repo` 返回 `required-artifact-missing`。
- V2 readonly：goal intake 绑定 `task_mode=readonly`、`artifact_mode=readonly`，final 评估得到 `required_artifacts=[]`、`completion_allowed=true`、`gate_allowed=true`。
- Final override：向 V2 evaluate 传 `task_mode=implementation` 被拒绝，不能替换 state-bound mode。
- Replan：仅 `goal.updated` + `mode_change_reason=replan` + 新 `goal-replan` attestation 可更新 mode，revision 从 1 变为 2。
- CR5 forged authority：trusted ID + arbitrary request/routing digest + recomputed SHA，在 normal evaluate 无 verifier 时使用 implementation floor 并拒绝 final；test-only verifier 对不匹配 binding 同样返回 false。
- End-to-end authority verification：open；本轮未声称验证外部签名或真实 routing decision provenance。
- V2 implementation：缺少 `build/repo` 时 final gate 失败。
- V2 release：缺少 `build/live/repo/review` 时 release gate 失败。
- V2 readonly 的 idle/active goal、缺失 required evidence、release gate 均失败。
- V2 缺失/未知 task mode、弱化 implementation floor、readonly 引入 implementation artifacts、嵌入敏感字段均拒绝。
- V1 policy 省略 task mode 与显式 `implementation` 的 decision 完全一致，schema 仍为 `runtime_control.decision/v1`。

## 环境与证据强度

- 当前默认 Python 为 3.8.10，低于项目要求的 Python 3.11+；`validate` 已明确标注结果为 development-only。
- 当前环境没有 `ruff`，未进行外网安装；release 证据需要在受支持 Python 环境补跑 ruff 与完整回归。
- 本轮未修改 Codex adapter/live manifest。V2 是 Engine opt-in；上层启用时必须将 policy 切到 V2，并为每次评估显式传入受治理的 task mode。

## 残余风险与回滚

- 风险：上层 adapter 若未迁移，仍使用 V1 全局工件语义；不会静默放宽，但只读 final 仍会按旧行为失败。
- 风险：task mode 的授权来源属于 adapter/goal intake 边界；Engine 只验证枚举、适用性矩阵和目标闭环，不根据原始 objective 推断。
- 回滚：删除 V2 schema/change 资产并回退 Engine V2 分支；V1 event/state/policy/decision 无需迁移或 journal 回滚。
