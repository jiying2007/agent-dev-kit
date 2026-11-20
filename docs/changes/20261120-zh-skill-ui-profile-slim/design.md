# 实施设计

1. 以 `manifest.json` 为唯一 Skill/Profile 身份源；Codex UI 文案存各 Skill 同目录的 `agents/openai.yaml`，不新建平行语言目录或路由表。
2. 保留 `SKILL.md:description` 与既有触发/非触发词，避免界面翻译改变语义选择或自动授权；可选 `default_prompt` 保留明确 `$skill-name`。
3. `large-refactor` 继承 `core` 并显式引入 `adk-planning-execution-loop` 与 `adk-code-simplification`；嵌入式重构通过两个现有 Profile 的显式组合。
4. `personal-core` 仅增加发布准备；低频记忆/归档/成长仍保留现有团队/研究 Profile，不删除方法或转换为兼容别名。
5. 通过源 Manifest 全覆盖测试、Profile 契约、导出/打包、完整 CI 及精确发行验证。Codex downstream 仍须经其签名 source-to-live handoff，禁止手改用户目录。
6. 后续候选身份合并另做生产行为/权限对照；没有真实 E2–E4 证据不将静态重叠等同无价值。

## 精确来源体积

使用当前候选 Git Tree 的各 Asset blob 大小，按现有 `profile_context_footprint` 的 entry/support 边界复算并收紧 8 个 Profile ratchet；不把 `agents/openai.yaml` 当作模型初始上下文。真实 token / Codex UI 显示仍需下游执行证据。所有 65 个已变化 Skill 均递增补丁版本，避免 Codex 导入时出现 changed skill but unchanged version。

## Codex 调用策略边界

Codex UI metadata 与 ADK 机器路由并非同一权威。为防止本来仅供显式调用的 supporting/governance/fallback Skill 被 Codex 依默认 true 隐式选用，7 个非 primary Skill 的 `agents/openai.yaml` 标注 `policy.allow_implicit_invocation: false`；其余主入口省略默认 true。更改仅收紧隐式调用，不扩大工具/执行权限。
