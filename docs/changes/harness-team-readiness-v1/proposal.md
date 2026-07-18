# 变更提案：harness-team-readiness-v1

## 背景

- 用户提供了一份团队 Harness Engineering 二次整理文章，要求结合现有 `llm_agent`、`agent-dev-kit` 与 Knowledge Hub 吸收优化。
- 现有 ADK 已具备分层上下文、change workflow、能力健康、Harness loop 合同和完成前验证，但缺少面向任意项目的统一 readiness 投影；旧分析文档和旧质量门禁仍描述已失效的平行目录。
- OpenAI 官方《Harness engineering: leveraging Codex in an agent-first world》作为一级来源；用户粘贴内容只作为二级输入，缺失原始文章 URL 与发布日期，不据此声明官方事实。

## 问题陈述（单问题）

- 本变更只解决一个明确问题：ADK 无法用一个确定性、可审查且不依赖模型判断的入口，汇总项目 Harness 的上下文、执行、权限、连续性、验证、恢复和新鲜度证据。
- 触发证据（日志/复现/反馈）：`docs/harness-engineering-analysis.md` 仍把已实现能力标为未来事项，`changes/README.md` 与 `scripts/quality-gates.sh` 仍指向非 canonical 变更结构；现有 `harness-loop-engineering` 只检查 ADK 自身合同，不检查目标项目 readiness。

## 目标

- 提供 `devkit.sh harness readiness --root <repo>` 确定性只读检查与 Markdown/JSON 报告。
- 以七个无权重维度输出 `pass|partial|needs-review|blocked|not-applicable`、证据、owner、验证时间、阻塞项和下一动作。
- 通过 manifest、正负 fixture、测试和 capability health 形成可追溯闭环。
- 校准 Harness 分析文档，并将旧 `changes/` 与旧 quality-gates 入口收敛到 `docs/changes/` 及现有 workflow/checker。

## 非目标

- 不新增 Planner/Generator/Evaluator/Archiver 平行角色或新的 Harness Skill。
- 不创建 CodeBuddy/Knot 专属目录、MCP Server、团队规范仓库或外部运行时集成。
- 不采用 100 分权重、AI 代码占比、提交数量等可被刷高的 KPI。
- 不执行自动修复、外部写操作、MCP 安装、commit、push、merge 或 active Knowledge Hub 发布。
- 不把计划中的 30 天试点描述为已完成现场证据。

## 上下文充分性检查

- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划

缺失的原始公众号 URL 只影响正式来源归档，不阻塞基于官方一级来源和现有仓库事实的工程优化；后续若提供 URL，再走独立 intake/review。

## Core/Optional 边界检查

- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：readiness 只读取目标仓证据，不绑定语言、IDE、模型或业务领域，属于 platform-neutral core 治理能力。

## 变更重复性检查

- 已检索是否存在相同 change-id/同类方案：现有 `harness-loop-engineering`、`capability health`、change workflow 和 verification gate 均已复核。
- 若有历史方案，本次差异与必要性：复用现有能力，不再实现运行循环；新增的是跨仓 Harness evidence projection，并把旧入口迁回 canonical change governance。

## Breaking Change 检查

- [ ] 否：不涉及兼容性破坏
- [x] 是：涉及兼容性破坏（必须补充迁移与回退计划）

`scripts/quality-gates.sh` 保留路径但不再接受旧 `request_analysis/coding/ci_result` 语义，改为检查 canonical `docs/changes/` 工件，因此属于有迁移说明的行为 breaking change。仓内调用点已复核，只有旧分析/旧说明引用；外部调用者需先迁移工件，再改用 `scripts/check-change-governance.sh`。回退可恢复旧脚本，但会重新启用已废弃的平行框架。readiness 新命令默认 report-only，只有显式 `--gate` 才返回未就绪状态。

## Spec 链路检查

- requirements 基线：本提案的目标、非目标、七维输出合同和验收标准。
- design 决策：`design.md` 的 contract-driven Python core、有限扫描、脱敏和状态聚合规则。
- tasks 追溯关系：`tasks.md` 的 T1 至 T5 分别对应治理校准、实现、fixture/测试、能力健康和知识沉淀。

## 安装范围与依赖边界

- 安装范围（global-ready/project-bound）：命令本身属于 ADK global-ready；被扫描仓库只作为只读 project-bound 输入。
- 依赖边界（脚本/数据/上下文）：仅 Python 标准库、ADK manifest、目标仓文本元数据和本地文件系统；不访问网络、不读取凭证值、不执行目标仓脚本。

## Prompt 回归证据计划

- before/after 对比输入：同一正向 fixture 和包含硬编码 MCP token 的负向 fixture；before 只能人工拼接现有 checker，after 由单一 CLI 输出稳定合同。
- 失败样例保留方式：负向 fixture 与 `negative-results.md` 同时保留，报告只暴露敏感字段路径和问题码，不回显秘密值。

## 收敛模式与退出条件

- 当前模式（diagnosis/repro/planning/execution）：planning；change governance 检查通过并迁移到 `applied` 后切换 execution。
- 退出条件（进入执行/收敛）：实现、定向测试、quick/full gate、独立 review 工件和 Hub reviewing candidate 均有证据；真实试点仍作为开放项。

## 备选方案与取舍

- 方案 A：新增 prompt-only `harness-audit` Skill 和加权总分。拒绝，因为判定不可稳定复现，分数会掩盖关键维度短板并诱导刷分。
- 方案 B：复用 ADK typed core、manifest 和现有 capability health，输出无权重 readiness 状态。采用，因为可机械验证、可跨工具复用，并保留人工复核边界。
- 选型理由：只有路径、结构、配置和脱敏检查进入机械门禁；架构质量、业务正确性和现场有效性继续显示为 evidence gap，不伪装为自动结论。

## 风险与回退

- 启发式误判：每个维度输出实际 evidence_refs 与 blocker code；默认 report-only，支持人工复核。
- 大仓扫描成本：manifest 限制文件数量、单文件大小并排除 `.git`、依赖和构建目录。
- 敏感信息泄漏：只报告文件和 JSON key path，绝不输出检测到的值。
- 兼容性：旧脚本保留包装层；回退时可撤销新 Python 模块、manifest、CLI 分支和测试，并恢复旧文档，不影响现有 workflow 数据。
