# Verification Evidence

## Current evidence

| Command | Result | Scope |
| --- | --- | --- |
| `rtk bash tests/test_runtime_bundle.sh` | pass，3 cases | deterministic bundle、source exclusion、symlink/unknown profile negative |
| `rtk bash tests/test_profile_coherence.sh` | pass | `team-core` profile closure |
| `rtk bash tests/test_optional_skills.sh` | pass | optional install regression |
| `rtk bash tests/test_asset_taxonomy.sh` | pass | lifecycle/profile/catalog taxonomy |
| `rtk bash tests/test_product_maturity_v3.sh` | pass | release reproducibility、rehearsal、安全边界 |
| `rtk bash tests/test_docs_cli_alignment.sh` | pass | CLI/docs coverage |
| `rtk bash tests/test_skill_content.sh` | pass，448 assertions | Skill 内容质量 |
| `rtk bash scripts/devkit.sh validate --strict` | pass | 三个 source_ref 经官方复核刷新后 strict 通过 |
| `rtk bash tests/run_all.sh`（team-codex-assets） | pass，4 cases | 一键 setup 幂等、import/install/rollback、path traversal、source-bearing bundle negative |
| 真实 RC7 `team-core` bundle smoke | pass，32 skills / 63 source files | import、build、install dry-run/apply/check、双 rollback |
| `rtk bash tests/run_all.sh --timing-json /tmp/adk-team-runtime-full-after-refresh-20260821.json` | 59/59 pass | 前置 freshness 与 Skill 内容门禁修复后完整回归通过 |
| `rtk bash scripts/run-local-ci-parity.sh --python all --mode quick` | Python 3.11/3.12 wheel build、install、doctor pass；matrix overall fail | 两条 matrix 均被同一组三个 source freshness 到期阻断 |
| `rtk bash scripts/team-assets.sh install ...`（最终隔离目标） | pass，96 operations | plan、dry-run、apply、target check、rollback |
| Knowledge Hub `knowledge-new --apply` + `knowledge-check --dry-run` | reviewing candidate applied；Hub check pass | 脱敏候选，不含私网地址，不提升 active |
| 内部团队仓 push + fresh clone smoke | pass；remote `master=4aa112a` | fresh clone tests、32-Skill build/doctor、96-operation plan/dry-run/apply/check/rollback；成员入口收敛为一键 `setup` |
| `rtk bash scripts/team-assets.sh setup --target /tmp/...` 连续两次 | pass；首次 installed 32 skills/96 changes，二次 unchanged/0 changes | 成员一键安装与幂等更新 |

## Pending

- ADK source push 与个人 `~/codex -> ~/.codex` source-to-live 证据。
- 根仓 gitlink/adk.lock/current-status 收口不混入本 source change。
- 真实团队成员新 Codex session discovery/trigger pilot。
