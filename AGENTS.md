# agent-dev-kit 仓库规则

`agent-dev-kit` 是平台中立的 Agent/Skill/Workflow/Profile 资产包；`embedded-fullstack` 是业务 profile。生命周期、R1–R8、恢复协议与 Gate 见 `docs/agent-operating-rules.md`。

## 1. 默认规则

- 修改前读目标目录规则、README 与实现；默认简体中文，技术标识保留英文。
- 非平凡实现、长任务、失败恢复或 Gate 变更维护 `docs/changes/<id>/{requirements,design,tasks}.md`。
- 行为变更需确定性、非交互测试；删除/API 变化先检索调用点并记录迁移、回滚。
- 根因未明时 read-only-first、单变量实验；失败写 `negative-results.md`，无 fresh 验证不声明完成。
- dirty 变更属于用户，不回退/覆盖/清理无关内容；不自动 commit/push/merge/rebase。
- Token/上下文默认 `balanced`：progressive disclosure、tool/skill deferred loading、稳定上下文前置、动态上下文后置、摘要带 raw pointer。高风险升级 `audit/L3` 原文；Low Token 仅 runtime overlay。细则见 `manifests/token_context_policy.json` 与 `adk-token-context-governance`。

## 2. 结构与 SSOT

- `manifest.json` 是产品边界、target/profile/agent/skill/workflow/MCP 的 Manifest SSOT；`manifests/` 仅放受测治理 contract，不形成产品镜像。
- `agents/`、`skills/` 是 core；`optional-skills/` 仅显式请求时安装/导出；`src/agent_dev_kit/` 是 typed core；`scripts/devkit.sh` 是稳定入口；`docs/changes/` 存证据；`tests/` 存回归。
- ID/文件名用 kebab-case。`SKILL.md` 含 `name/description/triggers/non_triggers/inputs/outputs/constraints`；正文留触发、流程、输出契约，长背景放 `references/`。
- 参考仓只作治理输入；生产资产由 manifest/handoff fragment 声明。能力明确属于 `core` 或 `optional-skills`，不得重复 skill/profile。

## 3. 安全与质量

- 本工作区 shell 经 `rtk`；手工修改源码、脚本、配置、文档用 `apply_patch`。
- Shell 用 bash、`set -euo pipefail`、LF、kebab-case；新增 Python 工具进 typed core，包装脚本只转发。
- 不安装到未审查 runtime，不硬编码凭证，不把不可信输入拼入命令/外部写；MCP 默认禁用，启用需显式审查。
- 一个 change 聚焦一个问题；breaking change 声明影响、迁移、回滚。

## 4. 验证

```bash
rtk scripts/devkit.sh validate --quick
rtk scripts/devkit.sh validate --strict
rtk scripts/devkit.sh export --target claude-code --profile core --out dist --clean
rtk scripts/devkit.sh release check
rtk tests/run_all.sh
```

workflow 变更走 `propose -> apply -> verify -> review -> archive`。小改跑定向测试；共享逻辑、manifest、installer、release、安全、lifecycle 变更跑完整回归。PR/交付给出摘要、证据、风险、回滚和影响文件；提交格式 `<type>(scope): <中文动词摘要>`。
