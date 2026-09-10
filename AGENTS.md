# agent-dev-kit 仓库规则

`agent-dev-kit` 是平台中立的 Agent/Skill/Workflow/Profile 生产资产包；`embedded-fullstack` 是业务 profile。详细生命周期、R1–R8、恢复协议和 Gate 选择见 `docs/agent-operating-rules.md`。

## 1. 进入仓库即遵守

- 修改前读取目标目录局部规则、README 与相关实现；默认简体中文，技术标识保留英文。
- 非平凡实现、长任务、失败恢复或 Gate 变更必须先有 `docs/changes/<id>/requirements.md`、`design.md`、`tasks.md`；范围变化先更新这些产物。
- 行为变更必须增加或更新确定性、非交互测试；不弱化失败用例。删除或公共 API 变化前检索调用点，并记录迁移与回滚。
- 根因未明时 read-only-first、单变量实验，失败路径写入 `negative-results.md`；没有新鲜验证证据不得声明完成。
- dirty 变更属于用户，不回退、覆盖或清理无关内容；不自动 commit/push/merge/rebase。

## 2. 结构与 SSOT

- `manifest.json`：产品边界、target、profile、agent、skill、workflow 与 MCP 的唯一结构化 Manifest SSOT；禁止新增平行 Manifest 镜像。
- `agents/`、`skills/`：core 资产；`optional-skills/`：仅显式请求时安装/导出；`src/agent_dev_kit/`：typed core；`scripts/devkit.sh`：稳定入口；`docs/changes/`：可审查变更证据；`tests/`：回归。
- ID 和文件名用 kebab-case。`SKILL.md` 必须含 `name/description/triggers/non_triggers/inputs/outputs/constraints`，正文只保留触发、流程、输出契约，长背景放 `references/`。
- 参考仓只作治理输入；生产资产必须由 manifest 和 handoff fragment 声明。能力必须明确属于 `core` 或 `optional-skills`，不得保留重复 skill/profile。

## 3. 命令、安全与质量

- 本工作区所有 shell 命令经 `rtk`；手工源码、脚本、配置、文档修改必须用 `apply_patch`。
- Shell 使用 bash、`set -euo pipefail`、LF 与 kebab-case；新增 Python 工具进入 typed core，包装脚本只转发。
- 不安装到未声明/未审查的 runtime，不硬编码凭证，不把不可信输入拼进命令或外部写操作。MCP 默认为空/禁用，启用需显式审查。
- 一个 change 聚焦一个真实问题；breaking change 必须声明影响、迁移和回滚。

## 4. 高频流程与验证

```bash
rtk scripts/devkit.sh validate --quick
rtk scripts/devkit.sh validate --strict
rtk scripts/devkit.sh export --target claude-code --profile core --out dist --clean
rtk scripts/devkit.sh release check
rtk tests/run_all.sh
```

- workflow 变更走 `propose -> apply -> verify -> review -> archive`，保持状态门禁。
- 小改动至少定向测试；共享逻辑、manifest、installer、release、安全或 lifecycle 变更升级到完整回归。
- PR/交付需含变更摘要、验证证据、风险与回滚、影响文件。提交格式 `<type>(scope): <中文动词摘要>`。
