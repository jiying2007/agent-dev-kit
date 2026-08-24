# 变更提案：realtime-token-usage-monitor-v1

## 背景
- 现有 `scripts/check-token-budget.sh` 检查的是 Skill、文档和入口规则的静态体积，
  `task-cost` 只在执行前生成预算 receipt；运行中的模型调用尚无平台中立、可流式消费的
  Token 预算控制面。
- 2026-08-24 用户明确要求“动态实时检测 token 消耗”。
- OpenAI Agents SDK 已提供逐次运行 usage、checkpoint usage 和 tracing；LangGraph/Temporal
  的 durable execution 强调可重放状态、幂等副作用与 checkpoint；Anthropic context
  editing 则证明旧工具结果清理必须由可观测阈值驱动。本变更只吸收这些通用合同思想，
  不复制第三方实现或引入运行时依赖。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：Agent 长任务运行期间无法按事件实时看到累计 Token、预算占比、
  消耗速率、预计耗尽时间和确定性动作建议，因而静态预算无法驱动 checkpoint/compact/stop。
- 触发证据（日志/复现/反馈）：`check-token-budget.sh` 只扫描资产；`task_cost.py` 只做执行前
  分类；仓内不存在接受 usage JSONL 的实时监测入口；用户反馈见当前 goal。

## 目标
- 新增平台中立的实时 Token 消耗监测与预算动作建议

## 非目标
- 不直接读取任一厂商私有数据库、会话正文或 prompt。
- 不调用模型、不主动压缩上下文、不自动停止外部进程、不发送网络告警。
- 不用 Token 数评价质量或人员绩效；不承诺厂商账单金额准确性。
- 不替代静态 `token-budget`、性能门禁、trace/eval 或 provider adapter。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（重复事件、snapshot 回退、敏感正文、阈值边界、恢复一致性）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，按 canonical adapter 边界显式 fail closed，不猜测厂商字段语义

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：usage 事件、累计预算、状态等级和动作建议均不依赖平台；provider 映射留在
  runtime adapter，不进入 core。

## 变更重复性检查
- 已检索 `token-context-workflow-optimization-v1`、`check-token-budget.sh`、`task_cost.py`、
  `performance.sh`、`monitoring.sh`、usage eval 归一化逻辑。
- 历史方案覆盖静态体积、执行前成本分类和事后 eval；本次新增运行中 usage event stream、
  幂等恢复、阈值状态机和机器可消费动作，职责不重复。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：`requirements.md` R1-R8。
- design 决策：`design.md` D1-D8。
- tasks 追溯关系：`tasks.md` T1-T6。

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：ADK core/global-ready，是否进入具体 runtime 由后续
  source-to-live 评审决定。
- 依赖边界（脚本/数据/上下文）：仅 Python 3.11 标准库和 typed core；输入为 canonical JSONL；
  不新增第三方包、网络和后台 daemon。

## Prompt 回归证据计划
- before/after 对比输入：同一组 delta/snapshot/duplicate/malformed usage fixtures；before 无入口，
  after 输出逐事件状态和最终 summary。
- 失败样例保留方式：确定性测试覆盖重复 event_id、snapshot 倒退、敏感键、非法阈值和预算耗尽。

## 收敛模式与退出条件
- 当前模式（diagnosis/repro/planning/execution）：planning，change apply 通过后进入 execution。
- 退出条件（进入执行/收敛）：定向测试、strict validate、quick/full 回归、独立 review 与完成门禁
  均有新鲜证据；否则固定为 `needs-fix`。

## 备选方案与取舍
- 方案 A：轮询 Codex/Claude 私有状态库。耦合平台、字段不稳定且扩大敏感数据读取面，拒绝。
- 方案 B：扩展旧 `monitoring.sh` 后台 daemon。该脚本偏主机磁盘运维，状态和安全合同不足，拒绝。
- 方案 C：typed core 流式 JSONL evaluator，由 adapter 提供 canonical usage。选用。
- 选型理由：平台中立、可重放、易测试、默认只读、事件级输出可直接接到长任务执行器。

## 风险与回退
- 风险：不同 provider 的 cache Token 计数语义不同。要求 adapter 明确提供 `total_tokens`，core
  不把 cache 字段重复计入总量。
- 风险：重复/乱序事件导致超计。使用 `event_id` 去重，snapshot 按 `scope_id` 检查单调性。
- 风险：把 prompt 混进事件。拒绝已知正文键，状态文件只保存计数、hash/ID 和时间。
- 回退：移除新增 `token monitor` 路由和 typed module/test；旧命令、manifest 与运行资产不变。
