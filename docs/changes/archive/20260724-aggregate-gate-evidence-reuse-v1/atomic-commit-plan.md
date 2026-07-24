# Atomic Commit Plan：2026-07-24

本计划定义获得用户明确 Git 授权后的原子提交边界。用户已于 2026-07-24
明确授权执行 ADK 4 个、root 1 个本地原子 commit；授权不包含 push、merge、
rebase、source-to-live 或清理既有用户 dirty。

## 前置条件

1. 两仓继续保留当前用户 dirty；禁止 `git add -A`、`git commit -a`、stash、
   reset 或 checkout 清理。
2. 每个提交只使用显式路径；共享文件必须使用 `rtk git add -p -- <path>`，
   并在 commit 前用 `rtk git diff --cached --check` 和
   `rtk git diff --cached --stat` 复核。
3. 每个提交先在当前 working tree 完成定向验证，再通过临时 worktree 或临时
   clone 验证 staged tree；未验证中间态不得标记为 commit-ready。
4. 以下提交标题为建议值，最终仍须满足
   `<type>(scope): <中文动词摘要>`、摘要不超过 50 字且不加句号。

## ADK-1：ecosystem/security

建议标题：`feat(security): 完善 MCP 与 Skill 维护门禁`

整文件范围：

- `docs/reference-adoption-matrix.md`
- `docs/reference-adoption.md`
- `fixtures/agent-ecosystem-standards/pass/local-fixture-bundle.json`
- `fixtures/agent-ecosystem-standards/fail/agentic-skill-security-incomplete.json`
- `fixtures/agent-ecosystem-standards/fail/coding-agent-target-enabled.json`
- `fixtures/agent-ecosystem-standards/fail/mcp-rc-runtime-enabled.json`
- `fixtures/agent-ecosystem-standards/fail/mcp-rc-weak-auth.json`
- `fixtures/agent-ecosystem-standards/fail/skill-maintenance-invalid-digest.json`
- `fixtures/agent-ecosystem-standards/fail/skill-maintenance-missing-digest.json`
- `manifests/external_agent_pattern_contracts.json`
- `manifests/skill_mcp_dependencies.json`
- `manifests/skill_reproducibility_contracts.json`
- `scripts/check-agent-ecosystem-standards.sh`
- `tests/test_agent_ecosystem_standards.sh`
- `docs/changes/archive/20260724-mcp-2026-compat-staging/`
- `docs/changes/archive/20260724-skill-security-maintenance-v1/`

验证：

~~~bash
rtk bash scripts/check-agent-ecosystem-standards.sh --summary-json
rtk bash tests/test_agent_ecosystem_standards.sh
rtk bash scripts/validate-assets.sh --strict
~~~

## ADK-2：repository runtime evidence

建议标题：`feat(eval): 增加真实仓库运行时证据门禁`

整文件范围：

- `manifests/eval_suites.json`
- `manifests/repository_runtime_eval_contract.json`
- `src/agent_dev_kit/cli.py`
- `src/agent_dev_kit/repository_evaluation.py`
- `tests/fixtures/repository_runtime_eval_tasks.jsonl`
- `tests/test_repository_runtime_evidence.sh`
- `docs/changes/archive/20260724-repository-runtime-evidence-v1/`

共享文件 hunk：

- `README.md`：只选 `eval repository plan/certify` 与 `fixture-pass` 说明；
  不选 Python launcher 说明。
- `docs/commands.md`：只选 `eval repository` 命令和 contract 语义；
  不选解释器入口与 `verify-failed` 重试说明。
- `tests/run_all.sh`：只选两处 `test_repository_runtime_evidence.sh`；
  不选 `test_python_launcher.sh`。

验证：

~~~bash
rtk bash tests/test_repository_runtime_evidence.sh
rtk bash scripts/devkit.sh eval repository plan --contract manifests/repository_runtime_eval_contract.json --summary-json
rtk bash tests/run_all.sh --quick
~~~

## ADK-3：field evidence

建议标题：`feat(field): 完善量产现场证据模板`

整文件范围：

- `skills/adk-production-field-readiness/SKILL.md`
- `skills/adk-production-field-readiness/references/pilot-measurement-evidence.md`
- `docs/changes/archive/20260724-field-evidence-v2/`

验证：

~~~bash
rtk bash scripts/validate-assets.sh --strict
rtk bash tests/run_all.sh --quick
~~~

根仓的 Software M5 policy/test/source 与此提交有交叉证据，但不跨仓混入同一
commit；由 Root-1 更新 gitlink 后统一验证。

## ADK-4：terminal maturity 与 change closeout

建议标题：`fix(cli): 收紧 Python 与验证重试边界`

整文件范围：

- `docs/workflows.md`
- `scripts/devkit.sh`
- `scripts/workflow.sh`
- `tests/test_python_launcher.sh`
- `tests/test_workflow.sh`
- `docs/changes/archive/20260724-terminal-maturity-optimization-v2/`
- `docs/changes/archive/20260724-aggregate-gate-evidence-reuse-v1/`

共享文件 hunk：

- `README.md`：只选 Python 3.11/3.12 launcher 与 release evidence 说明。
- `docs/commands.md`：只选解释器入口与 `verify-failed` 可重试说明。
- `tests/run_all.sh`：只选两处 `test_python_launcher.sh`。

验证：

~~~bash
rtk bash tests/test_python_launcher.sh
rtk bash tests/test_workflow.sh
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/run_all.sh --quick
~~~

ADK-4 后必须确认 `rtk git status --short` 没有漏掉本轮 ADK 资产；若仍有未知
dirty，停止，不把它并入提交。

## ADK clean-HEAD 门禁

四个 ADK commit 均形成后，在 clean HEAD 上执行：

~~~bash
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/run_all.sh
rtk bash scripts/devkit.sh security check --summary-json
rtk bash scripts/devkit.sh release check --summary-json
~~~

当前主机 Python 3.8.10 只能提供 development evidence。release evidence 应使用
受支持的 Python 3.11/3.12 或受控 local-CI parity，并设置
`ADK_REQUIRE_SUPPORTED_PYTHON=1`。

## Root-1：M5、terminal 与 aggregate integration

建议标题：`feat(governance): 闭环 M5 与聚合门禁证据`

整文件范围：

- `.github/workflows/ci.yml`
- `README.md`
- `docs/product-maturity-model.md`
- `docs/software-m5-certification-plan.md`
- `manifests/product_maturity_scorecard.json`
- `manifests/software_m5_policy.json`
- `scripts/README.md`
- `scripts/check-all.sh`
- `scripts/check-architecture-reports.sh`
- `scripts/check-current-status-consistency.sh`
- `scripts/check-doc-sync.sh`
- `scripts/check-root-regression.sh`
- `scripts/check-workspace-entrypoints.sh`
- `scripts/lib/same-run-evidence.sh`
- `tests/run_all.sh`
- `tests/test_architecture_reports.sh`
- `tests/test_check_all_contract.sh`
- `tests/test_current_status_consistency.sh`
- `tests/test_product_maturity_contracts.sh`
- `tests/test_same_run_evidence.sh`
- `tests/test_software_m5_certification.sh`
- `tools/codex_assets/software_m5.py`
- `agent-dev-kit` gitlink，仅指向完成 ADK-1 至 ADK-4 后的精确 clean HEAD。

以下默认不进入 Root-1：

- `fixtures/reference-repository/removal/pass/removal-plan.json`
- `manifests/external_practice_sources.json`
- `subrepos/adoption-matrix.jsonl`
- `subrepos/adoption-matrix.md`
- `subrepos/dirty-baseline.tsv`
- `subrepos/registry.csv`
- 三个既有观察型参考子仓的 dirty gitlink
- `.cache/`、`hermes/`、`hermes_data/`
- `reports/external-practice-*`、`reports/reference-*`、`reports/spec-kit-*`

`reports/terminal-maturity-*` 与
`reports/aggregate-gate-evidence-reuse-quick-2026-07-23.json` 是 dirty-worktree
验证证据，默认保留为审查产物，不和源码提交混合；若 owner 要求入库，应单独
形成 evidence commit，并先检查路径、时间戳和脱敏。

验证：

~~~bash
rtk tests/run_all.sh
rtk scripts/check-current-status-consistency.sh . --summary-json
rtk scripts/check-evidence-bundle.sh . --summary-json
rtk scripts/check-subrepo-state.sh .
rtk scripts/check-workspace-entrypoints.sh .
rtk scripts/check-all.sh --full --result-json reports/check-all-full-clean.json
rtk bash ~/codex/scripts/final-ready.sh
~~~

## 分支与远端边界

- 当前两仓都在 `main`，不存在可 local-merge 的 feature branch。
- 本轮只授权本地 commit；执行完上述原子提交和 clean gates 后停止，不触碰
  远端。
- 未授权创建分支、push、PR、merge、rebase 或 source-to-live。
- 若授权 PR，还需单独确认目标远端、分支名、push 与 PR 权限。
- discard 会丢失混合 dirty，当前禁止。
