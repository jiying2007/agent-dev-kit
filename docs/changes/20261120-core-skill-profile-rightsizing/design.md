# 方案与回滚

1. **保留默认 core 22 项及全部 Profile 身份/顺序**：实测现有 Workflow、Goal、Claude/OpenCode 导出依赖这些已承诺的能力，不再削减数量。
2. **精简正文而非删功能**：runtime-router 缩短重复流程并复用未变任务路由、先核目标 Profile 的安装清单；context-engineering 明确 Token 预算/交接职责并压缩恢复流程。
3. **可选组合治理**：只记录 KEEP/DEFER/MERGE/RETIRE 的证据要求，不扩大默认加载和执行权限。
4. **严格控制字节与效果声明**：使用既有 5600-byte router gate、Profile 全量源码 ratchet、发布回归；不可放大阈值或以静态体积替代真实 Token A/B。
5. **回滚**：整 PR revert，不触碰用户 live 目录，不改变现有发布签名及 Product M5 授权。
