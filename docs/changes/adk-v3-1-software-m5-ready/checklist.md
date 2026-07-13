# 交付清单：adk-v3-1-software-m5-ready

- [ ] 关键场景覆盖
- [ ] 风险项评估完成
- [ ] 回退方案可执行
- [ ] 验证证据可追溯
- [ ] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
- [ ] 评审结果为 pass（无 blocker/major 未闭环）
- [ ] Prompt before/after 对比证据
- [ ] Skill Intake 归属与安装范围结论
- [ ] 收敛结论或阻塞说明

## 当前判定

- 已完成：关键场景、风险、回退、证据链、代码审查、quick `15/15`、full `49/49`、
  两次 source build 一致性、wheel 隔离安装、`3.0.0 -> 3.1.0-rc.1 -> 3.0.0` 演练和根仓 certifier 集成。
- 待最终勾选：提交与远端核验。
- 明确保留：Prompt 实验与 Skill Intake 不属于本次产品控制面变更，不以伪造 before/after 或新增 skill 代替。
- 外部阻塞：Claude CLI 未认证，双 runtime campaign 保持 `not-run/blocked`。
