# Verification Evidence

## Scope

- source-ready：ADK 原生路由、pilot/control gate、retired tombstone、根 runtime footprint policy。
- plan-ready：28-Skill `team-core` development Bundle 与团队导入 plan。
- live-pending：未应用团队仓、`~/codex` 或 `~/.codex`；根参考仓保持不变。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash agent-dev-kit/scripts/run-local-ci-parity.sh --python all --mode full` | 0 | Python 3.11/3.12 均 68/68，routing 30/30，dependency audit pass | full parity receipt | Release Gate | ADK source snapshot |
| `rtk scripts/devkit.sh validate --strict` | 0 | manifest、Skill、profile 严格校验通过 | terminal output | ADK | manifest mirror |
| `rtk bash tests/test_match_effectiveness.sh` | 0 | 40/40；旧外部 Skill 名称只保留 review 意图 | terminal output | Routing | prompt regression |
| `rtk bash tests/test_skill_trigger_matrix.sh` | 0 | 正负触发矩阵通过 | terminal output | Routing | trigger fixtures |
| `rtk bash scripts/pilot-readiness.sh --summary-json` | 0 | 10/10 ready，fallback_used 均为 no | terminal output | Pilot | native ADK evidence |
| `rtk scripts/check-runtime-targets.sh . --summary-json` | 0 | required/forbidden footprint contract 通过 | terminal output | Workspace | runtime_targets.json |
| `rtk bash tests/test_runtime_live_footprint.sh` | 0 | required 缺失与 forbidden residue 负路径均被阻断 | terminal output | Workspace | live footprint gate |
| `rtk scripts/check-runtime-live-footprint.sh . --summary-json --strict` | 1 | 当前 live 仍有 forbidden vendor path，正确 fail closed | terminal output | Runtime | live-pending blocker |
| `rtk scripts/devkit.sh release runtime-build --profile team-core ...` | 0 | 28 Skills / 59 files；Bundle 文本无外部兼容命中 | development artifact | Runtime Bundle | plan-only |
| `rtk bash scripts/team-assets.sh bundle plan ...` | 0 | 团队导入 plan ready，5 个变更 Skill 使用新版本路径 | team cache plan | Team Distribution | plan-only |
| 根仓 `rtk bash tests/run_all.sh --fail-fast` | 1 | 现有 smoke identity/owner attestation 阻断，非本轮改动 | terminal output | Workspace | existing product evidence |
| 根仓 `rtk scripts/check-all.sh --quick --working-tree` | 1 | 54/55，其余本轮相关门禁通过 | terminal output | Workspace | existing current-status blocker |

## Prompt Regression

- before：复杂只读 review 文本曾 abstain；混合“工作树”样例曾误路由 worktree governance。
- after：原始只读 review 文本和显式旧外部 review 名称均命中 `adk-code-review-loop`；真实创建 worktree 仍命中 `adk-worktree-governance`。

## Completion Guard

- source gate：pass。
- team/live gate：needs-fix，等待 clean commit/release 与 live prune。
- breaking migration：旧外部 Skill 名称只保留意图并映射 ADK 原生能力；无安全等价能力时返回 no-skill/needs-input。
- rollback：恢复上一 clean Runtime Bundle，并走同一 plan/dry-run/apply 与 receipt rollback。

## Codify Decision

- reusable_pattern：外部参考与运行兼容分离；runtime 用 required/forbidden footprint fail closed。
- promotion_candidate：false。
- next_task_friction_reduced：后续不再维护逐 Skill sunset 评分。
- reduced_by：retired tombstone、路由 fixtures、runtime footprint contract。
- reduction_evidence：双 Python full parity、routing 30/30、footprint 正负测试。
- do_not_promote_reason：仍待 owner 审查 clean release 与 live prune plan。
- owner_review：pending。
- rollback_path：上一 clean Runtime Bundle 和 source-to-live receipt。
- verification_evidence：本文件 Evidence Index。
