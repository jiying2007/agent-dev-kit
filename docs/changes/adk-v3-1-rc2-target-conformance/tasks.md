# 执行任务：adk-v3-1-rc2-target-conformance

| Task | Status | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| T0 baseline-and-contract | complete | 本 change docs | dirty reference repos、live targets | ADK strict、root quick、proposal/design/tasks/state 完整 |
| T1 target-contracts | complete | `targets.py`、target contracts/schema、manifest Agent metadata | runtime roots | contract unit/CLI static check |
| T2 export-unification | complete | `compiler.py`、export CLI/tests | install transaction | golden tree、frontmatter、support files、atomic negative |
| T3 install-unification | complete | `installer.py`、install CLI/tests | external target dirs | plan v2/receipt v3、hash equivalence、rollback/migration |
| T4 manifest-schema-version | complete | schema、manifest JSON/YAML、pyproject、release docs | historical rc.1 evidence | strict validation、unknown-key negative、version sync |
| T5 runtime-smoke | complete-local | target CLI、fixtures/tests/docs | real credentials | static pass；无 runtime 时明确 not-run/exit 2 |
| T6 engineering-gates | complete-local | CI/security/performance/eval control plane、OpenAI/Anthropic freshness gate | paid campaign、remote release | clean-clone/static/security/provenance/perf/eval/docs checks |
| T7 root-governance | complete-local | root status/scorecard/task pack/report；lock 仅在真实 commit 后更新 | reference subrepos | root contract checks、M3/M4/M5 wording一致；未提交边界显式失败 |
| T8 review-and-verify | complete-local | review/verify/evidence docs | commit/push/tag/live apply | ADK full 51/51；root quick 52/56，4 项同源 external boundary |

## 执行契约

- claimant：Codex；用户是范围和外部执行 decision owner。
- retry_budget：同一根因/假设最多 2 次修复；第 3 次前必须更新根因并 replan/split。
- staleness_threshold：每完成一个 task 或 45 分钟更新一次 heartbeat；连续两次无信息增量必须 replan。
- heartbeat：写入 `state.yaml` 的 `last_action`、`next_action`、`blockers`、`evidence_delta`。
- stop_condition：仅 `pass`、`replan`、`split`、`blocked`、`abort`。
- shared contract/schema/manifest/CI 串行修改；本任务不使用子代理。
- 任何 runtime、付费、第二操作者、长期现场、tag/push/release/live apply 均需要单独显式授权。

## required_evidence

- 改前基线与改后定向/全量门禁退出码。
- golden tree、frontmatter、support files、unsupported kind/no partial output。
- export/install 同源 hash、plan tamper/expiry/schema migration、receipt rollback。
- manifest Draft 2020-12 执行证据及至少一个预期 schema failure。
- target runtime smoke 的 `pass` 或真实 `not-run`，不得用 static 结果替代。
- breaking migration、rollback anchor、open blocker 和证据索引。

## Ownership 与并行冲突检查

- scope_write：ADK target/compiler/installer/schema/CLI/test/release/docs，以及根仓 working-candidate 治理文件。
- scope_read：根仓审计报告、rc.1 change artifact、官方 target/spec/CI 文档。
- must_not_touch：dirty reference subrepos、用户 live target roots、`~/.codex`、未经授权的 git history 和远端状态。
- shared contract/schema/manifest/CI 由主线程串行修改；本变更未使用子代理，不存在并行写冲突。

## 轻量工件与收敛结论

- 需求与设计：`proposal.md`、`design.md`。
- 执行与状态：`tasks.md`、`state.yaml`、`checklist.md`。
- 证据与复核：`negative-results.md`、`benchmark.json`、`effect-eval.json`、`verify-report.md`、`review-report.md`、`release-rehearsal.json`。
- 收敛结论：本地实现通过；commit/root lock、真实 runtime、remote CI 和 field certification 为显式外部 blocker。
