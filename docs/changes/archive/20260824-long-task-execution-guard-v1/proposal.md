# 变更提案：long-task-execution-guard-v1

## 背景
- 长任务 heartbeat/retry/staleness/checkpoint/stop condition 已在 Skill、runbook 和 fixture contract 中声明，
  但没有对当前任务 state 执行的 typed runtime-neutral gate。
- 新增 realtime Token monitor 后，其 action 仍未接入长任务完成/恢复判断。

## 问题陈述（单问题）
- 只解决：把长任务 anti-stall、completion evidence 与 Token action 变成一个可机器验证的守卫。
- 证据：源码搜索仅命中模板、manifest fixture validator 和 embedded pilot，没有通用 live state evaluator。

## 目标
- 新增可机器验证的长任务心跳重试证据与 Token 动作守卫

## 非目标
- 不运行任务、不写 state、不调度 agent、不自动 compact/stop、不替代 workflow verify/review。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（时间确定性、假 completed、Token 建议越权、敏感 state 回显）
- [x] 已明确验证命令与通过标准
- [x] 现有模板与外部 durable execution 证据充分

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：平台中立 state validation；不绑定 provider/runtime。

## 变更重复性检查
- 已检索 harness-loop contracts、goal contracts、long-task template、runner contracts、locking/readiness。
- 现有实现验证静态 fixture 或特定 target，不接受当前任务 state；本次复用字段而非重建方法论。

## Breaking Change 检查
- [x] 否：additive CLI/module/test/docs
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements：`requirements.md` R1-R7。
- design：`design.md` D1-D6。
- tasks：T1-T5。

## 安装范围与依赖边界
- 安装范围：ADK core/global-ready。
- 依赖边界：Python standard library、JSON state；无网络/第三方依赖。

## Prompt 回归证据计划
- before：无 execution 命令；after：fresh/stale/retry/token/completion fixtures。
- 失败样例：deterministic Python/CLI tests。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：定向、quick/full、review 和 change verify 通过。

## 备选方案与取舍
- A：继续仅靠 Markdown advisory，拒绝。
- B：typed pure evaluator + thin CLI，选用。
- 理由：可复放、可 gate、不会扩大副作用。

## 风险与回退
- 风险：action 被误解为授权；输出明确 `advisory_only=true`，调用方另行审批。
- 回退：删除新 module/command/test/docs；现有模板与 monitor 不变。
