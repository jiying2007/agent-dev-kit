# 实施与验证

- [x] 固定 v11.4.13 主线身份和完整 Manifest/Skill/Profile 来源。
- [x] 比较变更前后八个 Profile 的解析集合：仅 core 移出六项，其余完全一致（源码构造检查）。
- [x] 更新 Skill 路由快路径、上下文边界和组合精简判断；复用既有 profile coherence 回归。
- [ ] Python 3.12 严格验证、全量回归、静态安全、CodeQL、Platform 与发布检查（以最终 PR HEAD 的 GitHub Actions 为准）。
- [ ] 受保护 PR 合并及 fresh-main CI；如通过，按既有不可变发布工作流生成 v11.4.14，Root 消费另做独立验证。
- [ ] 真实宿主任务成功率、Token、时延 A/B：not-measured；不使用 Codex/ChatGPT Work 额度冒充效果数据。
