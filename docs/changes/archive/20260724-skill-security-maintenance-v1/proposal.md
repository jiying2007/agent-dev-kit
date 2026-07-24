# 变更提案：skill-security-maintenance-v1

## 背景
- ADK 已有 Agent Skills portable contract、OWASP Agentic Top 10 ASI01-ASI10、MCP provenance 和第三方 Skill intake，但 Skill 行为层尚无 AST01-AST10 显式 crosswalk。
- 2026 年 Agent Skills 实证研究表明，稳定行为契约与本地 binding 的维护模式不同；当前 manifest 没有统一记录 upstream revision、行为 diff、binding diff、effect/use 和 retire/refresh 日期。
- VS Code/GitHub Copilot 已支持 `.agents/skills` 等目录，但当前缺少真实 use case；按建议只记录 target watch，不新增 direct target。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：Skill 的供应链安全和维护新鲜度证据分散，无法用同一 contract 判断恶意 Skill、过权、漂移、跨平台复用和长期失效。
- 触发证据：现有 `skill_reproducibility_contracts.json` 缺 AST10、stable/local diff、use/effect 和 retire evidence。

## 目标
- 新增 AST01-AST10 crosswalk，映射现有 provenance、permission、sandbox、scan、governance 和 target conformance 控制。
- 新增 `skill-maintenance-evidence-v1`，要求 upstream revision/digest、stable behavior diff、target-local binding diff、use/effect、last verified 和 retire/refresh due。
- 新增 VS Code/GitHub Copilot watch entry，保持 `runtime_enabled=false`，没有 smoke/use case 不新增 target。
- 扩展 ecosystem standards 正负 fixture 和 checker。

## 非目标
- 不采用 OWASP 提议的 Universal Skill Format，不声明 OWASP 认证。
- 不给 55 个内部 Skill 伪造上游 revision 或使用次数。
- 不安装第三方 Skill，不新增 GitHub Copilot direct target，不启用 vendor-only `context: fork` core semantic。

## 上下文充分性检查
- [x] 已明确安全/维护字段和适用边界
- [x] 已识别规范成熟度、供应链、target-specific metadata 和数据伪造风险
- [x] 已明确 checker/fixture/test
- [x] 未知使用效果保持 `not-measured`，不得填充虚假数字

## Core/Optional 边界检查
- [x] 治理 contract 属于 core
- [x] vendor target/watch 属于 optional/disabled
- 归属结论：扩展现有 `skill_reproducibility_contracts` 和 ecosystem gate，不创建新 Skill。

## 变更重复性检查
- 已检索 Agent Skills portable contract、第三方 skill domain policy、OWASP ASI crosswalk 和 target contracts。
- 本次复用现有 checker；AST 是 Skill 行为层，不能用 Agent-level ASI 完全替代。

## Breaking Change 检查
- [x] 否：新增 method-only contract 和 fixture，不改变现有 Skill frontmatter/安装格式
- [ ] 是：涉及兼容性破坏

## Spec 链路检查
- requirements 基线：本提案与外部实践候选报告 3.9、3.10、4.1 节。
- design 决策：本 change `design.md`。
- tasks 追溯关系：本 change `tasks.md`。

## 安装范围与依赖边界
- 安装范围：global-ready method-only governance。
- 依赖边界：现有 JSON manifest/checker/fixture；不新增 vendor CLI、runtime 或网络。

## Prompt 回归证据计划
- 不修改 prompt。
- 负例保留：AST coverage 不完整、maintenance evidence 缺 digest/retire、watch runtime 被启用、vendor-only 字段提升为 core。

## 收敛模式与退出条件
- 当前模式：planning。
- 退出条件：source refs、contracts、fixture、checker、测试和文档一致性通过。

## 备选方案与取舍
- 方案 A：把所有新字段加到 `manifest.json` 每个 Skill 条目。
- 方案 B：先定义独立 evidence contract，只对外部派生/复用/晋级候选要求实例证据。
- 选择 B：避免给内部 Skill 伪造 provenance，也避免破坏 portable manifest。

## 风险与回退
- 风险：把未稳定 AST 项目当正式标准、字段形式主义、重复 ASI 控制、target 扩张。
- 控制：source 状态为 observe、method-only、runtime disabled、crosswalk 引用本地控制而不复制正文。
- 回退：移除新增 source/candidate/contract/fixture；现有 ASI、portable Skill 和 target contract 保持不变。
