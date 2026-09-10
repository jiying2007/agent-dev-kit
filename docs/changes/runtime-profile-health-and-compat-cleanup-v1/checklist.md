# 检查清单：runtime-profile-health-and-compat-cleanup-v1

- [x] live `active-profile.env` 与 `managed-files.json` 的 profile 一致。
- [x] 已受管的 team-collab skill 不再因默认 build 而被误判为 unmanaged。
- [x] 未列入 managed-files 的 direct skill 仍触发 fail-closed 测试。
- [x] inactive/empty Superpowers plugin 不进入 team-collab build。
- [x] dry-run 仅包含受管状态更新与 Superpowers 退役路径删除。
- [x] apply 后 runtime health、footprint、routing 和 target checks 通过。
- [x] Prompt before/after 对比证据
- [x] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
- [x] Skill Intake 归属与安装范围结论
- [x] 收敛结论或阻塞说明
- [ ] ADK lock 与根仓 release evidence：等待当前 lifecycle worktree clean commit 后独立收口。
