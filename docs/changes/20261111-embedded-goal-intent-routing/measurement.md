# Embedded Goal Skill 按意图路由 — v11.2.4

## 原因与取舍
- 当前 v11.2.3 的 `adk-planning-execution-loop` 仅在 `team-core` 可用；`embedded-fullstack` 的多阶段任务因此需要切换无关团队 Profile。
- **不**把该 Skill 加到通用 `core`，避免将其额外源码潜在负担扩大到个人/普通任务。
- 仅为 `embedded-fullstack` 增加既有 Skill，`large-refactor` 经继承自动获得；`team-core` 不变。Manifest / 路由场景标识双向一致，仍 `explicit-profile-required`、`workspace-write` 须有获批计划和范围证据。
- 仍保留一个 primary Skill；只在已批准的复杂多阶段任务按需加载正文。此修改不增加新的 Goal、Agent、计划器、守护进程或费用上限。

## 精确 Git 资产字节（非模型 Token）
已有 `skills/adk-planning-execution-loop/SKILL.md` 为 3711 UTF-8 bytes，按需 reference 为 3624 bytes。新增潜在来源表面：

| Profile | 资产数变化 | entry bytes 变化 | potential full source bytes 变化 |
| --- | ---: | ---: | ---: |
| core | 0 | 0 | 0 |
| team-core | 0 | 0 | 0 |
| embedded-fullstack | +1 | +3711 | +7335 |
| large-refactor | +1 | +3711 | +7335 |
| personal-core / other | 0 | 0 | 0 |

仅更新两个受影响 Profile 的精确 source-growth ratchet，没有百分比余量。原记录属于源码字节，不是目标运行时初始 prompt、Tokenizer、真实速度或费用测量。

## 安全与验收
- 只有已批准的多阶段实施任务才选择该 Skill；CI 等待、只读计划、小改动不应额外加载。
- 继承关系由 Manifest 的原生 profile resolution 检查验证，不复制 Skill 文件，不改变 `adk-goal-authoring` 的职责边界。
- `tests/test_profile_context_footprint.py` 的正/反例覆盖 embedded/large/team/core；既有 Source/Release/Runtime/Product 资格分离。
- 本变更的发布需受保护 main、fresh-main CI、immutable Tag 和正式 Release；Codex 已有的 provider lock 仍须独立导入并签名核验，不能以此声明其本机 live 已更新。
