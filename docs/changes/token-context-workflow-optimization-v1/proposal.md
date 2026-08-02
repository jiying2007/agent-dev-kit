# 变更提案：token-context-workflow-optimization-v1

## 背景
- 当前已有 `token-lean`、Hub `summary-json`、compact test runner 和 same-run evidence，
  但固定上下文、路由、Hub 预检、门禁编排和观测仍分别放大默认成本。
- 2026-08-01 基线：进入 ADK 时三级规则文本约 21.8 KiB；`token-lean` 恰好启用
  20 个 skill；根仓 smoke 12 项耗时 32 秒且 same-run reuse 为 0。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：在不削弱高风险门禁的前提下，降低 ADK 与 Hub
  日常任务的默认上下文、错误路由、重复扫描和输出成本。
- 触发证据：usage dashboard 因缺少 `thread_goals` 失败；通用 Python 单测查询把
  embedded skill 排第一；Hub 18 天 580 次调用中 context 为 425 次；smoke 复用为 0。

## 目标
- 降低 ADK 与 Knowledge Hub 默认上下文和重复门禁成本

## 非目标
- 不删除完整 profile、vendor skill、Hub owner gate、source-to-live 或 release 验证。
- 不自动 commit、push、提升 active、写 memory 或修改 `~/.codex` 手工资产。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出局部原文回退与分阶段验证计划

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：预算、路由、检索和验证编排是平台中立控制面；embedded 能力
  只调整为延迟加载，不修改其业务实现。

## 变更重复性检查
- 已检索 `aggregate-gate-evidence-reuse-v1`、既有 token context runbook、Codex
  profile 与 Hub retrieval contract。
- 历史方案只覆盖 `check-all --full` 的 workspace entrypoint allowlist；本次扩展到
  默认上下文、Skill/Hub 路由、usage 兼容和 Codex source-to-live receipt，不重造
  历史 fail-closed evidence schema。

## Breaking Change 检查
- [x] 否：不涉及公共命令删除；默认候选数和 active profile 收窄，但能力仍可延迟发现
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：`requirements.md` R1-R8。
- design 决策：`design.md` D1-D7。
- tasks 追溯关系：`tasks.md` T1-T7。

## 安装范围与依赖边界
- 安装范围：ADK 契约为 global-ready；根仓与 Hub 实现为 project-bound；Codex 资产
  必须经 `~/codex -> ~/.codex` source-to-live。
- 依赖边界：本地文件、SQLite 只读状态、Hub registry/index、临时 receipt；无网络、
  无凭证、无外部写入。

## Prompt 回归证据计划
- before/after：通用 Python 单测、单行 README、跨仓决策、Hub 显式 project、缺表
  SQLite、no-op apply、root smoke。
- 失败样例：进入 `negative-results.md` 与定向 fixture，不删除既有失败断言。

## 收敛模式与退出条件
- 当前模式：planning。
- 退出条件：requirements/design/tasks 完整并通过 change apply 后进入 execution；所有
  分仓门禁和 source-to-live 通过后收敛。

## 备选方案与取舍
- 方案 A：删除治理与验证；拒绝，安全和可追溯性退化。
- 方案 B：保留能力，按任务风险延迟披露并复用确定性证据；采用。
- 选型理由：优化“何时加载/何时验证/输出多少”，不改变高风险事实门禁。

## 风险与回退
- 风险：过度瘦身导致能力不可发现、缓存误复用、Hub 路由被强制覆盖、旧 SQLite
  不兼容。回退：恢复 profile/limit；receipt 校验失败自动重跑；显式路由无效时
  fail closed；缺表降级为空 goals 并标记 unavailable。
