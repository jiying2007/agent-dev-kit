# RC7 Token 与上下文治理 release baseline

## 问题陈述（单问题）

当前工作树新增 task-cost profile，并修改 Token、上下文和交付门禁。`templates/` 属于 mapped asset；若只提交实现而继续沿用 RC6 release source，根仓 current-status consistency 会正确拒绝。必须建立更高的 `3.1.0-rc.7` prerelease baseline，不能覆盖或复用 RC6 身份。

## 上下文充分性检查

- 已读取 RC6 source/evidence 提交模型、artifact rehearsal、根仓 current-status checker 与当前四仓状态。
- checksum-bound RC6 artifact 仍在本机，受支持 Python 3.11/3.12 pinned images 可用。
- 四仓 fetch 后均为 `0 behind / 0 ahead`；用户明确授权本地提交和 push。

## Core/Optional 边界检查

本次 task-cost、Token/context receipt 与 release gate 都是平台中立控制面，归属 core；不新增 optional skill、MCP runtime、plugin、hook 或外部服务。

## 变更重复性检查

复用现有 task-cost CLI、release build/rehearse、local-CI parity、Software M5 policy、Knowledge Hub candidate 和 Codex source-to-live 链路；不创建第二套版本、发布或归档工具。

## Breaking Change 检查

不删除或重命名公开 API。RC7 是向后兼容的 prerelease 增量；工作树门禁新增显式模式，但默认 release 语义保持 fail closed。

## Spec 链路检查

需求由两个 Token/context change 工件承载；本变更补齐版本、迁移、release source、artifact/rehearsal、evidence commit 与根仓 baseline 的可追溯闭环。

## 安装范围与依赖边界

- release build 与 rehearsal 只写 `/tmp` 隔离目录；不上传 artifact。
- Codex source-to-live 已有 plan/apply/check 证据，本轮不扩大到其他 runtime。
- 不读取或输出凭证，不执行 tag、远端 Release、付费 runtime campaign 或 active promotion。

## Prompt 回归证据计划

本变更不新增 runtime prompt；以 deterministic routing、skill trigger、task-cost 正负测试、Python 3.11/3.12 full parity 和 Codex 五 profile smoke 作为语义非回归证据。

## 收敛模式与退出条件

- 将 ADK 版本从 `3.1.0-rc.6` 提升到 `3.1.0-rc.7`。
- 固化 Token/context 实现、测试、迁移说明和 campaign contract。
- 从 exact source commit 双构建一致 artifact。
- 以 checksum-bound RC6 artifact 执行 RC6→RC7→rollback rehearsal。
- 固化 evidence commit，并同步根仓 gitlink、lock、current-status、policy 与 release evidence。

### 非目标与授权边界

- 不创建 tag、远端 Release、PR、merge 或 rebase。
- 不上传 artifact，不执行双 runtime 付费 campaign，不声明 Software M5 certified。
- 不提升 Knowledge Hub active 状态，不提交个人笔记或无关工作树。
- 用户已明确授权本地提交和现有远端分支 push。

### 退出条件

- 版本身份、strict/release/security、受支持 Python 3.11/3.12 full parity 全部通过。
- exact source commit 双构建字节一致，checksum 与 source file count 可复核。
- RC6→RC7 升级、candidate rollback、RC6 managed hash 恢复通过。
- source→evidence commit 的 mapped path diff 为空。
- 根仓 `--release-clean --full` 通过，四仓推送后本地 HEAD 与 upstream 一致。
