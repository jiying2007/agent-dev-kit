# ADK Goal技能归属与工作流应用

用户要求Goal生成能力归属ADK，并实际应用工作流。

- 将平台中立的Goal合同技能和只读检查/渲染能力注册到ADK core；避免把Codex私有路径写成通用契约。
- gros_compile真实入口接入ADK，保留原目标、累计、全部验收及用户dirty；不运行AAC业务或操作设备。
- 定向验证技能发现、合同正负例、从外部cwd调用、实际项目恢复和导出。
- 不自动commit/push/release；正式Codex运行导入仍须canonical provider commit和签名release身份，源码候选不得冒充已发布运行资产。
