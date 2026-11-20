# 实施设计

1. 以 `manifest.json` 为唯一 Skill/Profile 身份源；Codex UI 文案存各 Skill 同目录的 `agents/openai.yaml`，不新建平行语言目录或路由表。
2. 保留 `SKILL.md:description` 与既有触发/非触发词，避免界面翻译改变语义选择或自动授权；可选 `default_prompt` 保留明确 `$skill-name`。
3. `large-refactor` 继承 `core` 并显式引入 `adk-planning-execution-loop` 与 `adk-code-simplification`；嵌入式重构通过两个现有 Profile 的显式组合。
4. `personal-core` 仅增加发布准备；低频记忆/归档/成长仍保留现有团队/研究 Profile，不删除方法或转换为兼容别名。
5. 通过源 Manifest 全覆盖测试、Profile 契约、导出/打包、完整 CI 及精确发行验证。Codex downstream 仍须经其签名 source-to-live handoff，禁止手改用户目录。
6. 后续候选身份合并另做生产行为/权限对照；没有真实 E2–E4 证据不将静态重叠等同无价值。
