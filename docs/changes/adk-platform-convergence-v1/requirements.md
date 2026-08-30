# 需求基线：adk-platform-convergence-v1

## Goal Statement

在不把 ADK 扩张为通用 Agent runtime、不放宽权限和不覆盖用户 dirty 内容的前提下，落实
`reports/llm-agent-adk-comprehensive-design-assessment-2026-08-30.md` 的 P0/P1/P2 目标，形成可编译、
可验证、可回滚、可跨运行时评测的最终平台版本。

## Non-goals

- 不实现新的 LLM 推理循环、通用 scheduler、Temporal/LangGraph server 或后台 daemon。
- 不默认启用 MCP、Hook、Plugin、Automation、Tasks 或外部写操作。
- 不把 fixture、自试点或静态 contract 冒充独立 runtime/field evidence。
- 不自动 commit、push、merge、rebase、清理参考子仓或修改 `~/.codex` live。

## Global Constraints

- Python release baseline 为 3.11/3.12；不支持解释器只能形成 development evidence。
- 共享 `manifest.json`、`manifest.yaml`、schema 由单一任务独占写入。
- 行为变化必须包含正例、负例、边界和回归测试。
- routing、workflow、runtime 结论必须支持 `abstain` 或 `not-applicable`，不得强制伪命中/伪通过。
- 外部来源只采用官方文档、规范或上游仓库，记录 retrieved/review/expires 和变化判断。
- 所有运行能力默认关闭；启用需要 owner decision、目标适配、权限和 rollback 证据。

## Requirements

### R1 路由单一 IR

- 路由合同显式包含 task mode、否定信号、mutation permission、profile availability 和 abstain。
- 现有正向路由保持兼容；组合否定不得被关键词强制命中。
- routing intent、matrix 和文档必须可由同一权威结构校验或生成。

### R2 平台中立 Core

- `core` 不包含 driver/BSP/RTOS/C-C++/HIL 等嵌入式专属 Agent/Skill。
- `embedded-fullstack` 继续提供完整嵌入式闭包。
- core、embedded、release、team Profile 的 closure 和 export 测试通过。

### R3 Runtime Control 适用性

- final gate 根据 task mode 计算适用工件。
- readonly assessment/explanation 不要求 build/repo 实施工件。
- implementation/release 缺 build/repo 时继续 fail-closed。
- 不允许用 `allow_idle`、未知 mode 或缺目标闭环绕过 gate。

### R4 官方来源和工具链新鲜度

- 当前到期官方来源完成真实复核，不只延长日期。
- strict validate 不再因已复核来源到期失败。
- 默认入口优先选择受支持 Python；本机缺失时明确降级，不伪造 release evidence。

### R5 Workflow IR

- 一等 Workflow 具有版本化节点、I/O、transition、retry/timeout/cancel、idempotency、approval、
  checkpoint、rollback、evidence 和 terminal state 合同。
- `WORKFLOW.md` 是人类可读投影或与 IR 受同步门禁约束。
- ADK 只定义/验证执行语义，不内置外部 durable runtime。

### R6 Runtime Adapter SPI

- target adapter 明确 discovery/load/trigger/resume/cancel/rollback/trace 能力和 unsupported 行为。
- 至少一个 target 完成 native conformance；其他 target 不以 static contract 冒充 runtime pass。

### R7 Trace 和 Effect Eval

- 每次 run 可关联 asset bundle hash、target/runtime/model、tool、cost/latency、outcome、人工介入和隐私状态。
- routing eval 覆盖 contrastive、negation、abstain、metamorphic 和 multi-turn。
- baseline/ADK 对照保留统计、成本和失败证据。

### R8 Agent/Skill/Profile 价值治理

- Agent 声明 role/input/output/permission/tool/authority/handoff/evidence/assumption/eval 合同。
- Skill/Profile 记录真实 invocation、误路由、abstain、outcome 和退役信号。
- 数量、PR、报告和 Token 总量不作为质量 KPI。

### R9 维护性和 Evidence Graph

- 维护预算增加耦合、churn、SSOT 重复、owner concentration、执行时间和 inactive asset 指标。
- source→decision→asset→bundle→runtime→trace→outcome→release/rollback→retirement 可追溯。
- 新增长期报告必须有 supersession/retention 决策。

### R10 真实运行和 Field

- 至少两个 runtime 完成 baseline/ADK campaign。
- 至少一个独立真实仓、两个 human operator 和不少于 30 天 field cycle。
- upgrade、rollback、fault、recovery、maintenance、review 均有事件证据。

## Done When

- R1-R9 对应 source/test/runtime-local 验证全部通过，R10 由现有 Software M5 certifier 证明完成。
- ADK full、root full、strict validate、profile/workflow/routing/target/security/release 门禁全绿。
- 交叉审查 blocker/major 清零，minor 有处置决定。
- current architecture、machine backlog、scorecard 和实际证据一致。
- 没有未解释的 skipped requirement、stale evidence 或权限扩大。

## Required Evidence

- change artifacts：requirements/design/tasks/negative-results/verification/review/state/history。
- routing/profile/workflow/runtime/target 正负测试。
- Python 3.11/3.12 full regression、远端或 local parity 证据。
- native runtime campaign 和 field ledger/certifier 证据。
- 根仓与 ADK clean/release 或 working-tree fingerprint 边界。

## Blocker Policy

- 外部认证、第二操作者或 30 天 field cycle 缺失时，R10 保持 blocked-external，但不得阻止继续完成 R1-R9。
- 同一技术 blocker 连续三轮且无新信息时才升级为 blocked；否则继续替代实现或补证据。
- 任何权限放宽、secret、路径越界、数据破坏或 runtime/live 未授权写入立即停止相关任务。

