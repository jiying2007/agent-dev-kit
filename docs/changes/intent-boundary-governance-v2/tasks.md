# 执行任务：intent-boundary-governance-v2

- [x] T1 冻结 invocation 与 task-package v2 声明式合同；verify：manifest/schema/official-docs governance 定向负例证明非法 mode、未知 override、v1 task schema 和权限冲突均失败
- [x] T2 实现 direct target invocation adapter；verify：Claude explicit-only fixture 生成 `disable-model-invocation: true`，OpenCode/Hermes 对同输入 fail closed，implicit 导出保持无冗余字段
- [x] T3 增强 task breakdown、planning loop、parallel governance、task template；verify：三项 Skill 与模板只引用 v2，research/prototype 无 implementation 权限，Skill 质量/token 门禁通过
- [x] T4 增强 architecture hotspot scope 与 prototype evidence；verify：Agent 输出契约和结构化 evidence contract 必需字段、扩域条件、retention 条件被机械检查
- [x] T5 更新文档、migration、版本和 llm_agent adoption/lifecycle 证据；verify：ADK 3.1.0-rc.5、manifest sync、doc sync、adoption structured/status 检查通过，sampled watch 未恢复 submodule
- [x] T6 硬切 `~/codex` managed metadata 并完成 source-to-live rehearsal/apply；verify：legacy 顶层 metadata/explicit true 零残留，build/doctor/plan/dry-run/apply/routing/check 与运行态 smoke 有证据
- [x] T7 完成定向、quick/full、安全、性能、独立 review、提交和复盘；verify：blocker=0、major=0，Evidence Index 与完成声明一致

## Ownership 与并行冲突检查

- scope_write：
  - ADK `manifest.json|manifest.yaml`、manifest/target schemas、target adapters、structured/reproducibility/plugin contracts；
  - 既有 task/planning/parallel Skill、architecture Agent、task/prototype templates、tests/docs/change evidence；
  - 根仓 adoption matrix/lifecycle/source assessment；
  - 经 dirty 分类和审批后的 `~/codex` metadata/checker/manifest/source-to-live evidence。
- scope_read：上游不可变 snapshot、OpenAI/Claude 官方 metadata 文档、本地 ADK/Codex contracts、全部 v1/legacy 调用点。
- must_not_touch：根仓进入本 change 前的无关已修改子仓与未跟踪目录；上游仓；远端；凭证；未审查 hook/MCP/plugin；与本 change 无关的 Codex source dirty。
- shared contract：manifest schema、task schema、target compiler、版本和 source-to-live 均串行。
- Parallel Suitability：no；所有主要任务共享 schema/adapter/版本，且本轮用户未要求多 Agent。

## Task package v2 自举记录

| ID | kind | question_to_resolve | implementation_permission | exit_gate | handoff_target | retention_decision |
|---|---|---|---|---|---|---|
| T1 | decision | invocation/task v2 的唯一 SSOT 与硬切字段是什么 | forbidden | owner-decision | T2 | keep-final |
| T2 | implementation | direct target 如何确定性映射 invocation mode | approved | implementation-verified | T3 | keep-final |
| T3 | implementation | 现有 planning Skills 如何消费 work-item kind | approved | implementation-verified | T4 | keep-final |
| T4 | implementation | hotspot scope 与 prototype provenance 如何机械门禁 | approved | implementation-verified | T5 | keep-final |
| T5 | implementation | 版本、文档和 adoption provenance 如何同步 | approved | implementation-verified | T6 | keep-final |
| T6 | implementation | Codex source-to-live 如何无 legacy 硬切 | approved | implementation-verified | T7 | keep-final |
| T7 | decision | 本地终态声明是否被独立证据支持 | forbidden | owner-decision | none | archive-negative-result |

每项 `evidence_required` 为对应 verify 命令的真实退出码、结果摘要和 evidence path；`question_to_resolve` 只允许在当前任务内收敛。T2–T6 的 `approved` 来自用户当前“按建议吸收优化落地”授权，但不扩大网络写入、push/publish 或未审查运行时权限。

## 关键路径与检查点

`T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7`

- checkpoint：每项完成后更新本文件、`negative-results.md`、`verification-evidence.md`。
- retry_budget：同一失败根因最多 2 次。
- heartbeat：每项至少新增一个正例、负例或状态证据。
- staleness_threshold：45 分钟。
- stop_condition：`pass|replan|split|blocked|abort`。
- merge/commit order：ADK contract/compiler → ADK consumers/evidence/version → root adoption → Codex source adapter → source-to-live evidence。

## 轻量工件与收敛结论

- 需求梳理工件：`proposal.md`、`design.md`、root source assessment report。
- task checklist 工件：本文件 T1–T7 与 `checklist.md`。
- 执行反馈/验收记录工件：`verification-evidence.md`、`negative-results.md`、`review-findings.md`、benchmark/timing/release rehearsal JSON。
- 收敛结论：ENHANCE 项均在既有 core/optional 资产中完成；OBSERVE/REJECT 项未进入运行依赖；无未闭环 blocker/major。
- 阻塞说明：无；remote publish、tag 与真实双 runtime certification 明确不在本 change 范围。
