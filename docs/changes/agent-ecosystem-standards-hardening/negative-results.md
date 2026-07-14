# 负结果记录：agent-ecosystem-standards-hardening

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-14 | 为 Agent Skills 再改一次 compiler/target renderer | 检查 `src/agent_dev_kit/targets.py`、`tests/test_target_contracts.sh` 与 RC2 verification report | RC2 已保留 `description` 并覆盖多个 target；重复实现无新增价值 | 会制造重复逻辑和回归面 |
| 2026-07-14 | 新建统一 ecosystem mega-manifest | 对照六个既有领域 SSOT 和 external source ledger | 相同概念会出现第二 owner，增加 drift | 采用“来源集中、契约归域、跨 manifest 校验” |
| 2026-07-14 | 本次直接启用 ACP/A2A runtime 或新增 submodule | 对照 ADK 平台中立资产边界与本次验收范围 | 需要 transport、auth、compatibility、runtime smoke 和供应链审批，超出方法吸收范围 | 只登记 watch-only metadata 与复审触发器 |
| 2026-07-14 | 在 change task 中保留本机参考子仓名称 | 运行 `tests/run_all.sh --fail-fast` | `test_no_external_repo_refs` 拒绝绑定本地参考仓名称的治理文档 | 改为通用的 dirty reference subrepo 边界 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rg -n "Agent Skills|description|target conformance" src tests docs/changes reports` | 0 | 发现 RC2 已覆盖 target conformance，确认无需重复修改 compiler | `reports/llm-agent-adk-terminal-maturity-audit-2026-07-13.md` | diagnosis | `proposal.md` |
| `jq 'keys' manifests/{skill_reproducibility_contracts,adk_runtime_policy_gates,automation_worktree_contracts,skill_mcp_dependencies,trace_eval_contracts}.json` | 0 | 六类目标均存在可复用 SSOT | `manifests/` | architecture | `design.md` |
| `rtk tests/run_all.sh --fail-fast --timing-json /tmp/agent-ecosystem-full-timing.json` | 1 | 首轮全量在 `test_no_external_repo_refs` 失败；定位为 change task 的本机仓名绑定，已最小修复 | `docs/changes/agent-ecosystem-standards-hardening/tasks.md` | regression | `negative-results.md` |
| `rtk scripts/check-agent-ecosystem-standards.sh --summary-json` | 0 | 283 checks；7 sources；ASI01-ASI10；6 negative fixtures；runtime disabled | `scripts/check-agent-ecosystem-standards.sh` | contract | `design.md` |
| `rtk tests/test_agent_ecosystem_standards.sh` | 0 | 新增跨 manifest contract test 通过 | `tests/test_agent_ecosystem_standards.sh` | targeted-test | `tasks.md` |
| `rtk scripts/validate-assets.sh --strict` | 0 | strict asset validation 通过并执行新 checker | `scripts/validate-assets.sh` | strict-gate | `checklist.md` |
| `rtk tests/run_all.sh --quick --fail-fast` | 0 | quick suite 18/18 通过 | `tests/run_all.sh` | regression | `tasks.md` |
| `rtk tests/test_no_external_repo_refs.sh` | 0 | 首轮 full failure 的定向修复验证通过 | `tests/test_no_external_repo_refs.sh` | regression-fix | `negative-results.md` |
| `rtk tests/run_all.sh --fail-fast --timing-json /tmp/agent-ecosystem-full-timing.json` | 0 | 修复后 full suite 52/52 通过，elapsed_ms=365989 | `/tmp/agent-ecosystem-full-timing.json` | full-regression | `checklist.md` |
| `rtk scripts/check-doc-sync.sh .` | 0 | 根仓 docs/governance 同步通过 | `reports/agent-ecosystem-standards-absorption-2026-07-14.md` | root-governance | `checklist.md` |
| `rtk scripts/check-adoption-matrix-status.sh .` | 0 | Markdown/JSONL adoption ledger 状态门禁通过 | `subrepos/adoption-matrix.md` | root-governance | `checklist.md` |
| `rtk scripts/check-adk-harden-readiness.sh . --skip-full-suite` | 3 | 首轮发现两条 observe 记录缺 ASW 分层与 intake package | `reports/observe-secondary-intake-packages-2026-07-14.md` | readiness-negative | `negative-results.md` |
| `rtk scripts/check-observe-intake-depth.sh .` | 0 | 补齐 ACP/A2A ASW 与 secondary intake package 后，7 条 observe 记录通过 | `reports/observe-secondary-intake-packages-2026-07-14.md` | root-governance | `checklist.md` |
| `rtk scripts/check-adoption-matrix-structured.sh .` | 0 | 稳定生成器重建 JSONL 后与 Markdown SSOT 同步 | `subrepos/adoption-matrix.jsonl` | root-governance | `checklist.md` |
| `rtk scripts/check-adk-harden-readiness.sh . --skip-full-suite` | 0 | ADK harden baseline、routing、intake、handoff 和 global health 通过；full suite 已独立执行 | `reports/agent-ecosystem-standards-absorption-2026-07-14.md` | readiness | `checklist.md` |
| `rtk scripts/check-all.sh --quick` | 1 | 54/56；仅 strict ADK 子仓因本次未提交改动为 dirty，连带 current-status 检查失败 | `agent-dev-kit/` | aggregate-known | `checklist.md` |
