# 变更提案：field-evidence-v2

## 背景
- Software M5 已要求独立仓库、两名 human operator、30 天跨度和完整 field event，但 workload 只记录 task count/success rate，尚不能审计任务自选偏差、人工基线和并发 Agent 下的真实时间。
- METR/HCAST 与生产率研究表明，任务/参与者选择和不可靠时间测量会显著扭曲结论。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：现场试点证据无法区分真实生产率改善与任务选择、人工估时或并发 Agent 造成的测量偏差。
- 触发证据：当前 policy 没有 task preregistration/disposition、human baseline、wall-clock/human-active/agent-active time 和 concurrent-agent 指标。

## 目标
- 新增 `task_selection_recorded` 与 `human_baseline_recorded` 必需 field event。
- 扩展 workload 指标，记录 preregistered/rejected task、wall-clock、human-active、agent-active 和 concurrent-agent peak。
- 强制独立 reviewer 的 review event 记录 selection-bias assessment 与时间测量方法。
- 更新 M5 certifier、测试、计划文档和 field-readiness evidence template。

## 非目标
- 不生成或回填 30 天现场事件，不新增第二 operator，不伪造独立仓库。
- 不降低成功率、时长、仓库或 reviewer 门槛。
- 不记录 operator 姓名、邮箱、prompt、客户数据或绩效评分。

## 上下文充分性检查
- [x] 已明确 event/metric 输入输出
- [x] 已识别 PII、选择偏差、并发计时和历史事件兼容风险
- [x] 已明确定向与根仓 full gate
- [x] 真实 field evidence 不足时保持 blocked

## Core/Optional 边界检查
- [x] Software M5 认证 contract 属于 core
- [x] 具体项目事件属于 project-bound
- 归属结论：validator/policy 是根仓 control plane；Skill 只增加通用 evidence guidance。

## 变更重复性检查
- 已检索 `software_m5.py`、policy、ledger、field event chain 和 `adk-production-field-readiness`。
- 本次扩展现有 append-only event 模型，不建立第二本 ledger。

## Breaking Change 检查
- [x] 否：RC 尚未认证，新增要求只提高未来 certification 证据；现有历史事件保持可读
- [ ] 是：涉及兼容性破坏

## Spec 链路检查
- requirements 基线：本提案与外部实践候选报告 3.7 节。
- design 决策：本 change `design.md`。
- tasks 追溯关系：本 change `tasks.md`。

## 安装范围与依赖边界
- 安装范围：root control plane global-ready；event project-bound。
- 依赖边界：标准库和现有 ledger/event chain；不新增 telemetry SDK 或外部写入。

## Prompt 回归证据计划
- 不修改 runtime prompt。
- 正负对比：旧最低 workload metric 与 v2 完整 metric；缺 selection/baseline/time/reviewer assessment 均 fail closed。

## 收敛模式与退出条件
- 当前模式：planning。
- 退出条件：policy/validator/tests/docs 通过；认证状态继续 blocked 直到真实试点满足条件。

## 备选方案与取舍
- 方案 A：只在文档建议记录更多指标。
- 方案 B：把少量关键指标纳入不可弱化机器 contract。
- 选择 B：这些字段经常遗漏且遗漏会导致高成本错误结论，符合 Gate 条件。

## 风险与回退
- 风险：事件 schema 膨胀、历史事件失效、PII 泄露、机械指标被当绩效 KPI。
- 控制：只约束 qualifying independent pilot，匿名 operator ID，明确禁止绩效用途。
- 回退：恢复 policy v1 metric set 和 validator 常量；保留已追加事件为历史，不改写 hash chain。
