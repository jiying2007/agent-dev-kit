# Design

仅修改七个已有 Skill 入口，把专业领域决策与呈现文风分离，遵循 risk-tier（lite / standard / formal）。使用维护文档而非常驻二次 prompt；`adk-prose-revision` 保持显式可选，不负责领域事实审核。默认输出精简、风险升高才补全授权、证据、恢复。旧文件不自动改写，回滚可恢复这七个入口与测试/指南，不修改版本锁定消费方。

16 项 source-only 例子和路由正例不证明真实模型效果；真实 A/B 还需要同模型、预算、输入与独立人工评估（当前 not-measured）。
