# Platform 可移植性增量

PR 279 的 platform 工作流在 test_agent_platform.sh 阶段真实失败。相同源码的本地 public audit 独立复现：新增 implicit_context 尚未登记为内部扩展字段。该独立工作流不属于本地 run_all.sh 的 102 套集合。

本增量只修改 manifests/agent_platform_contracts.json 与既有平台测试。implicit_context 仅加入 internal_extension_fields；portable 标准字段、renderer、Skill、matcher 和权限不变。未知字段仍精确拒绝。

实现者和独立审查者均验证 public audit 65/65；完整平台套件通过。独立旧合同反控失败，新合同正控、额外未知字段反控与还原正控通过；Claude Code、OpenCode 两次实际静态导出不携带内部字段，范围描述保留。原路由矩阵 21/21 通过。

独立源码审查目标为 3568327a9877e2e789e079c6251cdf26af3c10c0，base 为 da34b8bed95d164eaab8982b0e13de508054ecfc；Spec/Quality PASS，R-02 已关闭。使用既有 source-change typed evidence 记录；前序源码、包装审查和失败记录保持原样。

旧 PR head da34b8 的主 CI 已观察到完整回归 102/102、contract、static-security、deterministic-eval-package 成功，但平台工作流失败仍阻止完整交付。最终提交必须重新通过全部 required CI 后才能合并、发布与 Root 接入；本增量不预填这些结果。

导出证明只覆盖静态产物，原生宿主行为、实际模型 usage/Token/成本、设备和现场效果仍未测；原 8 个字节约束及其计量器未改。
