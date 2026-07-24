# 变更提案：aggregate-gate-evidence-reuse-v1

## 背景
- 2026-07-23 新鲜根仓 `check-all.sh --full` 用时 906 秒；其中
  `check-workspace-entrypoints.sh` 用时 207 秒。
- root regression 已执行全部 16 个根测试并通过，但 workspace aggregate
  又执行 `test_runtime_target_evidence_package.sh`（约 18 秒）与
  `test_runtime_target_evidence_promotion.sh`（约 38 秒），形成同一聚合运行
  内可证明的重复覆盖。
- 终态成熟度复审将该问题记录为 minor TM-003；优化前提是不删除唯一覆盖、
  不复用历史失败/过期结果、不弱化 strict dirty 和外部证据门禁。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：full 聚合门禁在同一次、同一未变化工作区内
  重复执行已通过的 expensive leaf checks，但目前没有可验证、fail-closed
  的单次运行证据传递机制。
- 触发证据：
  - `reports/terminal-maturity-check-all-full-2026-07-23.json`：55/59，
    906 秒，workspace aggregate 207 秒。
  - `reports/terminal-maturity-root-tests-2026-07-23.json`：16/16，
    两个重复测试合计约 56 秒。
  - `terminal-maturity-optimization-v2/review-report.md`：TM-003 minor。

## 目标
- 为 full 聚合门禁增加同运行、指纹绑定的安全证据复用
- 保留 standalone workspace aggregate 的完整执行语义。
- 通过父 PID、workspace fingerprint、producer/output digest 与 allowlist
  阻断跨会话、失败、篡改和漂移证据。
- 输出机器可读的实际复用项并量化新鲜 full 提速。

## 非目标
- 不复用 harden、performance、expected-failure、JSON interface assertion、
  live/source-to-live 或失败结果。
- 不实现跨进程历史 cache、TTL cache、远端 cache 或 release evidence cache。
- 不改 strict dirty、M5 blocker、外部现场条件和成熟度等级。
- 不 commit、push、merge、rebase，不写 `~/codex` 或 `~/.codex`。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（伪造、漂移、输出替换、兼容、性能）
- [x] 已明确验证命令与通过标准
- [x] 已读取历史 full gate audit；历史结论仅作 provisional 背景

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：聚合门禁证据传递与 fail-closed 验证属于平台中立的测试
  控制面，不引入 runtime-specific optional asset。

## 变更重复性检查
- 已检索 `docs/changes/`、根 scripts/tests 与历史 Hub validation reports；
  不存在同 change-id 或可复用的同运行 evidence contract。
- `terminal-maturity-optimization-v2` 新增结果 JSON 与 timing，但没有证据复用；
  本 change 只闭环其 review minor TM-003。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：`requirements.md` R1-R5。
- design 决策：`design.md` D1-D5。
- tasks 追溯关系：`tasks.md` T1-T6。

## 安装范围与依赖边界
- 安装范围：root project-bound；不进入 runtime live assets。
- 依赖边界：Bash、Python 标准库、Git、SHA-256；不新增网络或第三方依赖。

## Prompt 回归证据计划
- 本变更不修改 prompt，before/after 为 not-applicable。
- 失败样例由自动化 fixture 与 `negative-results.md` 保存。

## 收敛模式与退出条件
- 当前模式：planning，apply 后进入 execution。
- 退出条件：R1-R5 可重放；blocker/major=0；full 真实报告复用数和耗时；
  invalid evidence 全部 fallback。

## 备选方案与取舍
- 方案 A：删除 workspace 中重复检查。拒绝，standalone aggregate 会失去覆盖。
- 方案 B：持久化按时间复用结果。拒绝，容易把跨会话、过期或漂移结果当真。
- 方案 C：仅由同一次 `check-all` 父进程提供、工作区和摘要绑定的临时证据，
  无效时回退执行。采用，可兼容 standalone 且 fail-closed。

## 风险与回退
- 风险：workspace fingerprint 覆盖不足；显式覆盖根仓与 ADK 的 HEAD、
  diff、status 和 untracked file content，并补漂移负测。
- 风险：marker 存在但目标测试未执行；证据同时要求 root regression 整体
  exit=0、精确 marker、脚本/输出 digest 与未变化 fingerprint。
- 风险：fingerprint 自身开销抵消收益；只在 full 内启用并量化 component
  timing，不满足收益阈值则移除复用。
- 回退：删除临时 evidence 传递和 allowlist 调用，standalone 原命令路径
  始终保留；不触碰用户既有 dirty 变更。
