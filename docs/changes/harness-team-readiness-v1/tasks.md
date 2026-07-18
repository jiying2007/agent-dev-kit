# 执行任务：harness-team-readiness-v1

- [x] T1 需求确认与边界冻结；verify：`rtk agent-dev-kit/scripts/check-change-governance.sh agent-dev-kit/docs/changes/harness-team-readiness-v1`
- [x] T2 实现 contract-driven readiness core、CLI 与报告渲染；verify：正向、证据不足、敏感配置三类命令输出符合状态合同
- [x] T3 增加正负 fixtures 和回归测试；verify：`rtk agent-dev-kit/tests/test_harness_readiness.sh`
- [x] T4 接入 capability health，校准 canonical change/Harness 文档；verify：capability 与 docs CLI alignment 测试通过
- [x] T5 完成独立 review、quick/full gate、Knowledge Hub reviewing candidate 和交付收口；verify：Evidence Index 可追溯且没有 blocker/major 未闭环
- [x] T6 修复否定权限文本被识别为完整边界证据；verify：反面说明不能使 `tool_and_permission_boundary=pass`
- [x] T7 增加验证时间未来拒绝与 freshness window；verify：未来和过期日期均产生稳定 blocker，窗口内日期保持有效
- [x] T8 重新执行独立 review、Harness 定向测试和 full regression；verify：HR-007 至 HR-010 fixed且无新 blocker/major

## Ownership 与并行冲突检查

- 写入范围（scope_write）：`agent-dev-kit` 中本 change 工件、readiness Python/manifest/fixtures/tests、CLI、capability contract、Harness/change/commands/usage/README 文档及旧 quality-gates 兼容包装层。
- 读取范围（scope_read）：根与 ADK AGENTS、官方来源记录、既有 Harness/goal/capability/change 合同、Knowledge Hub 路由结果、相关测试。
- 是否与其他任务冲突（同文件/同 contract/同配置）：未并行派发；`agent-dev-kit` 实施前为 clean。根仓已有 unrelated dirty gitlink 与未跟踪目录，不进入写入范围。

## 轻量工件与收敛结论

- 需求梳理工件：`proposal.md`。
- task checklist 工件：本文件 T1 至 T5。
- 执行反馈/验收记录工件：`negative-results.md`、`baseline-report.md`、`review-findings.md`、`verification-evidence.md`、后续 workflow `verify-report.md` 与 `review-report.md`。
- 收敛结论或阻塞说明：2026-07-18 反例审计发现的权限否定语义、future/stale、历史评估时钟与嵌套 ownership 假阳性均已修复并复审；本地 change 恢复 pass。原公众号 URL、多仓试点和 field evidence 继续作为开放项，不授权 active promotion 或 terminal 声明。
