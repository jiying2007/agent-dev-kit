# Planning Execution Loop Runbook

## 目标

把复杂任务转成可审查、可恢复、可验证的阶段执行闭环。

## 适用场景

- 已有计划需要持续执行。
- 任务跨会话、跨阶段或有多个验证检查点。
- 需要从参考仓吸收能力并落到 adk 资产。

## 推荐组合

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Primary Skill：`adk-planning-execution-loop`
- Supporting Skills：`adk-task-breakdown`、`adk-verification-before-completion`

## 工件

- `PROJECT.md`：目标、边界、非目标、长期约束。
- `REQUIREMENTS.md`：可证伪需求、验收条件、开放问题。
- `PLAN.md`：阶段、依赖、done criteria、验证命令。
- `session-state.md`：当前阶段、已完成项、未闭环项。
- `next-actions.md`：下一步命令和完成标准。
- `risk-ledger.md`：风险、阻塞、被证伪路径。
- `resume-prompt.md`：新会话恢复入口。
- `SUMMARY.md`：会话压缩摘要和最终交接上下文。
- `goal-closure.md`：原始目标、完成声明、证据、open items、停止条件。
- `repair-ledger.md`：失败范围、保留的通过项、最小重跑命令、回退锚点。

## 目标闭环与卡死保护

- 每个长任务开始时记录 `goal_statement`、done criteria、`retry_budget` 和 `staleness_threshold`。
- 每个 checkpoint 更新 heartbeat：当前阶段、最新动作、下一步、阻塞和是否有信息增量。
- 长任务按阶段交给窄上下文执行单元时，主流程只分发任务包、范围和验收标准；不得把全量历史和无关日志继续传给每个执行单元。
- 复杂交付可使用“规划者/执行者”分工：规划者只产出目标、架构、任务边界和验收标准；执行者只能按当前阶段任务包修改文件，并在阶段结束后停止等待检查。
- 规划文档是阶段执行的单一事实源。执行者发现计划缺口、上下文冲突或需要扩大 scope 时，必须回到计划审查，而不是自行扩写目标。
- 进入完成声明前，先生成 `completion_claim`，再由 `adk-verification-before-completion` 独立核对证据。
- retry budget 用尽、heartbeat 过期或连续无信息增量时，必须 replan、split、blocked 或 abort，不能继续盲目推进。

## Spec-Driven Execution Gate

流程强度按项目类型、行为变化、影响面和风险决定：小且无行为变化的任务可走轻量验证；跨模块、架构、核心系统、生产路径或安全边界变更必须进入标准或严格 spec gate。正式产品或高风险变更不得从“直接实现”开始。至少按以下阶段推进：

1. 需求验证：确认问题、用户/设备场景、非目标和验收方式。
2. 方案设计：沉淀架构、接口、数据流、状态机、风险和回退策略。
3. 评审：对需求、工程、测试、交互或运维影响做针对性审查。
4. 任务切片：使用 `adk-task-package-schema-v2` 拆成 decision/research/prototype/implementation，声明问题、证据、实现权限、exit gate、handoff、retention、`scope_read`、`scope_write`、`must_not_touch` 和验证命令。
5. 执行与验证：每个任务独立检查结果，不能把“生成了代码”当作完成。
6. 复盘：记录返工原因、验证缺口和可复用经验候选。

Planner 派发前必须先校验计划 schema：必填字段完整、kind/permission/exit gate 一致、`dependsOn` 引用存在、依赖图无环、prompt/context 未超预算、`retry_budget` 明确。decision/research/prototype 固定禁止 implementation 权限；校验失败时不得创建 worker、worktree 或子代理，必须返回 plan repair。

数据库 schema 变更必须同带迁移、回滚和兼容性说明；删除较大代码、公共 API 或共享 contract 前必须列出调用点、影响面和 approval gate。

## 门禁强度分级

每个关键质量要求必须标注 enforcement level，避免把建议误写成不可绕过门禁：

| Level | 含义 | 示例 |
|---|---|---|
| deterministic | 由 CLI、测试、schema、hook 或 CI 程序性阻断 | 格式校验、单测、资产 schema、密钥扫描 |
| approval | 由明确 owner 人工确认后放行 | 生产配置、外部连接器、发布、权限扩大 |
| advisory | 由 Skill、prompt、runbook 或 review 提醒模型遵守 | TDD 纪律、任务拆分建议、代码风格建议 |

不可绕过的事项必须落到 deterministic 或 approval；单靠 Skill、Prompt 或自然语言规则只能标为 advisory。若同一质量要求同时写入 Skill 与 CI，以 CI/脚本证据为完成声明依据。

## Harness 分层

复杂 Agent 交付按 harness 设计治理，而不是只优化 prompt 或增加子 Agent。

| 层 | 责任 | ADK 落点 |
|---|---|---|
| Goal/task | 明确目标、非目标、验收和停止条件 | `REQUIREMENTS.md`、任务卡 |
| Context | 控制读取层级、预算、原文回退和交接 | `token-context-governance.md` |
| Tool/MCP | 暴露受控能力，执行前做 allow/deny | `mcp-governance.md`、tool policy |
| Execution | 分阶段推进，窄上下文执行，检查 heartbeat | `PLAN.md`、`session-state.md` |
| Feedback/eval | 测试、lint、review、evaluator 和人工审批 | verify/review gate |
| Handoff | 保存状态、风险、证据和下一步 | `SUMMARY.md`、`resume-prompt.md` |

堆更多 Agent、MCP 或 token 不等于更强。只有当任务契约、验证证据、失败回退和交接状态齐全时，才允许扩大并行度或工具面。

垂直业务自动化从脚本升级为可复用 Skill 或 workflow 前，必须把接口适配、核心规则、数据依赖和人工审批拆层治理。批处理、外部 API、文件转换或表格生成类任务还必须声明断点续传、去重、缓存有效期、错误分级和最小重跑策略。

## Planner / Worker / Critic Loop

多 Agent 工作流必须把“计划、执行、质疑”拆成可验证角色，而不是让一个 Agent 同时自由发挥：

1. Planner 只输出结构化任务图，至少包含 task id、owner、scope、inputs、expected output、dependencies 和 verification。
2. Worker 只执行分配给自己的任务包，并把结果写回共享状态摘要；不得扩大目标或修改未授权范围。
3. Critic 不执行实现，只检查证据、可靠性、风险和缺口，并给出 `pass`、`rework` 或 `blocked`。
4. `rework` 必须回到 Planner 更新任务图，不允许 Worker 直接按评论发散修改。
5. 共享状态只能保存压缩后的阶段结果、证据路径和未解决风险，不保存全量原始日志。

该循环适合跨模块研究、方案评审和报告生成；涉及 shared contract、schema、根配置或生产动作时仍按串行治理。

## 失败修复策略

- 失败后先确认最小失败范围：输入、文件、模块、测试、设备阶段或运行环境。
- 修复前写 repair note：failed scope、passing scope to preserve、minimal rerun、rollback anchor。
- 已通过产物默认保留；只重跑最小失败项，除非共享契约或全局配置发生变化。
- schema/格式正确不代表语义正确，语义修复后仍需走完成前证据核验。

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 验收门禁

- 每个阶段都有 done criteria 与验证证据。
- 恢复工件足够让新会话继续执行。
- 目标闭环记录能从原始目标追溯到完成声明、证据和剩余风险。
- 失败修复记录包含最小失败范围、保留通过项和最小重跑证据。
- 完成声明前必须通过 completion gate。
- checkpoint 写入后必须可读、可追溯，并且无孤儿临时状态。
- 临时参考材料只能作为背景输入，不能未经评估进入长期知识或 adoption matrix。
