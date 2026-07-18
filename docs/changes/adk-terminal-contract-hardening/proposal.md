# 变更提案：adk-terminal-contract-hardening

## 背景

2026-07-18 终态审计确认 ADK 本地功能和全量回归基础较强，但性能包装门禁、安装模式、manifest schema 与支持环境之间存在声明和执行不一致。若继续保留这些差异，release candidate 可能在局部门禁显示通过时仍违反自己的合同。

## 问题陈述（单问题）

本变更只解决一个问题：**终态相关机械门禁没有完整执行其所声明的合同，导致假绿或跨层语义漂移。** Harness 专属判定缺陷继续在既有 `harness-team-readiness-v1` change 内修复，真实 runtime 与 field certification 保持外部 blocker。

## 目标

- 根性能包装器把 quick timing 交给 ADK strict budget checker，超预算必须失败。
- `manifest.json`、YAML mirror、schema、installer、CLI 与文档只声明当前真实支持的 copy 安装模式。
- 对 install、routing 和 dependencies 等关键 manifest 对象增加可执行 schema 约束和负向回归。
- 提升 Python 与 PyYAML 支持下限，避免把 EOL 运行环境作为当前发布基线。
- 保留 release、rollback、target export/install 和 Python 3.12 现有通过能力。

## 非目标

- 不实现新的 symlink 安装事务。
- 不把 ADK 改造成 LLM runtime。
- 不执行带凭证或费用的 runtime campaign，不伪造远程 CI、Scorecard 或现场证据。
- 不修改 reference subrepos、用户目录运行资产，不重写 git history，不创建 tag/push/publish 或修改远端状态。

## 2026-07-18 Scope Steering

owner 后续明确授权本地 commit、版本推进与 release rehearsal。范围因此增加 `3.1.0-rc.3` 版本同步、已提交快照制品构建、rc.2 → rc.3 回滚演练和根仓证据锁定；不扩展为 push、tag、GitHub Release、远端 CI 状态、live apply、付费 runtime 或 field certification。

## 上下文充分性检查

- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（兼容、性能、安全、发布）
- [x] 已明确验证命令与通过标准
- [x] 信息不足项已限定为外部认证，不阻塞本地合同修复

## Core/Optional 边界检查

- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：manifest、installer、schema、性能和支持环境是所有 target 共用的控制面合同，必须属于 core。

## 变更重复性检查

- 已复核 `adk-v3-1-rc2-target-conformance`、`adk-v3-product-maturity` 和当前性能预算实现。
- 本次差异：不重复建设安装或性能系统，而是修复 rc.2 后暴露的跨层声明漂移和外层门禁漏接。

## Breaking Change 检查

- [ ] 否：不涉及兼容性破坏
- [x] 是：涉及兼容性破坏（必须补充迁移与回退计划）

Python 最低版本将从 3.8 提升；manifest 中失真的 `symlink` 默认值将改为真实支持的 `copy`；此前仅验证为 object 的关键 nested manifest 字段将开始拒绝缺失必填项、错误类型与未知属性。依赖旧 Python 的使用者需先升级解释器；自定义 manifest 必须先运行 strict validate，删除未声明扩展字段并按 schema 修正数组、布尔值和对象结构。显式请求 symlink 的调用此前已经被实现拒绝，本次只是让声明和文档与真实行为一致。回退可恢复 pyproject/CI/manifest/schema/docs，但会重新引入 EOL 支持或合同漂移，不能作为长期方案。

## Spec 链路检查

- requirements：本提案中的单问题、目标、非目标和验收标准。
- design：`design.md` 的 truthful-gate、typed schema、copy-only 和 supported-runtime 决策。
- tasks：`tasks.md` 的基线、红灯、实现、定向回归、全量验证和收口任务。

## 安装范围与依赖边界

- 安装范围：ADK core 与根仓只读/验证包装层；不写 live runtime target。
- 依赖边界：Python 标准库、现有 PyYAML/jsonschema、bash 门禁和 manifest；不新增运行时网络依赖。

## Prompt 回归证据计划

- 本变更不修改 Agent/Skill prompt。
- 以行为 before/after 替代：超预算 timing fixture、symlink 声明、未知/错误 manifest 字段和 EOL Python 声明在改前可穿透或漂移，改后必须被机械拒绝或统一。

## 收敛模式与退出条件

- 当前模式：planning；change governance 通过后进入 Level 2 execution。
- 本地退出条件：红灯证据、最小实现、定向测试、strict/security/release、quick/full 和根仓适用集成证据完整。
- 外部退出条件：remote CI/runtime/field 证据仍由 Software M5 certifier 管理，本变更不得代替。

## 风险与回退

- Python 兼容破坏：文档明确最低版本，CI 采用受支持矩阵；回退只用于短期紧急恢复。
- schema 收紧误伤：先从当前 manifest 生成正例，并为每个收紧对象增加独立负例。
- 性能环境波动：预算不放宽；记录子步骤 timing，优先减少重复工作。
- 安装行为：保持 copy transaction、receipt 和 rollback 语义不变，只校准声明层。
