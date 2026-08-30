# 变更提案：adk-platform-convergence-v1

## 背景
- 2026-08-30 综合评估确认 ADK 控制面能力完整，但路由多 SSOT、core 嵌入式混入、Runtime Control
  工件适用性、来源 freshness、Workflow 执行语义、真实 runtime/field 和维护性仍未闭环。
- 当前 root quick 为 53/55，strict validate 因 28 条官方来源过期失败；组合否定路由存在可复现误命中。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：将“合同数量成熟”收敛为“单一 IR、最小 core、真实运行和可回滚证据成熟”。
- 触发证据（日志/复现/反馈）：`reports/llm-agent-adk-comprehensive-design-assessment-2026-08-30.md`、
  strict/quick gate、routing edge-case 命令和 Software M5 blocker。

## 目标
- 收敛 ADK 路由、Profile、运行控制与真实证据架构

## 非目标
- 不实现通用 Agent runtime、scheduler 或外部 durable engine。
- 不默认启用 MCP/Hook/Plugin/Automation，不执行未授权 live/source-to-live。
- 不用 fixture 替代 native runtime 或 field evidence。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [x] 属于场景化能力（optional）
- 归属结论与理由：IR、编译、路由、验证和 adapter SPI 属于 core；嵌入式、field、runtime-specific
  binding 属于 Profile/optional/target adapter。

## 变更重复性检查
- 已检索是否存在相同 change-id/同类方案：无同名 change；已有 intent boundary、runtime control、M5 readiness 等局部方案。
- 若有历史方案，本次差异与必要性：本次以 2026-08-30 评估为统一目标闭环，消除局部合同彼此平行演进。

## Breaking Change 检查
- [ ] 否：不涉及兼容性破坏
- [x] 是：routing/profile/workflow/runtime schema 可能变化，必须提供 compiler migration、兼容窗口和 rollback。

## Spec 链路检查
- requirements 基线：`requirements.md` R1-R10。
- design 决策：`design.md` D1-D8。
- tasks 追溯关系：`tasks.md` T1-T10。

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：IR/validator global-ready；embedded/runtime binding project/target-bound。
- 依赖边界（脚本/数据/上下文）：不新增 runtime server 依赖；外部规范只作 adapter/contract 输入。

## Prompt 回归证据计划
- before/after 对比输入：三条组合否定、现有 routing golden、Profile closure、readonly/implementation final gate。
- 失败样例保留方式：`negative-results.md` 和新增 fixtures/tests。

## 收敛模式与退出条件
- 当前模式（diagnosis/repro/planning/execution）：execution，按 P0→P1→P2 检查点推进。
- 退出条件（进入执行/收敛）：R1-R10 requirement-by-requirement completion audit 通过。

## 备选方案与取舍
- 方案 A：继续追加 checker、manifest、Skill 和静态报告。
- 方案 B：统一 IR、最小闭包、adapter SPI、Evidence Graph 和真实 campaign。
- 选型理由：选择 B；A 只增加控制面熵，不能关闭 runtime/field 有效性缺口。

## 风险与回退
- 风险：路由/Profile breaking、schema 漂移、并行写冲突、来源复核失真、权限扩大和 field 不可压缩时间。
- 回退：每个任务独立可回滚；manifest/compiler 保留明确 migration；runtime feature 默认关闭；field 缺失保持 blocker。
