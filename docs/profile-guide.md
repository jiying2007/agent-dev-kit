# Profile 选择指南

## 如何选择 Profile

| 场景 | 推荐 Profile | 说明 |
|------|-------------|------|
| 通用开发 | core | 最小核心配置 |
| 个人 ~/.codex | personal-core | 精简核心 + 发布 |
| 嵌入式全栈 | embedded-fullstack | 驱动/组件/应用全覆盖（默认） |
| 准备发布 | release-hardening + embedded-fullstack | 叠加发布强化 |
| 大型重构 | large-refactor + embedded-fullstack | 叠加 API 稳定性 |
| 线上事故 | incident-response | 根因/复盘/恢复 |
| 团队协作 | team-core | 交接/验证/评审 |
| Spec 驱动 | openspec-driven | 需求/设计/任务链路 |
| 吸收参考仓 | research-intake | 候选筛选与审查 |
| 高风险变更 | artifact-gated-lite + core | 产物门禁 |

## 叠加规则
- 可叠加: 任意 optional profile 可叠加 core 或 embedded-fullstack
- 冲突: release-hardening 与 incident-response/large-refactor 互斥
- 默认: embedded-fullstack 适合大多数嵌入式开发场景
