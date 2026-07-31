# RC6 release baseline refresh

## 问题陈述（单问题）

`agent-dev-kit@bb6d65b` 已修改 `skills/` 与 `templates/` 映射资产，但根仓 release baseline 仍绑定 RC5 source commit `66a8c19`，导致 `check-current-status-consistency.sh` 正确失败。必须为当前源码建立新的、更高 prerelease 版本及可复核 release evidence，不能把两个 RC5 artifact 伪装成合法升级。

## 上下文充分性检查

- 当前 ADK HEAD、RC5 artifact、release/rehearsal 实现和根仓 consistency checker 已读取。
- RC5 exact artifact 及 checksum 仍可用。
- 本机有 digest-pinned 的 Python 3.11/3.12 local-CI images。
- 用户授权修复当前 release baseline；未授权 live runtime 写入、tag 或 GitHub Release。

## Core/Optional 边界检查

本变更只刷新 ADK core 的版本和 release evidence，不新增 optional skill、MCP runtime、plugin、hook 或外部服务。

## 变更重复性检查

复用现有 `release build`、`release rehearse`、Software M5 policy 和 source-to-live 状态机；不新增第二套 release 工具或并行证据格式。

## Breaking Change 检查

RC6 不新增 API 删除。版本提升用于封装 RC5 后的 MCP governance、远程 ADB/HIL skill 和架构模板变更；回退目标为 checksum-bound RC5 artifact。

## Spec 链路检查

需求、设计、任务、负结果、rehearsal、verify report 和根仓 release evidence 形成单一可追溯链路。release source commit 与 evidence commit 分离，避免验证报告进入自身 artifact hash。

## 安装范围与依赖边界

- release rehearsal 仅写 `/tmp` 临时 target。
- source-to-live 固定为 `required-pending-owner-authorization`。
- 不写 `~/codex`、`~/.codex`、凭证、远端 release 或 tag。
- Python 3.11/3.12 验证使用现有本地容器镜像；release artifact 不下载依赖。

## Prompt 回归证据计划

本变更不修改 prompt 语义。以 RC5 与 RC6 的 deterministic routing、skill trigger、template 和 full suite 结果作为 before/after 非回归证据。

## 收敛模式与退出条件

- retry budget：每个失败阶段最多 2 次。
- staleness threshold：45 分钟无新证据则重新审查计划。
- heartbeat：每阶段至少新增一项命令级证据。
- stop condition：full gate 60/60 pass；若需要 live apply、远端发布或新权限则停止为 blocked。
