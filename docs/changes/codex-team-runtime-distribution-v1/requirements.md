# Requirements

## Goal

在不向团队公开 `agent-dev-kit` 实现源码的前提下，把选定 Profile 的 Skill 作为可复现、可校验、可回滚的 Runtime Bundle 交付给团队 Codex 用户。

## Scope

- 新增 platform-neutral、skills-only Runtime Bundle 构建命令。
- `team-core` 默认包含跨团队交接 Skill，消除 profile 与团队交付 runbook 的安装缺口。
- Runtime Bundle 包含版本、Profile、逐资产来源和 SHA256，但不包含 ADK Python、测试、内部变更证据或 Git 元数据。
- 团队发行仓通过 plan/apply/rollback 导入 Bundle，并通过 source-to-live 写入成员 `~/.codex`。

## Non-goals

- 不把 Codex 加入 ADK direct tool target。
- 不隐藏交付给成员的 `SKILL.md`；需要保密的执行逻辑应留在受控服务端。
- 不直接写成员运行目录，不自动 commit、push 或发布远端 Release。
- 不修改个人 `~/codex` 中已有的用户变更。

## Acceptance

- 相同 manifest、Profile 和 optional Skill 输入生成字节一致的 Runtime Bundle。
- Bundle 不包含 `src/agent_dev_kit`、`tests`、`.github`、`docs/changes` 或顶层 ADK source distribution。
- Bundle 拒绝未知 Profile、重复 optional Skill、symlink、路径穿越、摘要漂移和版本漂移。
- `team-core` 解析结果包含 `adk-cross-team-handoff`，且该 Skill 不再依赖 optional install。
- 团队仓能导入 Bundle；成员通过单个 `setup` 命令完成构建、plan/apply 和 drift 检查，底层仍保留 receipt 回滚能力供维护者处置故障。
- ADK 定向/严格/完整回归和团队仓测试提供新鲜证据。

## Rollback

- 回退 Runtime Bundle 命令、manifest/profile 变更和对应测试。
- 团队仓使用导入 receipt 回退 vendor/manifest，再使用 source-to-live receipt 回退成员运行目录。
- 保留上一版 Bundle、checksum 和团队发行版本作为恢复锚点。
