# Goal 工作流收敛优化

用户授权按审查建议落地，并以 gros_compile 为试点、设计可复用 Goal 生成技能。

- 保留原生 Goal 身份、累计、全部原验收和既有 dirty；不提交、发布或操作设备。
- 修复跨 cwd CLI 和当前状态 schema 失配；恢复入口默认 <=8 KiB，历史按需读取。
- Goal 生成只产合同草案，不自动启动/替换目标、设置预算或扩大权限。
- 父验收映射到可关闭子项；批次验收、预算提案、重试与停止条件明确。
- 验收：正负合同测试、跨 cwd 遮蔽测试、试点恢复/映射校验、相关回归和受管安装验证。

外部依据：OpenAI Using Goals in Codex、ExecPlan、Testing Agent Skills Systematically with Evals；本轮已重新读取官方资料。效率提升仅能在后续同任务测量后声明。
