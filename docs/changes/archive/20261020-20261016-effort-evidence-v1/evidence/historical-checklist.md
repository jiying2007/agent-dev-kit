# 现有路由导出 E0-E3 保守投入等级，调试审查证伪，A/B/A/B 性能证据纪律 — Checklist

- [x] 关键场景覆盖
- [x] 风险项评估完成
- [x] 回退方案可执行
- [x] 验证证据可追溯
- [x] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
- [x] Canonical Change Contract 追溯关系完整
- [ ] 评审结果为 pass（无 blocker/major 未闭环）
- [ ] Prompt before/after 对比证据
- [x] Skill Intake 归属与安装范围结论
- [x] 收敛结论或阻塞说明

## Gate classification
- 机械/结构：源码及发布链有真实成功收据。
- 真实 Owner 语义结论：NOT-RUN，GitHub PR #198 reviews 为空（来源事实）；单人维护可真实签署 Owner verdict，不得冒充其他 reviewer。
- Model/Native/Field：NOT-MEASURED，G21/G22/LTA 分离。
