# 执行任务：20261117-task-diagnostics

- [x] 需求确认与边界冻结：requirements.md/design.md。
- [x] TASK-001：在既有 Trace/import/CLI 实现显式诊断及验收反例；verify：`rtk proxy python -m unittest discover -s tests -p test_trace_summary.py` 与 `rtk proxy python -m unittest discover -s tests -p test_task_evidence.py`。Trace 18、Task 37 项实际通过，原 RED 保留。
- [x] TASK-002：增强既有 runbook 和 AAR 按需引用并同步既有模板；verify：`rtk proxy bash tests/test_skill_content.sh`、`rtk proxy bash tests/test_skill_sop_quality.sh`、`rtk proxy bash tests/test_profile_context_footprint.sh`。Skill content 211、SOP 22、Profile 6 项实际通过；clean candidate strict 仍由 TASK-003 统一执行。
- [ ] TASK-003：统一 11.4.0 元数据，完整回归、export、release check、独立 Spec/Quality、受保护发布和 Root 源码晋级；verify：`bash tests/run_all.sh`、`bash scripts/devkit.sh validate --strict`、`bash scripts/devkit.sh release check` 及当前提交 CI/Release 实际回执。

## Ownership 与并行冲突检查

- scope_write：独立 C1 实现者独占 trace_summary.py、task_evidence.py、evaluation_cli.py、两个对应测试及既有 runbook/AAR reference、与其字节一致的 templates/memory/after-action-review.md；不得修改 requirements/design。
- scope_read：既有 Trace/RunEvidence/TaskEvidence、安全读取、repository certification 及来源审查。
- coordinator 独占 change evidence、manifest、版本文件与共享发布配置；C2 实现者独占 reducer 与 execution-policy/target-contract 回归。共享文件不得并写。

## 轻量工件与收敛结论

- 需求梳理工件：requirements.md 与 proposal.md canonical contract。
- task checklist 工件：本文件与 checklist.md。
- 执行反馈/验收记录工件：verify-report.md 与 evidence 索引在真实运行后生成。
- 当前为 execution；代码、完整测试、独立审查及源码发布回执齐备后收敛。当前无宿主及模型效果证据，保持 not-measured。
