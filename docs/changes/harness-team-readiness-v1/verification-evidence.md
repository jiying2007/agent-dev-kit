# 完成前验证证据：harness-team-readiness-v1

## Claimant / Verifier

- Claimant：本 change 的实现工件，范围为 readiness typed core、CLI、manifest、fixtures/tests、capability health、canonical migration 和文档。
- Verifier：确定性命令证据与 `review-findings.md` 独立审查阶段；最终 review 为 pass，blocker=0、major=0。
- Human boundary：业务语义、owner 分配、30 天多仓试点与 active Knowledge Hub promotion 尚未由人类 owner 验收，本报告不替代该验收。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk agent-dev-kit/tests/test_harness_readiness.sh` | 0 | 正向 7/7 pass；evidence gap、template/ownership decoy、mixed/non-string secret、malformed/deep contract、权限否定语境、future/stale、历史 gate 时钟、预算超限与脱敏负向回归通过 | `tests/test_harness_readiness.sh` | Source Test | readiness core |
| `rtk agent-dev-kit/scripts/devkit.sh validate --strict` | 0 | strict manifest 与资产验证通过 | `manifests/harness_readiness_contracts.json` | Manifest | contract |
| `rtk agent-dev-kit/tests/run_all.sh --quick --fail-fast --timing-json /tmp/adk-quick-terminal-final-3.json` | 0 | 16/16 通过，耗时 65331ms；重型 product/taxonomy 仍在 full/根包装层 | 本文件 | Workflow Test | quick regression |
| `rtk agent-dev-kit/tests/run_all.sh --timing-json /tmp/adk-full-terminal-current.json` | 0 | 当前最终树 53/53 通过，耗时 340107ms；strict full budget 通过 | 本文件 | Workflow Test | full regression |
| `rtk agent-dev-kit/tests/test_capability_health.sh` | 0 | capability health=8，新增 team-harness-readiness 闭环可解析 | `manifests/adk_capability_health_contracts.json` | Capability | capability contract |
| `rtk agent-dev-kit/tests/test_docs_cli_alignment.sh` | 0 | `harness` public command 与 commands 文档一致 | `docs/commands.md` | Documentation | CLI docs |
| `rtk agent-dev-kit/scripts/check-format.sh` | 0 | diff whitespace/format 门禁通过 | 本文件 | Source | formatting |
| `rtk agent-dev-kit/scripts/check-file-modes.sh agent-dev-kit` | 0 | tracked script mode 与 Git index 一致 | `scripts/quality-gates.sh` | Source | file modes |
| `rtk scripts/check-adk-harden-readiness.sh .` | 0 | 隔离 exact-HEAD 基线 52/52 与 global Codex health 通过；不冒充本 change 证据 | 本文件 | Workspace Baseline | harden readiness |
| `rtk scripts/check-all.sh --full` | 1 | 55/62；本轮性能/goal 已定向修复，剩余失败由 strict dirty、旧 candidate digest 与派生 evidence/status 触发 | `docs/changes/harness-team-readiness-v1/negative-results.md` | Workspace | pre-commit open item |
| `rtk agent-dev-kit/scripts/devkit.sh harness readiness --root agent-dev-kit --gate --summary-json` | 0 | 当前 self readiness：6 pass、1 not-applicable；field not-verified | `.adk/harness-readiness.json` | Product Evidence | self current |
| `rtk git -C agent-dev-kit diff --check` | 0 | diff 无 whitespace error | 本文件 | Source | diff hygiene |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-17` | 0 | Knowledge Hub 候选及 registry/index 结构检查 pass，0 error、0 warning | `~/knowledge-hub/projects/agent-dev-kit/decisions/harness-readiness-v1-candidate.md` | Knowledge Hub | transaction `kh-20260717T151518Z-12bd8c2e` |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json` | 0 | changed-only 检查 1 个正文、精确登记 1 个、missing registry=0 | `~/knowledge-hub/registry/items.jsonl` | Knowledge Hub | reviewing candidate registration |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | final-ready 记录为 pass；session coach 为 HOT，原因是 `~/codex` 既有未提交资产变更，不授权本 change 执行 source-to-live 或清理 | `~/codex/.cache/session-coach-evidence.json` | Session Governance | final handoff |
| final targeted recheck：change governance / readiness test / strict validate / format / diff / file modes | 0 | 六项收口门禁全部通过 | 本文件 | Source + Change Artifact | post-archive closure |

## Acceptance Mapping

| Acceptance criterion | Evidence | Result |
|---|---|---|
| 七个固定维度、无加权总分 | manifest、正向 JSON、Markdown report | pass |
| 默认 report-only，显式 gate 阻断非 pass | 正向/blocked/evidence-gap fixture exit-code 测试 | pass |
| 不执行目标仓、不访问网络、不跟随 symlink | typed core 静态边界与 tests | pass |
| MCP 缺失为 not-applicable | evidence-gap fixture | pass |
| hardcoded secret blocked 且不回显 value | mixed/string/object secret fixture 与 grep 负断言 | pass |
| custom contract 错误归一化 | malformed/deep JSON contract test | pass |
| 扫描和报告有上限 | config/blocker budget tests | pass |
| template/说明文档不制造 pass | evidence decoy fixture | pass |
| 复用 capability/workflow/Skill，不建平行框架 | capability health 与 Harness 决策文档 | pass |
| legacy migration 明确 | proposal/design/changes README/compatibility wrapper | pass with declared breaking behavior |
| 权限完整证据要求结构化 metadata | 否定语境 fixture、permission boundary contract | pass |
| freshness 不能被未来/陈旧日期或历史 gate 时钟绕过 | future/stale 与 `--gate --as-of` 负例 | pass |
| 仓库 ownership 不接受任意嵌套 OWNERS | nested ownership decoy | pass |

## Negative Evidence

- 首轮 change-governance、format/file-mode、strict reference-boundary 和正向 fixture 均曾失败；修复路径与原始退出码保存在 `negative-results.md`。
- 根仓 full 的剩余失败由本次未提交的 strict 子仓、旧 candidate digest 和派生 evidence/status 触发；在不自动 commit/version/rehearse 的边界下不能消除。
- ADK 自身原 partial 基线已由独立 `adk-self-readiness-ownership` change 修复为 6 pass + 1 not-applicable；field evidence 仍为 not-verified。
- Knowledge Hub 条目仅为 AI drafted reviewing candidate，`manual_validation_pending=true`、`promotion=none`；没有把候选冒充 owner 已批准知识。
- `final-ready` 虽通过，但 session coach 暴露 `~/codex` 的既有 dirty 资产并标记 HOT；本次范围未修改、构建或 apply `~/codex`，不得把该状态归因于本 change 或宣称运行资产已刷新。

## Remaining Risk / Rollback

- Readiness 仍是保守启发式 evidence projection，不替代架构与业务 review；误报/漏报需通过 30 天多仓试点校准。
- `quality-gates.sh` 行为发生显式 breaking migration；外部旧调用者必须迁移工件。若出现无法迁移的生产调用，可恢复旧脚本并临时并行运行，但必须另立 sunset change。
- 原公众号 URL、发布日期与许可证未确认；本 change 不复制正文/图片，也不把二级材料提升为官方来源。
- 没有 field evidence，因此不得声明 production-certified 或 M5。
- Knowledge Hub 复核周期为 2026-10-15；active 前仍需 owner 签收、两仓/两操作者/30 天 report-only 试点与原公众号 URL provenance 补全。
