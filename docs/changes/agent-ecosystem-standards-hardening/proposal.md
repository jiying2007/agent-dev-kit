# 变更提案：agent-ecosystem-standards-hardening

## 背景
- `agent-dev-kit` 已完成多 target 的 Skill 渲染、描述字段和静态 conformance 修复，但这些能力尚未显式关联 Agent Skills 开放格式。
- 当前安全、自动化、MCP provenance、trace interoperability 分散在既有 manifest 中，缺少一份可机检的外部生态标准映射。
- 2026-07-14 对 Agent Skills、OWASP Agentic Top 10 2026、GitHub `gh-aw` safe outputs、MCP Registry、OpenTelemetry GenAI semantic conventions、ACP 和 A2A 的只读调研，确认存在可吸收的方法级实践。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：ADK 缺少对高价值 Agent 生态标准与安全实践的显式、可追溯、可机检治理契约。
- 触发证据（日志/复现/反馈）：`manifests/skill_reproducibility_contracts.json`、`manifests/adk_runtime_policy_gates.json`、`manifests/automation_worktree_contracts.json`、`manifests/skill_mcp_dependencies.json` 和 `manifests/trace_eval_contracts.json` 均无对应 external source reference；ACP/A2A 也没有 watch-only 决策。

## 目标
- 补齐 Agent 生态标准、安全与互操作治理契约
- 复用既有 SSOT manifest，而不是创建平行治理体系。
- 用正向 bundle 与负向 fixtures 固定 Agent Skills、OWASP ASI01-ASI10、safe-output、MCP provenance、OTel adapter 和 watch-only 边界。
- 产出来源决策、验证证据、回退边界和 adoption 记录。

## 非目标
- 不新增或启用外部 runtime、MCP server、connector、plugin、submodule 或网络写操作。
- 不把 ACP/A2A 实现为 transport runtime；只记录复审触发器。
- 不重做 RC2 已完成的 Skill compiler/target renderer。
- 不复制外部仓库源码、prompt、文档正文或受许可证约束的长段内容。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（来源漂移、契约重复、敏感 trace、runtime 越界、兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划：来源 freshness 到期后只读复核，不自动升级 runtime

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）：Agent Skills portable format、OWASP ASI crosswalk、safe-output、MCP provenance。
- [x] 属于场景化能力（optional）：OTel GenAI adapter、ACP/A2A watch-only metadata。
- 归属结论与理由：核心只定义平台中立治理契约；互操作 adapter 不默认启用，避免把 ADK 变成 runtime。

## 变更重复性检查
- 已检索 `docs/changes/`、相关 manifests、scripts 与 tests；不存在相同 change-id。
- RC2 已覆盖 target conformance，本次仅补 external provenance 和跨 manifest 治理门禁，不重复修改 compiler。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏；新增字段和检查器，不删除既有字段或改变默认 runtime 行为
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：`proposal.md` 的目标、非目标和完成标准。
- design 决策：`design.md` 的六类契约映射和 watch-only 边界。
- tasks 追溯关系：`tasks.md` T1-T5；每项均有明确写入范围和验证命令。

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：`global-ready` 治理资产；本次不执行 source-to-live apply。
- 依赖边界（脚本/数据/上下文）：仅仓内 JSON/Markdown/shell checker/fixtures；外部 URL 只作为 provenance，不在测试时联网。

## Prompt 回归证据计划
- before/after 对比输入：相同的 portable skill、安全 taxonomy、safe-output、MCP dependency、trace adapter 和 protocol watch bundle。
- 失败样例保留方式：`fixtures/agent-ecosystem-standards/fail/`，每个 fixture 固定单一 `expected_failure`。

## 收敛模式与退出条件
- 当前模式（diagnosis/repro/planning/execution）：`execution`。
- 退出条件（进入执行/收敛）：定向 checker、负向 fixtures、严格资产验证和全量测试全部通过；若存在 blocker/major 或 runtime 被意外启用则停止。

## 备选方案与取舍
- 方案 A：创建新的统一生态标准 mega-manifest。
- 方案 B：把来源决策放入既有 external ledger，把实际契约落到各自 SSOT，并用一个跨 manifest checker 验证。
- 选型理由：采用方案 B，降低重复概念和 schema drift，同时保留来源到落点的双向追溯。

## 风险与回退
- 风险：外部标准快速演进；通过 `retrieved_at`、`review_status`、`expires_at` 和版本 pin 控制。
- 风险：外部方法被误当作 runtime 授权；所有候选显式 `runtime_enabled=false`，ACP/A2A 仅 `observe-method-only`。
- 风险：trace 泄露 prompt/tool arguments；OTel adapter 默认关闭 content capture，并列出 deny fields。
- 回退：删除本 change 新增的 additive 字段、checker/test/fixtures 和 adoption 记录即可；不涉及数据迁移或外部状态回滚。
