# 变更提案：adk-v3-1-software-m5-ready

## 背景
- ADK 3.0 已具备本地 release-candidate 能力，但结果有效性只有一次 Codex 固定集证据，Claude、重复试验、并发 writer、真实升级回滚和长期 pilot 尚未形成统一认证链路。
- 当前产品总体保持 M3，不能用更多 fixture 或报告数量代替软件现场证据。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：建立可重放、可恢复、不可伪造的软件侧 M5-ready 评测、并发、发布回收和 pilot 认证控制面。
- 触发证据：`manifests/product_maturity_scorecard.json` 的 D04/D11/D12，以及 3.0 verify report 的 Claude not-run、单次固定集和 single-writer 边界。

## 目标
- 构建软件侧 M5-ready 评测与现场认证链路

## 非目标
- 不实现 LLM runtime、session store、分布式锁或自动外部写入。
- 不在没有 30 天独立 pilot 时把状态提升为 M5。
- 不创建 Git tag、GitHub Release、远端 artifact、跨仓 CI token 或 Knowledge Hub 写入。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：评测、事务互斥、制品回收和成熟度证据适用于所有 target/profile，不绑定业务场景。

## 变更重复性检查
- 已检索 `adk-v3-product-maturity`、runtime pilot、release hardening 与 maturity scorecard。
- 3.0 只提供单次 runtime report 和本地事务负例；本次新增 campaign、统计认证、writer lock、release rehearsal 与长期 ledger，不复制旧 pilot Markdown 门禁。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：根仓 `docs/product-maturity-model.md` 与确认后的软件侧 M5 计划。
- design 决策：本 change `design.md`。
- tasks 追溯关系：本 change `tasks.md`；长期 field gate 由根仓 pilot contract 维护。

## 安装范围与依赖边界
- 安装范围：control plane global-ready；pilot evidence project-bound。
- 依赖边界：Python 3.8+ 标准库、现有 PyYAML 兼容依赖、Codex/Claude 显式 opt-in；不新增 runtime SDK。

## Prompt 回归证据计划
- before/after：60 条锁定 hash 的 baseline/adk 双 runtime campaign，每个 condition 三次 trial。
- 失败样例：逐任务原子记录 error/attempt/usage，汇总字段由 certifier 重算。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：代码/fixture/full regression/local release rehearsal 通过，真实 campaign 在预算内完成，根仓 self pilot 可启动；否则保持原成熟度并记录 blocker。

## 备选方案与取舍
- 方案 A：继续堆叠单次 JSON/Markdown 证据。
- 方案 B：引入 campaign 与 append-only pilot 状态机。
- 选型理由：选择 B；只有原始记录重算、时间门禁和独立 pilot 才能避免自证循环。

## 风险与回退
- runtime 调用成本：执行前计算最坏预算并要求显式 `$150` 上限；可恢复，预算耗尽即停止。
- writer lock 残留：不自动清理，必须用准确 lock ID 显式 clear。
- 3.1 回归：保持 3.0 公共命令兼容；失败时回退提交和本地 artifact，不改 live target。
- 时间证据：self pilot 只能进入 M5-ready，最终 M5 必须等待至少一个独立 repo/operator 的连续 30 天证据。
