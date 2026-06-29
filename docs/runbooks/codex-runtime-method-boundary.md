# Codex Runtime Method Boundary

## 目标

将 Codex 工作流运行层中的可迁移方法抽象为 ADK method-only 规则，避免把外部 runtime、全局安装、hook、tmux 会话或用户目录状态带入 ADK core。

## 可吸收方法

- goal state：目标必须包含范围、非目标、成功标准、验证命令和阻塞条件。
- worktree discipline：只有隔离收益大于状态成本时才创建 worktree，并记录基线、scope_write、must_not_touch 和清理条件。
- doctor evidence：运行态健康检查必须输出可审查证据，而不是只给自然语言结论。
- release evidence：发布或交付必须记录版本、输入、输出、校验和回退路径。
- state scope：会话状态、项目状态和长期规则分层保存，避免把临时结论提升为全局规则。

## 禁止项

- 不运行外部 runtime、daemon、hook、MCP server 或全局安装命令。
- 不直接写入 `~/.codex`、用户 shell 配置、tmux 会话或插件目录。
- 不复制外部脚本实现；只保留可验证的字段、门禁和工件结构。

## ADK 落点

- `skills/adk-runtime-router/SKILL.md`：任务入口必须声明 required artifacts 和 fallback evidence。
- `skills/adk-worktree-governance/SKILL.md`：worktree 只在明确隔离收益和清理条件后使用。
- `skills/adk-verification-before-completion/SKILL.md`：完成声明绑定证据、回退和运行边界。
- `docs/runbooks/upstream-intake.md`：外部来源先做 intake，目标仓变更走 harden -> verify -> handoff。

## 验收

- method-only 资产能通过 ADK validate/test。
- 任何运行态写操作都有显式 tool target、approval boundary 和回滚路径。
- adoption matrix 中指向 `agent-dev-kit` 的完成项必须至少列出一个存在的 `agent-dev-kit/...` 证据路径。
