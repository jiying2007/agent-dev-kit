# Delivery Closeout：2026-07-24

## 收口预检基线

- Root：`main`，HEAD `7b3ef8523b1c77f8cc77d70e63702366a2df3c66`，
  相对 `origin/main` ahead 2。
- ADK：`main`，HEAD `9a8f735928976cf2efac81dd167911664bf6c490`，
  相对 `origin/main` ahead 11。
- 两仓都不是独立 feature branch；`merge-base HEAD main` 等于各自 HEAD，
  因此当前不存在可执行的 local merge。
- 两仓工作树均为混合 dirty：包含本轮 6 个 review-passed change、共享文件
  hunks、参考仓治理产物和既有用户子仓/未跟踪目录。

## 本轮 change lifecycle

以下 6 个 change 已完成 requirements/design/tasks/build/review/test，并已按
`review-passed -> archive` 收口：

1. `field-evidence-v2`
2. `mcp-2026-compat-staging`
3. `repository-runtime-evidence-v1`
4. `skill-security-maintenance-v1`
5. `terminal-maturity-optimization-v2`
6. `aggregate-gate-evidence-reuse-v1`

归档目录分别为：

- `docs/changes/archive/20260724-field-evidence-v2`
- `docs/changes/archive/20260724-mcp-2026-compat-staging`
- `docs/changes/archive/20260724-repository-runtime-evidence-v1`
- `docs/changes/archive/20260724-skill-security-maintenance-v1`
- `docs/changes/archive/20260724-terminal-maturity-optimization-v2`
- `docs/changes/archive/20260724-aggregate-gate-evidence-reuse-v1`

归档只移动 change artifact，不自动 stage、commit、push、merge、tag 或执行
source-to-live。

## Dirty 归属与共享触点矩阵

| Pack | 主要范围 | 共享触点 | 建议原子边界 |
|---|---|---|---|
| ADK ecosystem/security | MCP/Skill contracts、ecosystem checker/tests/fixtures、reference docs | checker、test、pass fixture | MCP + Skill Security 合并为一个提交，避免拆开中间态失配 |
| ADK repository runtime | repository evaluator/contract/CLI/test/eval suite/docs | `README.md`、`docs/commands.md`、`tests/run_all.sh` | repository runtime 独立提交，但只 stage 对应 hunks |
| ADK field evidence | field-readiness Skill/reference 与 change artifact | root M5 policy/source/test | ADK Skill 提交与 root M5 集成提交分别落地并交叉引用 |
| ADK terminal/aggregate | Python launcher、verify retry、docs/tests、两份 terminal change artifact | `README.md`、`docs/commands.md`、`tests/run_all.sh` | 只 stage launcher/retry hunks；aggregate helper 位于 root，不混入 ADK runtime pack |
| Root M5 integration | field/repository blockers、scorecard、certifier/tests/docs | M5 policy/source/test 同时承载两个 change | field + repository + maturity 作为一个已联合验证的根提交 |
| Root aggregate gates | root test runner、check-all、same-run evidence、workspace consumer、CI/docs/tests | `check-all.sh` 同时承载 terminal 与 reuse | 与 root M5 integration 同提交或紧邻提交；不能只提交 reuse 后遗漏 runner |
| Root reference/intake | registry/adoption/baseline/external-practice reports | removal fixture、registry/matrix | 与性能/M5 提交分离，由对应 reference change/owner 决定 |
| Existing user state | observe 子仓 dirty、`hermes/`、`hermes_data/`、其他 reports | 根 status/fingerprint | 不清理、不回退、不纳入优化提交 |

## 精确提交顺序（本地 commit 授权已收到）

1. ADK ecosystem/security pack。
2. ADK repository runtime pack。
3. ADK field evidence pack。
4. ADK terminal/aggregate governance pack。
5. 在 ADK clean HEAD 上重跑 ADK full、security、release、harden。
6. Root reference/intake pack 由其 owner 独立决定；不与优化提交混合。
7. Root M5 + terminal + aggregate integration pack，并更新 `agent-dev-kit`
   gitlink 到第 4 步的精确 HEAD。
8. 在 root clean state 重跑 quick/full、current-status、evidence-bundle、
   subrepo-state、workspace aggregate。
9. 若 ADK mapped assets 的提交包含 field-readiness Skill，获得 owner 授权后
   才执行 `agent-dev-kit -> ~/codex -> ~/.codex` source-to-live 链路。

共享文件 `README.md`、`docs/commands.md`、`tests/run_all.sh` 必须按 hunk stage；
不能使用整文件 `git add` 把 repository runtime 与 terminal launcher 混成错误
的中间提交。

## 收尾选项

| 选项 | 当前可用性 | 结论 |
|---|---|---|
| local-merge | 不可用 | 当前已在 `main`，没有 feature branch 可合并 |
| create-pr | 暂不可用 | 需要先创建分支、原子 commit，并获得 push/PR 授权 |
| keep | 可用 | 当前默认选择；保留工作树，等待精确 Git 授权 |
| discard | 禁止 | 未收到明确丢弃确认，且包含用户既有变更 |

## 验证与阻塞

- ADK working-tree full、双 Python quick、harden、security/release 证据已通过；
  每个 change 均为 `review-passed`。
- 归档后 6/6 change governance 检查通过，旧活动路径引用为 0；
  `tests/test_no_external_repo_refs.sh` 通过。
- 归档后 `scripts/devkit.sh validate --strict` 通过，
  `tests/run_all.sh --quick` 为 20/20；当前系统 Python 3.8.10 的结果仅为
  development evidence，不作为 release evidence。
- Root 与 ADK 的 `git diff --check` 均通过，root `check-doc-sync.sh` 通过。
- Root final full：55/59，aggregate reuse 6，性能目标闭环。
- 四个 root failure 共享 strict ADK dirty 根因；只有 ADK 形成真实 clean commit
  后才能消除，不能通过 baseline、跳过检查或历史 result cache 解决。
- `final-ready` PASS；Session Coach 的 THREAD_LONG/CTX_PRESSURE 只要求换线程，
  不改变源码验证结果。
- 本地原子 commit 已获授权，但仍禁止声称“可合并/可发布”；每个中间态必须
  独立验证，且 push、PR、merge、rebase 与 source-to-live 均不在授权范围。

## Knowledge Hub 与长期事实

- Hub 预检结果为路由歧义，命中项均为 `reviewing` provisional；只作历史
  provenance，不作为当前工作树权威。
- 当前 source evidence HEAD 陈旧，且没有 Knowledge Hub source-write 授权。
- 本轮不写新的 Hub candidate；待双仓 commit hash 与 clean full 产生后，再以
  不可变 commit 和新鲜验证结果生成 release/validation candidate，避免 provisional
  dirty workspace 成为长期事实。

## Final Status

- Source implementation：review-passed。
- Change lifecycle：archived（6/6，归档后治理与 quick regression 通过）。
- Git delivery：local-only atomic commit execution authorized；remote delivery 未授权。
- Source-to-live：blocked on clean ADK commit and explicit owner authorization。

## Authorized Execution Update

- Human owner 于 2026-07-24 明确授权按
  `atomic-commit-plan.md` 执行 ADK 4 个、root 1 个本地原子 commit。
- ADK-1：`40246e4`，ecosystem/security staged tree 验证通过。
- ADK-2：`172f964`，repository runtime staged tree quick 19/19。
- ADK-3：`bb86bff`，field evidence staged tree quick 19/19。
- 本文件作为 ADK-4 提交内容，无法自引用其最终 commit hash；ADK-4 与 Root-1
  hash 由 root 提交后的最终交付记录给出。
- 授权仍明确排除 push、merge、rebase、source-to-live 和既有用户 dirty 清理。
