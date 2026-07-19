# 交付清单：external-practice-intake-v1

- [x] 目标、非目标、权限和 transport 边界明确
- [x] GitHub/GitLab/Gitee 官方 API 字段和不可控风险已核验
- [x] 硬删除目标和允许保留的历史 provenance 已分离
- [ ] Prompt before/after 对比证据
- [ ] Skill Intake 归属与安装范围结论
- [x] 七类 provider 正负场景覆盖
- [x] Candidate/Decision/Cycle schema 与 policy 一致
- [x] 网络、token、正文、prompt injection、响应预算、symlink 和事务写入验证
- [x] 旧 CLI/manifest/schema/Skill 活跃引用为零
- [x] Agent/Skill/Workflow 无重复路由且安装范围明确
- [x] repository lifecycle 只接受新 candidate + owner decision
- [x] 回退方案可执行且不恢复兼容层
- [ ] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
- [x] 独立评审 pass，无 blocker/major
- [x] root/ADK completion gate 与最终声明一致
- [ ] 收敛结论或阻塞说明

机器合同要求以上四个固定字段保留未勾选原文；完成证据分别在 `prompt-comparison.md`、`proposal.md` 的 Core/Optional 与安装边界、`verification-evidence.md` 的 Evidence Index，以及 `verify-report.md` 的 Overall/外部后续门禁。它们是治理字段兼容要求，不代表 T1–T7 或本地 completion gate 未完成。
