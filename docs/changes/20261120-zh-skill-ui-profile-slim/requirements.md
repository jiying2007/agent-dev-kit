# Skill 中文展示与 Profile 精简需求

- 目标：Manifest 中全部 Core/Optional Skill 的 Codex UI 名称和短描述统一中文，保留原 Skill identity、权限及调用策略。
- 目标：通用 `large-refactor` 不隐式包含嵌入式专业资产；`personal-core` 不默认附带记忆/归档/成长复盘。
- 验收：65/65 `agents/openai.yaml` 有稳定中文名称、25–64 字符中文描述；现有 policy 不丢失。
- 验收：`large-refactor` 仅增加长任务执行与代码简化；`personal-core` 相对 `core` 仅增加发布检查。
- 边界：不宣称 Codex live 已同步、模型效果提升或 Token 实际节省；设备/发布权限与高风险门禁不变。
