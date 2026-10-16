# 现有路由导出 E0-E3 保守投入等级，调试审查证伪，A/B/A/B 性能证据纪律 — Canonical Change Proposal

## 问题陈述（单问题）
- 既有 ADK 能力有具名的质量或表述缺口，但应保留唯一 Routing IR、Skill v2、八阶段生命周期与变更合同。
- 本变更已实际按 PR #198 实施，当前文件为根据已完成的 CI/Release 事实补齐的治理追溯，**不是新一轮实现或独立审批**。

## 上下文充分性检查
- [x] 目标和影响面已冻结：src/agent_dev_kit/matcher.py and selected existing SKILL.md。
- [x] 已查阅原有 CI 门禁、版本和受保护主线证据。
- [x] 已识别跨宿主、真实模型/现场和 Human Owner 证据不能从源码回归推导。

## Core/Optional 边界检查
- [x] 仅修改既有 Skill 或匹配测试/文档，无新增 Skill 包或隐式依赖。
- 现有 core/optional 角色与安装配置不变；不让任何上游参考 Skill 成为 active runtime。

## 变更重复性检查
- 沿用原生产 matcher 和现有测试入口，不引入第二路由器、评估 SSOT 或并行工作流。
- 独立采纳治理仍由 Root 外部实践决策保持，不由此归档记录自行批准。

## Breaking Change 检查
- [x] 无 runtime schema、路由身份、effect permission 或目标接口破坏性变更。
- 回滚锚点是 PR #198 squash 合并前的受保护 main。

## Spec 链路检查
- requirements 基线：同目录 requirements.md。
- design 决策：同目录 design.md，沿用已受控的唯一权威。
- tasks 追溯：同目录 tasks.md；机器成功与人工独立复核分开记录。

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 以最小改动改进既有能力 | MODIFIED | ADK source 8.0.20 | src/agent_dev_kit/matcher.py and selected existing SKILL.md | ACC-001 | 不新增平行能力或提升 effect authority | TASK-001 | VERIFY-001 | PR #198 exact-head CI |
| REQ-002 | 确定性验证正负边界 | MODIFIED | ADK regression | existing test and validation path | ACC-002 | 全套回归及 source-context 预算无回退 | TASK-002 | VERIFY-001 | ADK main CI 38893064699 |
| REQ-003 | 将源码发布事实与真实效果资格隔离 | ADDED | ADK canonical change record | verify/report/evidence | ACC-003 | 原始 CI/Release 可追溯且 review 未伪造 | TASK-003 | VERIFY-002 | release v8.0.20 and Root integration |

## 安装范围与依赖边界
- 既有 core / optional 不变；不增加任何外部 Skill Pack、付费 API、MCP 或运行时依赖。
- 实际发布为 ADK v8.0.20，来源固定为 61ff6079dc1d994ac33fbd07a0f069d80b39341d。

## Prompt 回归证据计划
- 原有确定性语料和专项断言可证明 source 语义；未运行真实模型的 before/after，应记录 not-measured。
- 原生 Skill 发现、真实 Token、回归和人工返工需另由 G21/G22 完成。

## 收敛模式与退出条件
- Source software: protected PR #198, main 61ff6079dc1d994ac33fbd07a0f069d80b39341d, hosted CI、不可变 Release 均已验证。
- Change governance: 文本/证据结构补齐，独立 Human Reviewer **尚无 GitHub review 记录**；在真实审核前保持 active、不得 archive 或声称 full review PASS。
- 外部效果：继续由原 G21/G22/LTA 路径单独提供，不在本包提升资格。

## 备选方案与取舍
- 拒绝复制 Addy/Matt/pstack Skill Pack 或新增第二编排系统。
- 采用既有 ADK 能力的窄范围增强和确定性回归，未声称效果提升。

## 风险与回退
- 最大风险是将源码全绿误解释为真实模型、宿主和现场已验证；统一保持 not-measured。
- 回滚通过 Git revert 可恢复代码和文档，不修改外部签名、旧 Release 或产品资格。
