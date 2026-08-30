# 执行任务：adk-platform-convergence-v1

- [x] T0 需求确认、边界和完成证据冻结（R1-R10）
- [x] T1 routing IR、negation、abstain、metamorphic/multi-turn 和单一 matrix 投影（R1）
- [x] T2 core Profile 中立化和 capability closure（R2）
- [x] T3 Runtime Control task-mode applicability 与 goal intake provenance（R3）
- [x] T4 官方来源 freshness 与 Python 工具链（R4）
- [x] T5 Workflow IR、权限不变量与正文同步门禁（R5）
- [ ] T6 Runtime Adapter SPI 和首个 native conformance（R6）：SPI/receipt 已完成；认证就绪后最小 Claude smoke 无结果并有界终止，native 仍 not-run
- [ ] T7 Trace/effect eval 扩展（R7）：schema/validator/explicit emitter/Run Evidence/完整 population comparator 已完成；automatic adapter 与真实 baseline/ADK runtime campaign 未完成
- [ ] T8 Agent/Skill/Profile 价值合同（R8）：contract/receipt-driven measurement API 已完成；canonical usage 仍 not-measured，无真实 runtime/field receipt
- [ ] T9 维护性与 Evidence Graph（R9）：Graph 与三类 evidence metric evaluator 已完成；当前 reviewed churn/owner/inactive source 均 unavailable
- [ ] T10 双 runtime/独立仓/双 operator/30 天 field（R10）：真实外部证据未完成
- [ ] T11 交叉审查、全量验证和最终状态对账：provenance/runtime/campaign/harden 缺口已修复；正式 4.0 artifact continuity、最终 clean candidate commit/build、R6/R10 仍未收口

## Ownership 与并行冲突检查
- 写入范围（scope_write）：T1 独占主 manifest/schema/matcher；T3 独占 runtime_control；T4 独占 official docs；
  主 Agent 独占 umbrella change、Profile 整合、Workflow/Evidence Graph 和最终状态。
- 读取范围（scope_read）：全仓规则、manifest、typed core、tests、reports 和官方来源。
- 是否与其他任务冲突（同文件/同 contract/同配置）：主 manifest/Profile 必须等待 T1 handoff 后串行整合；其余首轮可并行。

## 轻量工件与收敛结论
- 需求梳理工件：`requirements.md`、综合设计评估报告。
- task checklist 工件：本文件 T0-T11。
- 执行反馈/验收记录工件：`verification-evidence.md`、`review-report.md`、`negative-results.md`。
- 收敛结论或阻塞说明：R1-R5 已实现；R7-R9 本地 evaluator/emitter 已实现但真实 runtime/field 数据仍 open；R6/R10 保持 open；
  supported full parity、checksum-bound rehearsal、R6/R10 未完成，不把本地候选冒充 release/field/M5 evidence。
