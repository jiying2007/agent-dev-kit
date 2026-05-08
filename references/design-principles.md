# adk 设计原则

> 来源: artifact-gated-agents 5 条设计原则

## 1. Artifact First（产物优先）
所有工作流的输出必须是可归档的产物（文档/代码/配置），而非口头承诺。

## 2. Gate Before Build（构建前门禁）
编码/构建之前，必须通过前置门禁检查（需求确认/设计评审/任务分解）。

## 3. One Role One Decision（一角色一决策）
每个决策点只有一个角色负责，避免集体决策导致的职责模糊。

## 4. Read-Only Reviewers（只读评审）
评审者只读不写，评审意见通过标准化模板提交，由负责人决定是否采纳。

## 5. Traceable Delivery（可追溯交付）
每个交付物必须可追溯到其输入（需求/设计/任务），形成完整链路。
