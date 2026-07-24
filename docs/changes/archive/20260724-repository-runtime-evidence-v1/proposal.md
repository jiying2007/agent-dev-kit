# 变更提案：repository-runtime-evidence-v1

## 背景
- Software M5 已有 60 条 `prompt/category/expected_skill/expected_safe` 路由任务和双 runtime campaign，但该证据只能证明路由与安全分类。
- 2026-07-22 外部实践复核显示，Inspect SWE、SWE-bench-Live、AgentLens、SecCodeBench、SecureVibeBench 和 token 成本研究提供了互补方法：真实仓库沙箱、任务新鲜度、过程质量、功能优先安全 oracle 和跨 trial 成本分布。
- 用户于 2026-07-23 明确授权按建议吸收落地；授权不包含付费调用、外部容器执行、凭证使用或伪造现场结果。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：ADK 缺少平台中立、可验证、默认不执行外部 runtime 的真实仓库评测证据合同。
- 触发证据：现有 `software_m5_eval_tasks.jsonl` 只包含路由标签；M5 状态仍被 `runtime_campaign` 和真实仓库证据阻断。

## 目标
- 新增 repository-runtime contract、冻结任务 metadata、可选 adapter contract、结果 certifier 与 CLI。
- baseline 必须记录 customization isolation；无法隔离时标记 `not-comparable`，不得计入效果结论。
- 结果同时验证功能、安全、过程质量、trace、token/cost 分布和任务 provenance。
- 为 SWE-bench-Live 新鲜度和 SecCodeBench/SecureVibeBench 安全 canary 提供 clean-room metadata contract，不复制外部任务正文。

## 非目标
- 不安装 Inspect/Inspect SWE，不执行外部 benchmark 容器，不新增 runtime SDK。
- 不运行付费 Codex/Claude campaign，不声称真实仓库 campaign 已通过。
- 不替换现有路由 campaign，不把 benchmark 得分当作产品认证。
- 不存储 raw prompt、secret、未脱敏 trace 或外部仓库正文。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（沙箱、网络、凭证、任务许可证、成本、可比性）
- [x] 已明确验证命令与通过标准
- [x] 外部执行条件不足时保持 contract/fixture-ready，不伪造 runtime evidence

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [x] 外部 runtime adapter 属于 optional
- 归属结论：contract、certifier 和 fail-closed gate 为 core；Inspect SWE 只保留 disabled-by-default adapter metadata。

## 变更重复性检查
- 已检索 `campaign.py`、`evaluation.py`、`effect_eval_contract.json`、`trace_eval_contracts.json` 和 Software M5 change。
- 本次差异：现有 campaign 评估路由分类；本变更评估真实仓库修改 outcome 和过程证据，不复刻旧 runner。
- `knowledge/L2-domain/lessons.md` 不存在；对相关关键词的历史 lessons 检索为负结果，未伪造经验条目。

## Breaking Change 检查
- [x] 否：新增独立 contract/CLI，不改变现有 `eval run/campaign/certify` 语义
- [ ] 是：涉及兼容性破坏

## Spec 链路检查
- requirements 基线：本提案与 `reports/external-practice-search-and-absorption-candidates-2026-07-22.md`。
- design 决策：本 change `design.md`。
- tasks 追溯关系：本 change `tasks.md`。

## 安装范围与依赖边界
- 安装范围：contract/certifier `global-ready`；真实 task/report `project-bound`。
- 依赖边界：Python 3.8+ 标准库和现有 ADK manifest；不新增 package、network、credential 或 runtime dependency。

## Prompt 回归证据计划
- before：现有路由 campaign 只能得出 route/safety。
- after：冻结的 repository report fixture 同时包含 outcome/process/resource/isolation 证据。
- 失败样例：缺 isolation、lucky pass、功能未过、安全未过、cost/token 缺失、task/revision/digest 漂移分别保留负 fixture。

## 收敛模式与退出条件
- 当前模式：planning；需求、设计和 tasks 完成后进入 execution。
- 退出条件：contract、CLI、正负 fixture、定向测试和 full regression 通过；真实 campaign 保持 `not-run` 直到另行批准。

## 备选方案与取舍
- 方案 A：扩展现有路由 campaign，使其同时执行仓库任务。
- 方案 B：新增独立 repository-runtime contract，并仅在 M5 集成层组合结论。
- 选择 B：避免混淆路由准确率和工程 outcome，也避免让可选 runtime 依赖污染 core。

## 风险与回退
- 风险：外部任务许可证与容器供应链、基线未真正隔离、token 成本失控、trace 泄密、伪造通过报告。
- 控制：版本/digest pin、默认无网络、凭证不入报告、逐结果重算、raw trace 禁止、缺证据 fail closed。
- 回退：移除新增 contract/CLI/fixture/M5 integration；原路由 campaign 和已有认证状态保持不变。
