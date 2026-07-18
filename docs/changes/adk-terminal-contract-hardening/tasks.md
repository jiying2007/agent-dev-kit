# 执行任务：adk-terminal-contract-hardening

| Task | Status | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| T0 planning-and-baseline | completed | 本 change 工件、根执行记录 | 用户 dirty 参考仓、git history | change governance、status/diff、改前负例 |
| T1 truthful-performance-gate | completed | 根性能包装器、相关测试/文档 | 性能预算数值 | 超预算负例失败、预算内正例通过、真实 quick strict |
| T2 copy-install-contract | completed | manifest JSON/YAML、schema、docs、tests | installer transaction 实现 | strict/schema/install/docs tests |
| T3 supported-security-baseline | completed | pyproject、CI、兼容说明、质量测试 | 凭证、远程 workflow 状态 | build metadata、security/release、CI contract tests |
| T4 integration-regression | completed | evidence/review 工件 | live runtime、远端、field ledger | targeted、quick/full、root applicable checks |
| T5 completion-review | completed | review/verify/state | commit/push/tag | blocker/major 复核、final-ready、open items |
| T6 controlled-local-ci-continuation | completed | local parity runner、PEP 639 metadata、waiver/evidence | 远端 CI 状态、release/Software M5/field 声明 | Python 3.11/3.12 container matrix、负例、复审 |
| T7 version-commit-rehearsal | in_progress | RC3 版本合同、source commit、本地 rehearsal 与证据 | push、tag、publish、live apply、历史 RC2 证据 | exact-commit build、可复现 SHA、rc.2 → rc.3 rollback/fallback |

## Ownership 与并行冲突检查

- scope_write：本 change 工件；ADK manifest/schema/install/security baseline/tests/docs；根性能包装器和执行报告。
- scope_read：根/ADK AGENTS、README、成熟度模型、旧 rc.2 change、现有测试与 Hub reviewing validation。
- must_not_touch：现有 dirty reference subrepos、`~/codex`、`~/.codex`、history rewrite、远端和真实 runtime 凭证。
- shared contract/schema/manifest/CI 串行修改；本任务不使用子代理。

## 执行与恢复合同

- claimant：Codex；verifier：完成前验证门禁和机械测试。
- retry_budget：同一根因最多 2 次；继续失败则更新假设并 replan/split。
- staleness_threshold：45 分钟或每完成一个 task 更新 heartbeat。
- stop_condition：pass、replan、split、blocked、abort。
- breaking change：Python 最低版本提升；必须有迁移/回滚说明。
- required_evidence：至少一个改前失败、对应改后通过、定向回归、full、根集成和开放 blocker。

## 轻量工件与收敛结论

- 需求与设计：`proposal.md`、`design.md`。
- 状态与任务：本文件、`state.yaml`、`checklist.md`。
- 负结果与证据：`negative-results.md`，后续补 `verification-evidence.md`、`review-findings.md`、`review-report.md`。
- 当前结论：本地合同修复、受控 CI waiver 替代证据和 source/test 复审已完成；外部 runtime、remote CI、candidate release rehearsal、独立操作者与 field certification 继续阻断 release/terminal 声明。
