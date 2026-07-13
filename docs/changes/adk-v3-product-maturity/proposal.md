# Proposal: adk-v3-product-maturity

## 问题陈述

ADK 已具备大量 Agent、Skill、Workflow 与治理契约，但公开 CLI、发布链路和运行效果证据仍存在语义缺口：release workflow 构建未声明的 Codex direct target，部分 ops/perf/security/monitor 命令只输出成功或主机状态，不代表资产平台能力，安装链路也缺少强制 plan、receipt 和原子回滚。

## 目标

- 将 ADK 明确收敛为平台中立的资产编译、分发和评测平台，不扩建 LLM runner。
- 发布 3.0.0 Major 接口，删除无真实实现或不属于资产平台的入口。
- 使用结构化 manifest 访问层，消除关键路径中的 ad-hoc `awk`/`grep` 解析。
- 让 install、export、release、benchmark 和 security 的成功状态可由行为证据验证。
- 为 Codex external handoff 与 Claude Code direct target 建立真实运行时评测入口。

## 非目标

- 不实现模型调用、会话存储、checkpoint 或完整 Agent orchestration runtime。
- 不把 Codex 重新加入 direct export targets。
- 不用模拟设备结果替代真实硬件 production readiness。
- 不修改 `llm_agent` 中已有 dirty 参考子仓。

## Breaking Change

本变更发布为 3.0.0：`convert` 政策性替换为 `export`；安装改为 plan/apply/rollback；删除 monitor、ops、perf optimize 和 security harden；manifest 与 CLI 均升级 schema。迁移与回滚必须在 release gate 前验证。

## 完成条件

- 新增回归测试先复现 release/CLI 契约缺口。
- ADK full suite、release build、安装回滚和至少一个已认证运行时的完整 baseline/adk 对照通过；未认证运行时必须记录为 `not-run`。
- 根仓同步 gitlink 后通过适用的 root gate，并对 source-to-live 做映射判定；没有映射资产变更时禁止为了取证执行无意义 live 写入。
