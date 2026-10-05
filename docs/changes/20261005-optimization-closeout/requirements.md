# 全部优化落地闭环

用户要求按前轮建议全部优化落地闭环，并明确授权 Execution Policy 任务预算上调为 3000 万、按阶段检查。

goal_statement：完成可在本机实施的源码、测试、评测入口和治理收敛；真实模型实验、签名与 owner 资格必须按实际授权与证据单独验收。

task-package v2：kind=implementation；question=优化项是否形成可复跑实现而非仅建议；permission=本地代码/文档/测试，模型费用需单独授权；exit=定向、全回归、最终快照矩阵与 fresh review；handoff=项目维护者；retention=脱敏结论和结构化证据，不保存 raw session/凭证。

## 验收项

1. dirty 工作区可运行隔离回归，不放宽 clean-source 发布门禁。
2. 评测、campaign、manifest/receipt 的关键输入统一拒绝重复键与非有限数，限额和错误脱敏有负例。
3. Provider / Execution Policy 文档入口一致，去除同一职责的旧入口。
4. 重复 operation、stale proposal、撤销权限、未知写入结果和恢复对账可确定性演练，默认不执行外部写入。
5. MCP transport、redirect、状态 handle / caller identity 负例落地；默认启用状态不变。
6. 根仓 intake/reference 及 ADK 官方文档 checker 按明确能力边界减少热点，原契约不变。
7. 预注册真实任务集与指标入口可用；有费用授权才运行模型，缺身份/结果不声明效果。
8. 最终快照验证、独立 review、Provider reviewing 归档与 Execution Policy 证据闭环。

非目标：未授权 commit/push/publish；自动晋升 owner 决策；更新签名以冒充当前 dirty source 资格；未经证据启用外部 runtime。

风险：输入严格化会拒绝旧歧义数据；模块拆分必须保留现有消费者 API；隔离测试提交只发生在临时 fixture，不提交用户仓库。
