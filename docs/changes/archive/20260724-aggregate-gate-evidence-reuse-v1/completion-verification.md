# Completion Verification：2026-07-24

## Scope Summary

- 验证范围：六个已 review-passed change 的 lifecycle 归档、ADK working-tree
  回归、root regression、双仓格式/文档治理、严格子仓状态和 Git 交付边界。
- 非目标：未经授权的 stage/commit/push/merge/rebase、用户 dirty 清理、
  `agent-dev-kit -> ~/codex -> ~/.codex` source-to-live，以及真实 30 天 field
  pilot/runtime campaign 的替代或伪造。

## Completion Claim Audit

| Claim | Verifier 结论 | 依据 |
|---|---|---|
| 六个 change 已完成 lifecycle | `pass` | 六个目录已迁入 `docs/changes/archive/20260724-*`，6/6 governance pass |
| ADK working-tree 实现通过定向回归 | `pass-development` | strict validate pass，quick regression 20/20；Python 3.8.10 不是 release evidence |
| Root 回归通过 | `pass-working-tree` | 新鲜 root regression 17/17 |
| Root full 已完全通过 | `rejected` | 最新完整门禁仍为 55/59；不得把局部 pass 升级为 full pass |
| 双仓可提交/可合并/可发布 | `rejected` | 两仓均在 `main` 且 mixed dirty；没有 Git 授权，strict ADK 子仓仍 dirty |
| Software M5 已认证 | `rejected` | `software_m5_certified=false`，真实 campaign、独立仓与 30 天 field evidence 未满足 |
| 运行资产已刷新 | `rejected` | 未执行 source-to-live；无 clean ADK commit 和 owner 授权 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash scripts/check-change-governance.sh docs/changes/archive/<date-change>`，逐个执行 | 0 | 6/6 archived change governance pass | 六个 `docs/changes/archive/20260724-*` 目录 | Workflow | lifecycle archive |
| `rtk bash tests/test_no_external_repo_refs.sh` | 1 | 原子计划包含外部仓专名，被门禁拒绝 | 本文件“Negative Gates” | Skill/docs | `atomic-commit-plan.md` |
| 修复后 `rtk bash tests/test_no_external_repo_refs.sh` | 0 | 外部仓专名抽象化后 pass | `atomic-commit-plan.md` | Skill/docs | docs governance |
| `rtk bash scripts/devkit.sh validate --strict` | 0 | strict validation pass；Python 3.8.10 development-only warning | `delivery-closeout.md` | Agent/Skill | ADK assets |
| `rtk bash tests/run_all.sh --quick`（ADK） | 0 | 20/20 pass | `delivery-closeout.md` | Workflow | ADK quick regression |
| `rtk tests/run_all.sh --timing-json reports/terminal-maturity-root-tests-closeout-2026-07-24.json` | 0 | 17/17 pass，78.602 秒 | `../reports/terminal-maturity-root-tests-closeout-2026-07-24.json`（root） | Workflow | root regression |
| `rtk git diff --check`（ADK 与 root） | 0 | 两仓差异格式 pass | `delivery-closeout.md` | Repository | working tree |
| `rtk scripts/check-doc-sync.sh .`（root） | 0 | docs/governance sync pass | `delivery-closeout.md` | Workflow | root docs |
| `rtk scripts/check-current-status-consistency.sh . --summary-json` | 1 | `current subrepo state is not pass`；strict ADK dirty | 本文件“Negative Gates” | Workspace | current status |
| `rtk scripts/check-subrepo-state.sh .` | 1 | clean=4、known-dirty=3、unexpected-dirty=1；唯一 unexpected 为 ADK 36 changes | 本文件“Negative Gates” | Workspace | subrepo policy |
| `rtk scripts/check-all.sh --full --result-json ...`（最终实现 working tree） | 1 | 55/59；四项共享 strict ADK dirty 根因；same-run reuse=6 | `delivery-closeout.md` | Workspace | aggregate gate |

说明：根仓 17/17 timing artifact 的实际路径为
`reports/terminal-maturity-root-tests-closeout-2026-07-24.json`。上表使用相对语义
标识，避免把本机绝对路径写入可迁移文档。

## Negative Gates

1. 文档门禁曾正确拒绝原子提交计划中的三个外部参考仓专名；修复为抽象类别后
   同一测试通过。这证明 deny path 有效，不把首次失败隐藏为“始终通过”。
2. 新鲜 `check-current-status-consistency` 返回
   `current subrepo state is not pass`。
3. 新鲜 `check-subrepo-state` 返回 `unexpected_dirty=1`，唯一 unexpected dirty
   是 strict `agent-dev-kit`（36 changes）；三个 observe 子仓均匹配已登记
   known-dirty baseline。
4. 该失败只能由形成受审查的 ADK clean commit 消除；不得通过改 baseline、
   跳过 strict 检查或复用历史缓存绕过。

## Review Status

- Implementation review：blocker=0，major=0，minor=0；六个 change 均已
  `review-passed` 后归档。
- Delivery review：blocker=1（缺少明确 Git commit/branch 授权）。
- Release review：blocker 保留；缺少受支持 Python release evidence、真实
  runtime/repository campaigns、独立 operator/repository 和 30 天 field evidence。

## Compatibility and Rollback

- 无默认 breaking CLI change：旧 Python 默认产生显式 development-only warning；
  只有设置 `ADK_REQUIRE_SUPPORTED_PYTHON=1` 才 fail-fast。
- `verify-failed -> verify retry` 放宽恢复路径，不破坏既有成功状态机。
- 新增 repository runtime/M5 blocker 会拒绝过去可能被误判为完整证据的
  clean-room fixture；这是有意的安全收紧。迁移方式是提供 owner-approved real
  repository task、digest-pinned adapter 和完整 report，而不是关闭 blocker。
- same-run evidence 只在同一父进程、相同 workspace fingerprint、成功 producer
  和允许的 TTL 内复用；不满足条件自动回退真实执行。
- 当前未形成 commit、未刷新运行资产，因此回退方式是保留 mixed working tree
  并由 owner 审查，不执行破坏性 reset/checkout。授权提交后应以原子 commit 为
  回退单位。

## Final Gate Result

- Change lifecycle：`pass`。
- Working-tree implementation verification：`pass-development`。
- Git delivery / clean full gate：本文件首次核验时为 `needs-fix`；后续 human
  owner 已明确授权 `atomic-commit-plan.md` 中的 4+1 个本地原子 commit，
  当前进入逐提交 staged-tree 验证和 clean full gate 阶段。
- Source-to-live / release / Software M5 certification：`blocked-by-design`，
  当前不得放行或声称完成。

## Authorized Execution Update

- 授权范围：ADK 4 个、root 1 个本地原子 commit。
- 已完成并独立验证：ADK-1 `40246e4`、ADK-2 `172f964`、
  ADK-3 `bb86bff`。
- 未授权：push、PR、merge、rebase、source-to-live、既有用户 dirty 清理。
- ADK-4 和 Root-1 的最终 hash、clean 状态与 full gate 结果由后续 root
  交付记录补充；本文件不伪造自引用 commit hash。
