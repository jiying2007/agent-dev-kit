# 设计 — 使用现有 Skill + 按需引用

保持 ADK 现有 56 core / 8 optional Skill identity 不变；仅强化已存在能力中的可执行策略，长知识放进各自 references，兼容单 Skill 导出而不隐式依赖其他仓库。

修复 `adk-interface-contract-design` 错误吞掉后续 Quality Gate 的 Markdown 围栏并纳入面向全登记资产的源测试。新增场景文件用于人工模型基线/对照，不生成虚假 E2/E3/E4 成功声明。

以实际 Profile 完整 UTF-8 源文件大小 + deferred reference 分别评估成本；只在有显式审核理由时更新源字节保护线，不以预测 Token 作为测量。保证完整回归、保护合并与不可变发布；Root 晋级另需真实 Sigstore 六件套和独立主线验证。
