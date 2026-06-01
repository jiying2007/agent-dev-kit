# Checklist: workflow-agent-contract-standardization

- [ ] Prompt before/after 对比证据
- [ ] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
- [ ] Skill Intake 归属与安装范围结论
- [ ] 收敛结论或阻塞说明

## 审查项
- [x] Workflow profile 闭包按适用 profile 过滤。
- [x] Workflow 命令只允许仓内 `scripts/` 或 `tests/` 路径。
- [x] Agent handoff 与 default skills 引用已登记资产。
- [x] Catalog 输出包含 Agent 和 Workflow 矩阵。
