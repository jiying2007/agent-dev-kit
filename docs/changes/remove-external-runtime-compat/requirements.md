# 需求基线：remove-external-runtime-compat

## 目标

- ADK 运行路由只选择 ADK 原生 Skill、Workflow 或项目专用流程，不再声明、安装或调用外部流程兼容 fallback。
- 保留根工作区对应参考仓及其采纳 provenance，继续作为只读外部实践输入。
- Codex 团队运行包重新导入后，不再包含外部流程兼容语义的 ADK Skill 文本。

## 非目标

- 不删除、同步、清理或改写根工作区对应参考子模块。
- 不重写历史 archive、既有评估报告或参考仓原文。
- 不自动 commit、push、merge 或绕过 clean-release/source-to-live 门禁。

## 验收标准

1. `skills/`、active `scripts/`、active `tests/` 和当前 pilot 文档不再把外部参考流程声明为 runtime fallback。
2. 删除 fallback sunset 矩阵及其专用检查脚本和测试；pilot readiness 独立校验 pilot 证据。
3. 显式包含旧外部 Skill 名称的需求、review 和调试请求仍路由到对应 ADK 原生 Skill。
4. ADK strict validation、路由回归、pilot readiness 与完整测试通过。
5. 根仓参考登记、对应 gitlink 和生命周期状态保持不变。
6. 团队 Codex 资产只能通过 clean release bundle 重新导入；无法满足 clean-commit 绑定时必须停在 source-ready，并明确 live pending。

## 风险与阻塞

- 这是 breaking policy change：用户点名旧外部 Skill 不再激活兼容 Skill，只保留意图并映射到 ADK 原生能力。
- 删除矩阵后不能丢失 pilot 的 workflow/artifact/device readiness 校验。
- 当前 `~/codex` 存在用户未提交改动，不能覆盖重叠 manifest 或手改 live；source-to-live 必须等待 clean release 与明确集成窗口。

## 防卡死与停止条件

- retry_budget: 2
- staleness_threshold: 连续 2 次同类验证失败且无新增根因证据
- heartbeat: 每完成 ADK source、team bundle、live apply 阶段更新一次计划和风险
- stop_condition: pass / replan / split / blocked
