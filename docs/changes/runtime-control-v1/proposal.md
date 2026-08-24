# 变更提案：runtime-control-v1

## 背景
- 当前 Goal、Token、长任务和完成门禁分散在 ADK `token_monitor.py`/`execution_guard.py`、
  Codex `usage_dashboard.py`/`session_coach*.py`/`final-ready.sh` 和多个 manifest/CLI 中。
- 用户明确要求只实现一套、不兼容、不残留、不冗余，并批准破坏式单轨切换。

## 问题陈述（单问题）
- 只解决：建立唯一 Runtime Control Engine、state/event/decision contract 和唯一用户 CLI，删除
  所有旧 active 实现、命令、配置与测试。
- 证据：调用点扫描显示 ADK 两套 evaluator、Codex usage/session coach 多套阈值与 goal template，
  且 `thread_goals` 当前不可用、usage wrapper 非 repo cwd 会被同名 package shadow。

## 目标
- 破坏式统一 Goal、Token、长任务与完成门禁控制面

## 非目标
- 不保留 alias/fallback/dual-read/dual-write/deprecation；不迁移旧 goal/cooldown/dashboard state。
- 不自动 commit/push；不覆盖 `~/codex` 现有 9 个不相关 dirty 文件。

## 上下文充分性检查
- [x] 已明确 runtime_control.event/state/decision v1 与唯一 CLI
- [x] 已识别破坏性删除、Goal SSOT、跨仓依赖、source-to-live 和 dirty overlap 风险
- [x] 已明确三仓定向/full、zero-residual、build/doctor/plan/apply/runtime health
- [x] owner 已明确批准不兼容硬切换

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：ADK 维护唯一平台中立 Engine；Codex 只维护 source adapter。

## 变更重复性检查
- 已检索五个现有 change、ADK typed core、Codex usage/session/goal/final-ready 全部调用点。
- 本 change supersede `realtime-token-usage-monitor-v1` 与 `long-task-execution-guard-v1`，不叠加第三层。

## Breaking Change 检查
- [ ] 否：不涉及兼容性破坏
- [x] 是：删除旧 CLI/schema/module/state；只允许整包 backup rollback，不允许混跑

## Spec 链路检查
- requirements：`requirements.md` R1-R10。
- design：`design.md` D1-D9。
- tasks：`tasks.md` T1-T8。

## 安装范围与依赖边界
- 安装范围：ADK core package + Codex source-to-live + llm_agent integration gate。
- 依赖边界：Codex adapter 采集 state DB/rollout/journal；仅 ADK Engine 决策；无 raw prompt 持久化。

## Prompt 回归证据计划
- before：四个用户命令、两套 ADK evaluator、Session Coach 私有决策。
- after：唯一 `runtime-control` CLI 与 `runtime_control.* /v1`；zero-residual scan 固化旧名称负例。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：三仓 full、zero-residual、source-to-live、whole-diff review 均有新鲜证据。

## 备选方案与取舍
- A：adapter + 兼容旧命令，拒绝；会保留双 SSOT。
- B：ADK 唯一 Engine + Codex 唯一 adapter/CLI + 原子删除，选用。
- 理由：实现、策略、配置、状态、入口和测试均只有一套。

## 风险与回退
- 风险：破坏现有脚本/goal state；不迁移旧 state，新 goal 从零开始。
- 回退：仅恢复切换前 source/live backup 整包；禁止新旧局部混合。
