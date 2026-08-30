# 设计说明：adk-platform-convergence-v1

## 架构影响
- D1：`llm_agent` 保持 Practice Observatory；ADK 保持 Asset Compiler/Policy/Eval/Release；外部 runtime
  负责 thread/model/tool/checkpoint/concurrency。
- D2：引入统一 routing/workflow/asset IR；Markdown、catalog 和 target 输出为受门禁的派生视图。
- D3：Profile 由 capability closure 解析并生成 lock；core 与 embedded 物理/语义解耦。
- D4：Runtime Adapter SPI 只声明 capability/conformance，不在 ADK 启动外部 scheduler/server。
- D5：Evidence Graph 关联 source、decision、asset、bundle、runtime、trace、outcome、release 和 retirement。

## 数据与配置影响
- routing 增加 task mode、negative signals、mutation permission 和 abstain。
- runtime control 增加 task-mode artifact applicability，未知 mode fail-closed。
- workflow IR 增加 node I/O、transition、retry/timeout/cancel、idempotency、approval、checkpoint、rollback 和 evidence。
- 所有新 schema 都版本化、拒绝未知必填字段并提供 fixture migration。

## 兼容性与迁移方案
- 先提供 parser/validator 和双格式只读验证，再切 canonical writer；禁止长期双写。
- existing routing positive fixtures、Profile export 和 target contract 是兼容基线。
- 组合否定、未知 task mode、缺 runtime evidence 是新增 fail-closed 行为。
- 回滚到变更前 manifest/schema/parser，并保持 runtime feature disabled。

## 验证策略
- 定向：routing、profile coherence、workflow closure、runtime control、official docs、target contracts。
- ADK：strict validate、quick/full、security、benchmark、release check。
- 根仓：doc/token/maintainability、quick/full、runtime routing/health、harden readiness。
- 运行态：至少一个 native target conformance；R10 使用现有 campaign/certifier。
- 评审：subagent 交叉审查后主 Agent 独立复核并关闭 blocker/major。
