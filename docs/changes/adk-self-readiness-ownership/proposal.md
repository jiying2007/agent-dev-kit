# 变更提案：adk-self-readiness-ownership

## 背景

Harness readiness 对 ADK 自身的报告为 `partial`：根 `AGENTS.md` 超过 180 行索引预算，六个适用维度缺 owner/验证日期，并且没有机械可发现的 ownership 文件。这些是仓库真实 evidence gap，不能通过调整评分隐藏。

## 问题陈述（单问题）

本变更只解决一个问题：**ADK 自身的 Agent 入口与 ownership/freshness 元数据没有达到它向目标仓提出的同一就绪合同。**

## 目标

- 将根 `AGENTS.md` 收敛为不超过 180 行的立即执行索引，详细规则下沉到受治理文档且不丢失语义。
- 增加根 `OWNERS`，声明当前维护责任和审查边界。
- 增加 `.adk/harness-readiness.json`，记录六个适用维度的 owner 与当前验证日期。
- 保持 MCP 不适用和 `field_evidence_status=not-verified`，不为取得 pass 扩大外部系统或现场声明。

## 非目标

- 不新增 CODEOWNERS 中无法确认的 GitHub 身份映射。
- 不改变 Agent/Skill prompt、权限、运行时或外部写路径。
- 不把 repository readiness pass 等同于 M4/M5、runtime 或 field 认证。

## 上下文充分性检查

- [x] 已明确输入/输出与接口契约
- [x] 已识别入口拆分、ownership 冒认和 freshness 过期风险
- [x] 已明确 readiness 与文档/格式验证命令
- [x] 已确认 decision owner `leiwenjun`，未知 GitHub handle 不写入 CODEOWNERS

## Core/Optional 边界检查

- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：根入口、ownership 和 readiness metadata 是仓库级治理合同，不属于可选业务能力。

## 变更重复性检查

- 既有 `harness-team-readiness-v1` 明确把入口拆分和 ownership 列为独立建议，本 change 承接该建议。
- 不修改 Harness 检测算法，只让 ADK 自身提供真实证据。

## Breaking Change 检查

- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

`AGENTS.md` 保留所有立即执行硬边界和详细规则入口；规则正文移动但不改变含义。回退可恢复单文件布局，但会重新触发 oversized index blocker。

## Spec 链路检查

- requirements：本提案的入口预算、ownership、freshness 和非现场边界。
- design：`design.md` 的 index/detail 分层与 metadata 合同。
- tasks：`tasks.md` 的基线、迁移、正负检查和收口。

## 安装范围与依赖边界

- 安装范围：仅 ADK source repository，不进入导出 bundle 或用户运行目录。
- 依赖边界：Markdown、OWNERS 和 JSON metadata，不增加第三方依赖。

## Prompt 回归证据计划

- before：根 `AGENTS.md` 270 行且 readiness 为 partial。
- after：根索引不超过 180 行，详细规则仍可定位，readiness 六个适用维度通过、MCP 维度保持 not-applicable。
- 不改 Agent/Skill prompt 行为；以规则关键词存在性与 readiness 报告为回归证据。

## 收敛模式与退出条件

- 当前模式：planning；change governance 通过后 execution。
- 退出条件：规则无丢失、索引预算通过、OWNERS/metadata 可发现、readiness 结果符合边界、full regression 无相关回归。

## 风险与回退

- 规则丢失：迁移前后对关键 R1-R8、生命周期、Gate 和资产边界关键词做机械比对。
- owner 冒认：只使用已在当前仓与 Hub 记录的 decision owner，不推断 GitHub 用户名。
- freshness 过期：90 天后 readiness 自动降级，促使 owner 重新验证而不是永久 pass。
