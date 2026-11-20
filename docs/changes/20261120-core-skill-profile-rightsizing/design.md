# 方案与回滚

- 将 Goal Authoring、并行 Agent、Worktree、上下文交接 四个条件性 Skill 从默认 core 的 include_skills 移出。
- 将同四项显式补入已有 personal-core、team-core、embedded-fullstack；经继承解析，其余七个 Profile 的 Skill 集合保持与基线完全一致。
- `adk-repo-drift-remediation` 和 `adk-after-action-review` 被现役 `runtime-routing` / `adk-delivery-gate` 的 core 工作流直接引用，必须保留默认 core；此项由真实 CI 契约失败暴露并已修正。
- 保留 Manifest 原有 Skill identity、内容和路由权威，避免破坏已有专用部署；仅默认 core 的发现面由 22 降至 18。
- 优化 runtime-router 的短路径，context-engineering 的职责界面，optional 组合治理的 KEEP/DEFER/MERGE/RETIRE 判据。保留高风险权限、原文证据、发布门禁。
- 回滚：整体 revert 该受保护 PR；已有部署不自动变更。需要使用专用能力时选择已存在的 Profile，而非安装全部 Skills。
