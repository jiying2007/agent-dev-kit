# 执行任务：runtime-profile-health-and-compat-cleanup-v1

- [x] 冻结目标、非目标、风险和验收。
- [x] 核实 live active profile、managed-files profile 与 Superpowers source plan 残留。
- [x] 在 Codex source 实现 profile-aware live doctor 并补正反测试。
- [x] 从声明式 source 移除 Superpowers plugin/runtime fallback，并完成 build 与 dry-run。
- [ ] 在 root 同步健康适配器、evidence freshness 和 lock 收口规则。
- [ ] 执行定向、跨仓与 source-to-live 验证；仅在 plan 审核通过后申请 live apply。

## Ownership 与并行冲突检查

- scope_write: `~/codex` runtime tooling/policy/tests 与本 change 工件。
- must_not_touch: 现有 `agent-dev-kit` lifecycle skills、root release evidence、reference subrepos。
- shared manifest、lock 与 live apply 均由主线程串行执行。

## 轻量工件与收敛结论

- 已产出 proposal/design/tasks/checklist/negative-results/verification evidence。
- runtime cleanup 已收敛；lock/evidence 因既有脏工作树保持 deferred。

## Goal Closure

- goal_statement: 让 ADK runtime 的 profile、资产归属和来源证据一致，并去除外部 runtime compatibility。
- required_evidence: profile positive/negative tests、routing/footprint tests、source build/doctor/plan/dry-run、fresh health report。
- retry_budget: 2
- staleness_threshold: 连续两次无新增证据的同类失败。
- stop_condition: pass / replan / blocked。
